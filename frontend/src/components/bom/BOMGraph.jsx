import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

const STAGE_STYLES = {
  FPN: { background: "#e3f2fd", border: "#1976d2" },
  PKGD: { background: "#e8f5e9", border: "#388e3c" },
  TSTD: { background: "#fff3e0", border: "#f57c00" },
  ASMBLD: { background: "#f3e5f5", border: "#7b1fa2" },
  MODULE: { background: "#ede7f6", border: "#5e35b1" },
  CHIP: { background: "#fce4ec", border: "#c2185b" },
  DIE: { background: "#fff8e1", border: "#f9a825" },
  WAFER: { background: "#e0f7fa", border: "#00838f" },
  FAB_OUT: { background: "#e8eaf6", border: "#3949ab" },
  RAW: { background: "#f5f5f5", border: "#616161" },
};

function getStage(node) {
  if (node?.stage) {
    return node.stage;
  }

  if (node?.metadata?.HDR_MATL_GROUP) {
    return node.metadata.HDR_MATL_GROUP;
  }

  const material = node?.material || "";
  return material.split("-")[0] || "UNKNOWN";
}

function BOMGraph({ data }) {
  const { nodes, edges } = useMemo(() => {
    const nodes = [];
    const edges = [];

    let nodeCounter = 0;

    const X_GAP = 220;
    const Y_GAP = 140;

    function buildNode(node, parentId = null, depth = 0, x = 0) {
      if (!node) {
        return;
      }

      const id = `node-${nodeCounter++}`;
      const children = node.children || [];

      const stage = getStage(node);

      const stageStyle =
        STAGE_STYLES[stage] || {
          background: "#ffffff",
          border: "#64748b",
        };

      nodes.push({
        id,
        position: {
          x,
          y: depth * Y_GAP,
        },
        data: {
          label: (
            <div
              style={{
                textAlign: "center",
                fontSize: "13px",
              }}
            >
              <div
                style={{
                  fontWeight: "700",
                  marginBottom: "5px",
                }}
              >
                {node.material}
              </div>

              <div
                style={{
                  fontSize: "11px",
                  fontWeight: "500",
                }}
              >
                {stage}
              </div>

              {node.metadata?.COMP_QTY !== undefined && (
                <div
                  style={{
                    fontSize: "10px",
                    marginTop: "4px",
                  }}
                >
                  Qty: {node.metadata.COMP_QTY}
                </div>
              )}
            </div>
          ),
        },
        style: {
          width: 180,
          padding: 12,
          border: `2px solid ${stageStyle.border}`,
          borderRadius: 10,
          background: stageStyle.background,
        },
      });

      if (parentId) {
        edges.push({
          id: `${parentId}-${id}`,
          source: parentId,
          target: id,
        });
      }

      if (children.length > 0) {
        const startX =
          x - ((children.length - 1) * X_GAP) / 2;

        children.forEach((child, index) => {
          buildNode(
            child,
            id,
            depth + 1,
            startX + index * X_GAP
          );
        });
      }
    }

    if (data?.material) {
      buildNode(data);
    }

    console.log("BOMGraph data:", data);
    console.log("BOMGraph nodes:", nodes);
    console.log("BOMGraph edges:", edges);

    return {
      nodes,
      edges,
    };
  }, [data]);

  if (!data) {
    return (
      <div
        style={{
          width: "100%",
          height: "600px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        No BOM data available.
      </div>
    );
  }

  return (
    <div
      style={{
        width: "100%",
        height: "600px",
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        fitViewOptions={{
          padding: 0.2,
        }}
        minZoom={0.2}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}

export default BOMGraph;