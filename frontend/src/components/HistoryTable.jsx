import { logger } from "../utils/logger"
import { clearHistory } from "../api/client"
import { useState } from "react"

export default function HistoryTable({ recipes, onDetails, onClear }) {
  const [clearing, setClearing] = useState(false)

  const handleClear = async () => {
    if (!confirm("Clear all saved recipes? This cannot be undone.")) return
    setClearing(true)
    try {
      await clearHistory()
      onClear()
    } catch {
      alert("Failed to clear history")
    } finally {
      setClearing(false)
    }
  }

  // add useState import at top
  // import { useState } from "react"

  if (!recipes.length) return (
    <div style={{ textAlign: "center", padding: "60px 0", color: "#8B8378" }}>
      <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "20px", marginBottom: "8px" }}>No recipes yet</div>
      <div style={{ fontSize: "13px" }}>Extract your first recipe from the other tab</div>
    </div>
  )

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "16px" }}>
        <button
          onClick={handleClear}
          disabled={clearing}
          style={{
            padding: "8px 16px",
            background: "none",
            color: "#DC2626",
            border: "1px solid #FECACA",
            borderRadius: "8px",
            fontSize: "12px",
            fontWeight: 500,
            cursor: "pointer",
            fontFamily: "'DM Sans', sans-serif"
          }}
        >
          {clearing ? "Clearing..." : "Clear All Recipes"}
        </button>
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
        <thead>
          <tr style={{ borderBottom: "1.5px solid #EDE8DF" }}>
            {["Title", "Cuisine", "Difficulty", "Date", ""].map(h => (
              <th key={h} style={{ padding: "10px 12px", textAlign: "left", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.8px", color: "#8B8378", fontWeight: 500 }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {recipes.map(r => (
            <tr key={r.id} style={{ borderBottom: "1px solid #F5F0E8" }}>
              <td style={{ padding: "14px 12px", fontWeight: 500, color: "#1a1814" }}>{r.title}</td>
              <td style={{ padding: "14px 12px", color: "#8B8378" }}>{r.cuisine || "—"}</td>
              <td style={{ padding: "14px 12px" }}>
                {r.difficulty && (
                  <span style={{
                    padding: "4px 10px", borderRadius: "20px", fontSize: "12px", fontWeight: 500,
                    background: r.difficulty === "easy" ? "#22c55e22" : r.difficulty === "medium" ? "#f59e0b22" : "#ef444422",
                    color: r.difficulty === "easy" ? "#16a34a" : r.difficulty === "medium" ? "#d97706" : "#dc2626"
                  }}>
                    {r.difficulty}
                  </span>
                )}
              </td>
              <td style={{ padding: "14px 12px", color: "#8B8378", fontSize: "13px" }}>
                {new Date(r.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
              </td>
              <td style={{ padding: "14px 12px" }}>
                <button
                  onClick={() => onDetails(r.id)}
                  style={{ padding: "7px 16px", background: "#1a1814", color: "#F5ECD7", border: "none", borderRadius: "8px", fontSize: "12px", fontWeight: 500, cursor: "pointer", fontFamily: "'DM Sans', sans-serif" }}
                >
                  Details →
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
