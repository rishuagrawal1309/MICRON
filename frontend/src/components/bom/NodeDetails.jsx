function NodeDetails({ node, onClose }) {

    if (!node) {
        return null;
    }

    const data = node.data;

    return (
        <div
            style={{
                position: "absolute",
                top: "20px",
                right: "20px",
                width: "280px",
                background: "white",
                border: "1px solid #ccc",
                borderRadius: "10px",
                padding: "20px",
                zIndex: 10,
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
            }}
        >

            <button
                onClick={onClose}
                style={{
                    float: "right",
                    border: "none",
                    background: "transparent",
                    fontSize: "18px",
                    cursor: "pointer"
                }}
            >
                ✕
            </button>

            <h3>Material Details</h3>

            <p>
                <strong>Material:</strong> {data.material}
            </p>

            <p>
                <strong>Stage:</strong> {data.stage}
            </p>

            <p>
                <strong>Quantity:</strong> {data.quantity}
            </p>

            <p>
                <strong>Plant:</strong> {data.plant}
            </p>

            <p>
                <strong>BOM Alternative:</strong> {data.bomAlt}
            </p>

            <p>
                <strong>Status:</strong> {data.status}
            </p>

            <p>
                <strong>Valid From:</strong> {data.validFrom}
            </p>

            <p>
                <strong>Valid To:</strong> {data.validTo}
            </p>

        </div>
    );
}

export default NodeDetails;