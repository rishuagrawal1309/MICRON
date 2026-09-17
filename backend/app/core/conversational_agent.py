import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.app.db.database import get_connection
from backend.app.core.graph import BOMGraph
from backend.app.core.traversal import BOMTraversal
from backend.app.core.anomalies import BOMAnomalyDetector

class ConversationalBOMAgent:
    """
    Intelligent Conversational Agent for Micron BOM supply-chain queries.
    Utilizes SQL + Graph Tools for zero-hallucination answers and retains multi-turn memory.
    """

    def __init__(self, graph: Optional[BOMGraph] = None):
        if graph is None:
            self.graph = BOMGraph()
            self.graph.build_graph()
        else:
            self.graph = graph

        self.traversal = BOMTraversal(self.graph)
        self.anomaly_detector = BOMAnomalyDetector(self.graph)
        self.conversation_history = []
        self.api_key = self._load_api_key()

    @staticmethod
    def _load_api_key() -> str:
        """Load the Gemini key from the process environment or the project .env file."""
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key:
            return api_key

        env_path = Path(__file__).resolve().parents[3] / ".env"
        if not env_path.exists():
            return ""

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == "GEMINI_API_KEY":
                return value.strip().strip('"').strip("'")
        return ""

    # =========================================================================
    # DETERMINISTIC SQL & GRAPH QUERY TOOLS
    # =========================================================================

    def tool_lookup_material(self, material: str) -> Dict[str, Any]:
        """Looks up a material's stage, direct components, parents, and plants in SQLite."""
        material = material.strip()
        conn = get_connection()
        cur = conn.cursor()

        # Parents (where this material is used as a component)
        cur.execute("""
            SELECT HDR_MATERIAL, HDR_MATL_GROUP, COMP_QTY, PLANT, BOM_ALT, BOM_STATUS, VALID_FROM, VALID_TO
            FROM bom_single_level
            WHERE COMP_MATERIAL = ?
        """, (material,))
        parents = [dict(r) for r in cur.fetchall()]

        # Children (components consumed by this material)
        cur.execute("""
            SELECT COMP_MATERIAL, COMP_MATL_GROUP, COMP_QTY, PLANT, BOM_ALT, BOM_STATUS, VALID_FROM, VALID_TO
            FROM bom_single_level
            WHERE HDR_MATERIAL = ?
        """, (material,))
        children = [dict(r) for r in cur.fetchall()]

        # Stage classification
        stage = None
        if children and children[0].get("HDR_MATL_GROUP"):
            stage = children[0]["HDR_MATL_GROUP"]
        elif parents and parents[0].get("COMP_MATL_GROUP"):
            stage = parents[0]["COMP_MATL_GROUP"]

        conn.close()

        return {
            "material": material,
            "stage": stage,
            "direct_children_count": len(children),
            "direct_children": children[:15],
            "parent_uses_count": len(parents),
            "parent_uses": parents[:15]
        }

    def tool_trace_lineage(self, material: str, direction: str = "forward") -> Dict[str, Any]:
        """Traces complete forward (top-down to RAW) or reverse (bottom-up to FPN) lineage."""
        material = material.strip()
        if direction.lower() == "reverse":
            lineage = self.traversal.reverse_lineage(material)
            fpns = [m for m in lineage if m.startswith("FPN-")]
            return {
                "material": material,
                "direction": "reverse (where-used upward)",
                "total_upstream_nodes": len(lineage),
                "affected_fpns": fpns,
                "full_path": lineage
            }
        else:
            lineage = self.traversal.forward_lineage(material)
            raws = [m for m in lineage if m.startswith("RAW-")]
            return {
                "material": material,
                "direction": "forward (explosion downward)",
                "total_downstream_nodes": len(lineage),
                "raw_materials": raws,
                "full_path": lineage
            }

    def tool_simulate_shortage(self, component: str) -> Dict[str, Any]:
        """
        Calculates the cascading impact if a component becomes unavailable.
        Finds all directly and transitively affected parent assemblies and FPNs with quantities.
        """
        component = component.strip()
        conn = get_connection()
        cur = conn.cursor()

        # Check if material exists
        cur.execute("SELECT COUNT(*) FROM bom_single_level WHERE COMP_MATERIAL = ? OR HDR_MATERIAL = ?", (component, component))
        if cur.fetchone()[0] == 0:
            conn.close()
            return {"error": f"Material {component} not found in BOM database."}

        # Reverse traverse to find all reachable FPNs
        upstream_nodes = self.traversal.reverse_lineage(component)
        affected_fpns = [m for m in upstream_nodes if m.startswith("FPN-")]

        # Direct parents
        cur.execute("""
            SELECT DISTINCT HDR_MATERIAL, HDR_MATL_GROUP, COMP_QTY, PLANT
            FROM bom_single_level
            WHERE COMP_MATERIAL = ?
        """, (component,))
        direct_parents = [dict(r) for r in cur.fetchall()]

        # Alternative BOM paths in other plants or alternative recipes
        cur.execute("""
            SELECT DISTINCT PLANT, BOM_ALT, HDR_MATERIAL
            FROM bom_single_level
            WHERE COMP_MATERIAL = ?
        """, (component,))
        plants_used = [dict(r) for r in cur.fetchall()]

        conn.close()

        return {
            "component": component,
            "status": "SHORTAGE_SIMULATED",
            "direct_affected_parents": direct_parents,
            "total_affected_fpns_count": len(affected_fpns),
            "affected_fpns": affected_fpns,
            "plants_involved": list({p["PLANT"] for p in plants_used}),
            "mitigation_notes": f"Consider re-routing production or sourcing alternative recipes across plants {list({p['PLANT'] for p in plants_used})}."
        }

    def tool_check_anomalies(self, anomaly_type: Optional[str] = None) -> Dict[str, Any]:
        """Fetches anomalies detected across the BOM graph."""
        anomalies = self.anomaly_detector.detect_all_anomalies()
        if anomaly_type:
            atype = anomaly_type.strip().upper()
            filtered = [a for a in anomalies if a.get("type") == atype]
        else:
            filtered = anomalies

        return {
            "total_anomalies": len(filtered),
            "sample_anomalies": filtered[:10]
        }

    def tool_compare_plants(self, fpn: str, plant1: str, plant2: str) -> Dict[str, Any]:
        """Compares BOM recipes for the same product across two manufacturing plants."""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT COMP_MATERIAL, COMP_QTY, BOM_ALT 
            FROM bom_single_level 
            WHERE HDR_MATERIAL = ? AND PLANT = ?
        """, (fpn, plant1))
        p1_rows = {r["COMP_MATERIAL"]: r["COMP_QTY"] for r in cur.fetchall()}

        cur.execute("""
            SELECT COMP_MATERIAL, COMP_QTY, BOM_ALT 
            FROM bom_single_level 
            WHERE HDR_MATERIAL = ? AND PLANT = ?
        """, (fpn, plant2))
        p2_rows = {r["COMP_MATERIAL"]: r["COMP_QTY"] for r in cur.fetchall()}

        conn.close()

        only_p1 = [k for k in p1_rows if k not in p2_rows]
        only_p2 = [k for k in p2_rows if k not in p1_rows]
        shared = [k for k in p1_rows if k in p2_rows]

        return {
            "material": fpn,
            "plant1": plant1,
            "plant2": plant2,
            "plant1_components": p1_rows,
            "plant2_components": p2_rows,
            "unique_to_plant1": only_p1,
            "unique_to_plant2": only_p2,
            "shared_components": shared
        }

    def tool_execute_sql(self, query: str) -> Dict[str, Any]:
        """Executes a safe read-only SQL query on bom.db for ad-hoc statistical questions."""
        q_upper = query.strip().upper()
        if not q_upper.startswith("SELECT"):
            return {"error": "Only SELECT queries are allowed."}

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)
            rows = [dict(r) for r in cur.fetchall()[:25]]
            return {"rows": rows, "count": len(rows)}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    # =========================================================================
    # CORE CONVERSATIONAL ENGINE
    # =========================================================================

    def answer_query(self, user_message: str) -> str:
        """Processes user message conversationally, grounding with tools."""
        user_message_clean = user_message.strip()

        # Update conversational memory
        self.conversation_history.append({"role": "user", "content": user_message_clean})

        # Keep last 10 messages for context
        history_context = self.conversation_history[-10:]

        # Check if Gemini API is available
        if self.api_key:
            try:
                return self._answer_with_gemini(user_message_clean, history_context)
            except Exception as e:
                # If Gemini API encounters an error (e.g. invalid key or network), fall back gracefully
                error_message = str(e)
                print(f"[ConversationalAgent] Gemini API fallback: {error_message}", flush=True)
                if "reported as leaked" in error_message.lower():
                    reply = (
                        "⚠️ **Gemini rejected the configured API key because Google has flagged it "
                        "as leaked.** Revoke that key, create a new Gemini API key, replace "
                        "`GEMINI_API_KEY` in `.env`, and restart the server."
                    )
                    self.conversation_history.append({"role": "assistant", "content": reply})
                    return reply
                return self._answer_with_rules(user_message_clean)
        else:
            return self._answer_with_rules(user_message_clean)

    def _answer_with_gemini(self, message: str, history: List[Dict[str, str]]) -> str:
        """Invokes Google Gemini with structured tool knowledge and conversational context."""
        # Provide domain data and tool execution results
        retrieved_data = self._gather_relevant_data(message)

        system_instruction = f"""
You are the Micron BOM Intelligence Assistant.
You specialize in semiconductor manufacturing Bill of Materials (BOM) analysis for Micron across the 10 lifecycle stages:
RAW -> FAB_OUT -> WAFER -> DIE -> CHIP -> MODULE -> ASMBLD -> TSTD -> PKGD -> FPN.

Data context retrieved from the SQLite database and graph engine:
{json.dumps(retrieved_data, indent=2, default=str)}

Guidelines:
1. Answer the user's question conversationally, clearly, and authoritatively using the retrieved data above.
2. Do NOT invent or hallucinate materials that do not exist.
3. Be helpful, concise, and format data using markdown lists, bold part numbers, and bullet points.
4. If asked about shortages, explain the cascading impact and affected Finished Product Numbers (FPNs).
5. If asked about anomalies, highlight the severity (CRITICAL/WARNING) and root-cause components.
"""

        prompt = f"{system_instruction}\n\nUser Question: {message}"
        request_body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode("utf-8")
        request = Request(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-3.6-flash:generateContent",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=45) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini API returned HTTP {exc.code}: {error_body}") from exc

        parts = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        reply = "".join(part.get("text", "") for part in parts).strip()
        if not reply:
            raise RuntimeError("Gemini API returned no text response.")
        
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def _gather_relevant_data(self, message: str) -> Dict[str, Any]:
        """Automatically runs appropriate tool functions based on query keywords and materials."""
        import re
        tokens = re.findall(r'[A-Za-z0-9_\-]+', message)
        data = {}

        # Look for material patterns
        materials = [t for t in tokens if any(t.startswith(prefix) for prefix in [
            "FPN-", "PKGD-", "TSTD-", "ASM-", "MOD-", "CHIP-", "DIE-", "WAF-", "FAB-", "RAW-", "PLT"
        ])]

        msg_lower = message.lower()

        # 1. Material lookup & lineage
        if materials:
            primary_mat = materials[0]
            data["material_lookup"] = self.tool_lookup_material(primary_mat)

            if "shortage" in msg_lower or "unavailable" in msg_lower or "affect" in msg_lower:
                data["shortage_simulation"] = self.tool_simulate_shortage(primary_mat)
            elif "lineage" in msg_lower or "raw" in msg_lower or "trace" in msg_lower:
                data["forward_lineage"] = self.tool_trace_lineage(primary_mat, "forward")
                data["reverse_lineage"] = self.tool_trace_lineage(primary_mat, "reverse")

        # 2. Plant comparison
        if "plant" in msg_lower and ("differ" in msg_lower or "compare" in msg_lower):
            plants = [t for t in tokens if t.startswith("PLT") or "PLT" in t.upper()]
            mat = materials[0] if materials else "FPN-0001"
            p1 = plants[0] if len(plants) > 0 else "PLT01"
            p2 = plants[1] if len(plants) > 1 else "PLT02"
            data["plant_comparison"] = self.tool_compare_plants(mat, p1, p2)

        # 3. Anomalies
        if "cycle" in msg_lower:
            data["anomalies_cycles"] = self.tool_check_anomalies("CYCLE")
        elif "orphan" in msg_lower:
            data["anomalies_orphans"] = self.tool_check_anomalies("ORPHAN")
        elif "anomaly" in msg_lower or "anomalies" in msg_lower or "violation" in msg_lower:
            data["anomalies_summary"] = self.tool_check_anomalies()

        # Default overview if nothing matched
        if not data:
            data["recent_fpns"] = [m for m in self.graph.forward_graph if m.startswith("FPN-")][:5]
            data["total_single_level_edges"] = sum(len(v) for v in self.graph.forward_graph.values())

        return data

    def _answer_with_rules(self, message: str) -> str:
        """Deterministic offline rule-based responder when no Gemini API key is configured."""
        import re
        msg_lower = message.lower()
        tokens = re.findall(r'[A-Za-z0-9_\-]+', message)
        materials = [t for t in tokens if any(t.startswith(prefix) for prefix in [
            "FPN-", "PKGD-", "TSTD-", "ASM-", "MOD-", "CHIP-", "DIE-", "WAF-", "FAB-", "RAW-"
        ])]

        # 1. Shortage / Impact Simulation
        if "shortage" in msg_lower or "impact" in msg_lower or "unavailable" in msg_lower:
            if materials:
                mat = materials[0]
                res = self.tool_simulate_shortage(mat)
                if "error" in res:
                    reply = f"❌ **Error**: {res['error']}"
                else:
                    fpn_list = ", ".join(f"**{f}**" for f in res["affected_fpns"][:10])
                    reply = f"⚠️ **Shortage Simulation for {mat}**:\n\n"
                    reply += f"- **Direct Parents Affected**: {len(res['direct_affected_parents'])}\n"
                    reply += f"- **Total Finished Products (FPNs) Impacted**: {res['total_affected_fpns_count']}\n"
                    reply += f"- **Affected FPNs**: {fpn_list}{'...' if len(res['affected_fpns']) > 10 else ''}\n"
                    reply += f"- **Involved Manufacturing Plants**: {', '.join(res['plants_involved'])}\n"
                    reply += f"\n💡 *Recommendation*: {res['mitigation_notes']}"
                self.conversation_history.append({"role": "assistant", "content": reply})
                return reply

        # 2. Cycles / Anomalies
        if "cycle" in msg_lower:
            res = self.tool_check_anomalies("CYCLE")
            reply = f"🔄 **BOM Cycle Audit**:\n- Detected **{res['total_anomalies']}** circular dependencies in the graph.\n"
            for c in res['sample_anomalies'][:3]:
                path = " ➔ ".join(c.get("path", []))
                reply += f"- Material: **{c.get('material')}** | Path: `{path}`\n"
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply

        if "anomaly" in msg_lower or "anomalies" in msg_lower:
            res = self.tool_check_anomalies()
            reply = f"⚠️ **Total Graph Anomalies**: **{res['total_anomalies']}** detected across the BOM.\n"
            reply += "Categories include: `CYCLE`, `ORPHAN`, `STAGE_VIOLATION`, `INCOMPLETE`, and `EXPIRED_ACTIVE`."
            self.conversation_history.append({"role": "assistant", "content": reply})
            return reply

        # 3. Lineage / Components
        if materials:
            mat = materials[0]
            if "raw" in msg_lower or "lineage" in msg_lower or "trace" in msg_lower:
                res = self.tool_trace_lineage(mat, "forward")
                raws = ", ".join(f"`{r}`" for r in res["raw_materials"][:8])
                reply = f"🔬 **Forward Lineage for {mat}**:\n"
                reply += f"- **Total Downstream Nodes**: {res['total_downstream_nodes']}\n"
                reply += f"- **Terminating Raw Materials**: {raws or 'None (Incomplete branch)'}\n"
                self.conversation_history.append({"role": "assistant", "content": reply})
                return reply
            else:
                res = self.tool_lookup_material(mat)
                reply = f"📦 **Material Details: {mat}**\n"
                reply += f"- **Stage**: `{res['stage'] or 'Standard'}`\n"
                reply += f"- **Direct Components**: {res['direct_children_count']}\n"
                reply += f"- **Where-Used (Parent Assemblies)**: {res['parent_uses_count']}\n"
                self.conversation_history.append({"role": "assistant", "content": reply})
                return reply

        # Default help
        reply = ("👋 I am your **Micron BOM Intelligence Agent**.\n\n"
                 "Ask me questions such as:\n"
                 "- *'What components make up FPN-0001?'*\n"
                 "- *'If DIE-0135 goes on shortage, which finished products are affected?'*\n"
                 "- *'Are there any cycles in the BOM graph?'*\n"
                 "- *'What raw materials go into FPN-0050?'*\n\n"
                 "*(Note: You can add your `GEMINI_API_KEY` in `.env` for open-ended generative responses!)*")
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply
