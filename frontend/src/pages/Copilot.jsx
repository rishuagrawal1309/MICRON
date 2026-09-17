import { useState } from "react";
import axios from "axios";
import BOMGraph from "../components/bom/BOMGraph";

function Copilot() {
  const [messages, setMessages] = useState([
    {
      sender: "ai",
      text: "Hello! I am your BOM Intelligence Copilot. Ask me anything about material shortages, paths, or anomalies.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();

    setInput("");

    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: userMessage,
      },
    ]);

    setLoading(true);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/copilot",
        {
          prompt: userMessage,
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: response.data.answer || "Analysis completed.",
          type: response.data.type,
          data: response.data.data,
        },
      ]);
    } catch (err) {
      console.error("Copilot error:", err);

      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: "Sorry, I encountered an error connecting to the intelligence backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page copilot-page">

      <div className="page-title">
        <h2>AI Copilot</h2>

        <p>
          Ask questions about your manufacturing BOM.
        </p>
      </div>

      <div className="chat-container">

        <div className="chat-messages">

          {messages.map((msg, index) => (

            <div
              key={index}
              className={`chat-bubble ${msg.sender}`}
            >

              <div
                style={{
                  whiteSpace: "pre-wrap",
                }}
              >
                {msg.text}
              </div>

              {msg.sender === "ai" && msg.type === "bom_structure" && (
                <BOMStructure data={msg.data} />
              )}

              {msg.sender === "ai" && msg.type === "anomalies" && (
                <AnomalyResults data={msg.data} />
              )}

              {msg.sender === "ai" && msg.type === "impact" && (
                <ImpactResults data={msg.data} />
              )}

            </div>

          ))}

          {loading && (
            <div className="chat-bubble ai">
              Thinking...
            </div>
          )}

        </div>


        <div className="chat-input-row">

          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();
              }
            }}
            placeholder="Ask about components, shortages, or structures..."
          />

          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            {loading ? "Sending..." : "Send"}
          </button>

        </div>

      </div>

    </div>
  );
}


/* =====================================================
   BOM STRUCTURE
   ===================================================== */

function BOMStructure({ data }) {
  if (!data) {
    return null;
  }

  const renderNode = (node, level = 0) => {
  if (!node) {
    return null;
  }

  const metadata = node.metadata || {};

  return (
    <div key={`${node.material}-${level}`}>

      <div
        style={{
          marginLeft: `${level * 24}px`,
          padding: "10px 12px",
          marginTop: "8px",
          borderLeft:
            level > 0
              ? "2px solid #cbd5e1"
              : "none",
          background: "#f8fafc",
          borderRadius: "6px",
        }}
      >

        <div
          style={{
            fontWeight: level === 0 ? "700" : "600",
            fontSize: "15px",
          }}
        >
          {level > 0 && "└── "}
          {node.material}
        </div>

        {Object.keys(metadata).length > 0 && (
          <div
            style={{
              marginTop: "6px",
              marginLeft: level > 0 ? "18px" : "0",
              fontSize: "12px",
              color: "#64748b",
              lineHeight: "1.7",
            }}
          >
            {metadata.COMP_QTY !== undefined && (
              <div>
                Quantity: {metadata.COMP_QTY}
              </div>
            )}

            {metadata.PLANT && (
              <div>
                Plant: {metadata.PLANT}
              </div>
            )}

            {metadata.BOM_ALT && (
              <div>
                BOM Alternative: {metadata.BOM_ALT}
              </div>
            )}

            {metadata.BOM_STATUS && (
              <div>
                BOM Status: {metadata.BOM_STATUS}
              </div>
            )}

            {metadata.VALID_FROM && (
              <div>
                Valid From: {metadata.VALID_FROM}
              </div>
            )}

            {metadata.VALID_TO && (
              <div>
                Valid To: {metadata.VALID_TO}
              </div>
            )}
          </div>
        )}

      </div>

      {node.children &&
        node.children.map((child) =>
          renderNode(child, level + 1)
        )}

    </div>
  );
};

  return (
    <div
      className="copilot-result"
      style={{
        marginTop: "12px",
      }}
    >
      <h4>BOM Structure</h4>

      <div
        style={{
          padding: "12px",
          borderRadius: "8px",
          background: "#ffffff",
        }}
      >
        {renderNode(data)}
      </div>
    </div>
  );
}


/* =====================================================
   ANOMALY RESULTS
   ===================================================== */

function AnomalyResults({ data }) {

  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="copilot-result">
        <p>No anomaly records found.</p>
      </div>
    );
  }

  return (
    <div className="copilot-result">

      <h4>Detected Anomalies</h4>

      {data.map((item, index) => (

        <div
          key={index}
          style={{
            marginBottom: "10px",
            padding: "10px",
            borderRadius: "8px",
          }}
        >

          <strong>
            {item.type || "Anomaly"}
          </strong>

          <pre
            style={{
              whiteSpace: "pre-wrap",
              marginTop: "6px",
            }}
          >
            {JSON.stringify(item, null, 2)}
          </pre>

        </div>

      ))}

    </div>
  );
}


/* =====================================================
   IMPACT RESULTS
   ===================================================== */

function ImpactResults({ data }) {

  if (!Array.isArray(data) || data.length === 0) {
    return (
      <div className="copilot-result">
        <p>No affected materials found.</p>
      </div>
    );
  }

  return (
    <div className="copilot-result">

      <h4>Shortage / Impact Analysis</h4>

      {data.map((item, index) => (

        <div
          key={index}
          style={{
            marginBottom: "12px",
            padding: "10px",
            borderRadius: "8px",
          }}
        >

          <strong>
            {item.fpn || item.material || "Affected Material"}
          </strong>

          {item.quantity_impact !== undefined && (
            <div>
              Quantity Impact: {item.quantity_impact}
            </div>
          )}

          {item.path && (
            <div>
              Path: {item.path.join(" → ")}
            </div>
          )}

        </div>

      ))}

    </div>
  );
}


export default Copilot;