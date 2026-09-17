import os
import sys
import json
import mimetypes
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Set base path to repository root
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.db.database import get_connection
from backend.app.core.graph import BOMGraph
from backend.app.core.traversal import BOMTraversal
from backend.app.core.anomalies import BOMAnomalyDetector
from backend.app.core.flatten import BOMFlattener
from backend.app.core.reconciliation import BOMReconciler
from backend.app.core.conversational_agent import ConversationalBOMAgent

FRONTEND_DIR = BASE_DIR / "frontend"

# Cache graph and instances
_graph = None
_traversal = None
_detector = None
_flattener = None
_reconciler = None
_agent = None

def get_services():
    global _graph, _traversal, _detector, _flattener, _reconciler, _agent
    if _graph is None:
        _graph = BOMGraph()
        _graph.build_graph()
        _traversal = BOMTraversal(_graph)
        _detector = BOMAnomalyDetector(_graph)
        _flattener = BOMFlattener(_graph)
        _reconciler = BOMReconciler(_graph, _flattener)
        _agent = ConversationalBOMAgent(_graph)
    return _graph, _traversal, _detector, _flattener, _reconciler, _agent

class BOMApiHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                payload = json.loads(post_data)
                message = payload.get("message", "").strip()
                if not message:
                    self._send_json({"error": "Empty message"}, 400)
                    return

                _, _, _, _, _, agent = get_services()
                reply = agent.answer_query(message)
                self._send_json({"reply": reply})
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api(path, query)
        else:
            self.handle_static(path)

    def handle_api(self, path, query):
        graph, traversal, detector, flattener, reconciler, agent = get_services()

        try:
            if path == "/api/overview":
                conn = get_connection()
                cur = conn.cursor()

                cur.execute("SELECT COUNT(*) FROM bom_single_level")
                single_count = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT HDR_MATERIAL) FROM bom_single_level")
                header_count = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT COMP_MATERIAL) FROM bom_single_level")
                comp_count = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM bom_flat")
                flat_count = cur.fetchone()[0]

                cur.execute("""
                    SELECT HDR_MATL_GROUP, COUNT(*) as cnt 
                    FROM bom_single_level 
                    WHERE HDR_MATL_GROUP IS NOT NULL 
                    GROUP BY HDR_MATL_GROUP 
                    ORDER BY cnt DESC
                """)
                stage_distribution = [{"stage": r["HDR_MATL_GROUP"], "count": r["cnt"]} for r in cur.fetchall()]

                conn.close()

                # Get anomaly stats
                anomalies = detector.detect_all_anomalies()
                anomaly_counts_by_type = {}
                anomaly_counts_by_sev = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
                for a in anomalies:
                    t = a.get("type", "UNKNOWN")
                    s = a.get("severity", "INFO")
                    anomaly_counts_by_type[t] = anomaly_counts_by_type.get(t, 0) + 1
                    anomaly_counts_by_sev[s] = anomaly_counts_by_sev.get(s, 0) + 1

                # Reconciled summary
                recon_results = reconciler.reconcile()
                recon_stats = {}
                for r in recon_results:
                    t = r.get("type", "MISC")
                    recon_stats[t] = recon_stats.get(t, 0) + 1

                self._send_json({
                    "database": {
                        "singleLevelRecords": single_count,
                        "uniqueHeaders": header_count,
                        "uniqueComponents": comp_count,
                        "flatRecords": flat_count,
                        "stageDistribution": stage_distribution
                    },
                    "anomalies": {
                        "total": len(anomalies),
                        "bySeverity": anomaly_counts_by_sev,
                        "byType": anomaly_counts_by_type
                    },
                    "reconciliation": {
                        "discrepancies": len(recon_results),
                        "byType": recon_stats
                    }
                })

            elif path == "/api/anomalies":
                anomalies = detector.detect_all_anomalies()
                type_filter = query.get("type", [None])[0]
                sev_filter = query.get("severity", [None])[0]
                q_filter = query.get("q", [None])[0]

                filtered = []
                for a in anomalies:
                    if type_filter and a.get("type") != type_filter:
                        continue
                    if sev_filter and a.get("severity") != sev_filter:
                        continue
                    if q_filter:
                        q_lower = q_filter.lower()
                        mat = str(a.get("material", "")).lower()
                        desc = str(a.get("description", "")).lower()
                        if q_lower not in mat and q_lower not in desc:
                            continue
                    filtered.append(a)

                self._send_json({"total": len(anomalies), "filtered": len(filtered), "anomalies": filtered})

            elif path == "/api/reconciliation":
                recon_results = reconciler.reconcile()
                type_filter = query.get("type", [None])[0]
                q_filter = query.get("q", [None])[0]

                filtered = []
                for r in recon_results:
                    if type_filter and r.get("type") != type_filter:
                        continue
                    if q_filter:
                        q_lower = q_filter.lower()
                        item_str = json.dumps(r, default=str).lower()
                        if q_lower not in item_str:
                            continue
                    filtered.append(r)

                self._send_json({"total": len(recon_results), "filtered": len(filtered), "results": filtered})

            elif path == "/api/materials":
                all_materials = set(graph.forward_graph.keys())
                for ch in graph.forward_graph.values():
                    all_materials.update(ch)
                prefix = query.get("q", [""])[0].lower()
                matched = [m for m in sorted(all_materials) if prefix in m.lower()] if prefix else sorted(all_materials)
                self._send_json({"materials": matched[:100], "total": len(matched)})

            elif path == "/api/tree":
                material = query.get("material", [None])[0]
                if not material:
                    fpns = [m for m in graph.forward_graph.keys() if m.startswith("FPN-")]
                    material = fpns[0] if fpns else (next(iter(graph.forward_graph)) if graph.forward_graph else "")
                
                if not material:
                    self._send_json({"error": "No materials available"}, 404)
                    return

                tree = traversal.get_bom_tree(material)

                relation_anomalies = {}
                for anomaly in detector.detect_all_anomalies():
                    anomaly_type = anomaly.get("type")
                    if anomaly_type == "STAGE_VIOLATION":
                        relation = (anomaly.get("material"), anomaly.get("child"))
                    elif anomaly_type == "EXPIRED_ACTIVE":
                        relation = (anomaly.get("material"), anomaly.get("component"))
                    else:
                        continue
                    relation_anomalies.setdefault(relation, []).append({
                        "type": anomaly_type,
                        "severity": anomaly.get("severity"),
                        "description": anomaly.get("description"),
                    })

                def annotate_tree(node):
                    for child in node.get("children", []):
                        child["edge_anomalies"] = relation_anomalies.get(
                            (node.get("material"), child.get("material")), []
                        )
                        annotate_tree(child)

                annotate_tree(tree)
                self._send_json(tree)

            elif path == "/api/lineage":
                material = query.get("material", [""])[0]
                direction = query.get("direction", ["forward"])[0]
                if not material:
                    self._send_json({"error": "Material parameter required"}, 400)
                    return

                if direction == "reverse":
                    lineage = traversal.reverse_lineage(material)
                else:
                    lineage = traversal.forward_lineage(material)

                self._send_json({"material": material, "direction": direction, "lineage": lineage})

            elif path == "/api/records/single":
                page = int(query.get("page", [1])[0])
                page_size = int(query.get("pageSize", [25])[0])
                offset = (page - 1) * page_size
                search = query.get("q", [""])[0].strip()

                conn = get_connection()
                cur = conn.cursor()

                where = ""
                params = []
                if search:
                    where = "WHERE HDR_MATERIAL LIKE ? OR COMP_MATERIAL LIKE ? OR PLANT LIKE ?"
                    params = [f"%{search}%", f"%{search}%", f"%{search}%"]

                cur.execute(f"SELECT COUNT(*) FROM bom_single_level {where}", params)
                total = cur.fetchone()[0]

                cur.execute(f"""
                    SELECT * FROM bom_single_level 
                    {where} 
                    ORDER BY id ASC 
                    LIMIT ? OFFSET ?
                """, params + [page_size, offset])
                
                rows = [dict(r) for r in cur.fetchall()]
                conn.close()
                self._send_json({"page": page, "pageSize": page_size, "total": total, "rows": rows})

            elif path == "/api/records/flat":
                page = int(query.get("page", [1])[0])
                page_size = int(query.get("pageSize", [25])[0])
                offset = (page - 1) * page_size
                search = query.get("q", [""])[0].strip()

                conn = get_connection()
                cur = conn.cursor()

                where = ""
                params = []
                if search:
                    where = "WHERE FPN LIKE ? OR PKGD LIKE ? OR MODULE LIKE ? OR CHIP LIKE ? OR RAW LIKE ?"
                    params = [f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"]

                cur.execute(f"SELECT COUNT(*) FROM bom_flat {where}", params)
                total = cur.fetchone()[0]

                cur.execute(f"""
                    SELECT * FROM bom_flat 
                    {where} 
                    ORDER BY id ASC 
                    LIMIT ? OFFSET ?
                """, params + [page_size, offset])
                
                rows = [dict(r) for r in cur.fetchall()]
                conn.close()
                self._send_json({"page": page, "pageSize": page_size, "total": total, "rows": rows})

            else:
                self._send_json({"error": "Endpoint not found"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def handle_static(self, path):
        if path == "/" or path == "":
            path = "/index.html"

        rel_path = path.lstrip("/")
        file_path = FRONTEND_DIR / rel_path

        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(FRONTEND_DIR.resolve())):
                self.send_error(403, "Access Forbidden")
                return
        except Exception:
            self.send_error(400, "Bad Request")
            return

        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File Not Found")
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

def run(port=8000):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, BOMApiHandler)
    print(f"[Micron BOM Server] Dashboard running at http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Micron BOM Web Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run on (default 8000)")
    args = parser.parse_args()
    run(args.port)
