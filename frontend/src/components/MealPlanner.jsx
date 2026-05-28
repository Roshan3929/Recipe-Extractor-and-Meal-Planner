import { useState } from "react"
import { generateMealPlan } from "../api/client"
import { logger } from "../utils/logger"

export default function MealPlanner({ recipes }) {
  const [selected, setSelected] = useState([])
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const toggle = (id) => {
    const newSelected = selected.includes(id)
      ? selected.filter(i => i !== id)
      : selected.length < 5 ? [...selected, id] : selected
    
    const recipe = recipes.find(r => r.id === id)
    logger.recipeSelect(id, recipe?.title || "Unknown", newSelected.includes(id))
    
    setSelected(newSelected)
  }

  const handleGenerate = async () => {
    if (selected.length < 3) {
      logger.warning("Generate button clicked but insufficient recipes selected")
      return
    }
    logger.buttonClick("Generate Meal Plan", { recipeCount: selected.length })
    logger.mealPlanStart(selected.length)
    setLoading(true)
    setError(null)
    setPlan(null)
    const startTime = performance.now()
    try {
      const res = await generateMealPlan(selected)
      const duration = Math.round(performance.now() - startTime)
      const itemCount = Object.values(res.data.combined_shopping_list || {}).flat().length
      setPlan(res.data.combined_shopping_list)
      logger.mealPlanComplete(itemCount)
      logger.info(`Meal plan generated in ${duration}ms`)
    } catch (e) {
      const duration = Math.round(performance.now() - startTime)
      const errorMsg = e.response?.data?.detail || "Failed to generate meal plan"
      setError(errorMsg)
      logger.mealPlanError(errorMsg)
      logger.info(`Meal plan failed after ${duration}ms`)
    } finally {
      setLoading(false)
    }
  }

  if (!recipes.length) return (
    <div style={{ background: "#fff", border: "1.5px solid #EDE8DF", borderRadius: "12px", padding: "24px" }}>
      <div style={{ textAlign: "center", padding: "60px 0", color: "#8B8378" }}>
        <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "20px", marginBottom: "8px" }}>No saved recipes</div>
        <div style={{ fontSize: "13px" }}>Extract some recipes first then come back to plan your meals</div>
      </div>
    </div>
  )

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
      {/* Recipe selector */}
      <div style={{ background: "#fff", border: "1.5px solid #EDE8DF", borderRadius: "12px", padding: "24px" }}>
        <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "20px", marginBottom: "6px" }}>
          Select Recipes
        </div>
        <div style={{ fontSize: "12px", color: "#8B8378", marginBottom: "20px" }}>
          Choose 2–5 recipes to combine
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "20px" }}>
          {recipes.map(r => (
            <div
              key={r.id}
              onClick={() => toggle(r.id)}
              style={{
                padding: "12px 16px",
                border: `1.5px solid ${selected.includes(r.id) ? "#E8845A" : "#EDE8DF"}`,
                borderRadius: "10px",
                cursor: "pointer",
                background: selected.includes(r.id) ? "#FFF5F0" : "#fff",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                transition: "all 0.15s"
              }}
            >
              <div style={{
                width: "20px", height: "20px",
                border: `2px solid ${selected.includes(r.id) ? "#E8845A" : "#D1CBC3"}`,
                borderRadius: "4px",
                background: selected.includes(r.id) ? "#E8845A" : "#fff",
                display: "flex", alignItems: "center", justifyContent: "center",
                flexShrink: 0
              }}>
                {selected.includes(r.id) && (
                  <span style={{ color: "#fff", fontSize: "12px", fontWeight: 700 }}>✓</span>
                )}
              </div>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 500, color: "#1a1814" }}>{r.title}</div>
                <div style={{ fontSize: "12px", color: "#8B8378" }}>{r.cuisine || "—"} · {r.difficulty || "—"}</div>
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={handleGenerate}
          disabled={selected.length < 3 || loading}
          style={{
            width: "100%", padding: "14px",
            background: selected.length < 3 ? "#E8E4DF" : "#E8845A",
            color: selected.length < 3 ? "#8B8378" : "#fff",
            border: "none", borderRadius: "10px",
            fontFamily: "'DM Sans', sans-serif",
            fontSize: "14px", fontWeight: 500,
            cursor: selected.length < 3 ? "not-allowed" : "pointer"
          }}
        >
          {loading
            ? "Planning..."
            : selected.length < 3
            ? `Select ${3 - selected.length} more recipe${3 - selected.length === 1 ? "" : "s"}`
            : `Generate Shopping List (${selected.length} recipes)`
          }
        </button>

        {error && (
          <div style={{ marginTop: "12px", padding: "10px 14px", background: "#FEF2F2", borderRadius: "8px", color: "#DC2626", fontSize: "13px" }}>
            {error}
          </div>
        )}
      </div>

      {/* Shopping list result */}
      <div style={{ background: "#fff", border: "1.5px solid #EDE8DF", borderRadius: "12px", padding: "24px" }}>
        <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "20px", marginBottom: "6px" }}>
          Combined Shopping List
        </div>
        <div style={{ fontSize: "12px", color: "#8B8378", marginBottom: "20px" }}>
          Quantities merged across all selected recipes
        </div>

        {!plan && !loading && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "#C4BBB3" }}>
            <div style={{ fontSize: "32px", marginBottom: "8px" }}>🛒</div>
            <div style={{ fontSize: "13px" }}>Your combined list will appear here</div>
          </div>
        )}

        {loading && (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {[60, 80, 50, 70, 90].map((w, i) => (
              <div key={i} style={{
                height: "14px", background: "#F5F0E8",
                borderRadius: "4px", width: `${w}%`,
                animation: "pulse 1.5s infinite"
              }} />
            ))}
            <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
          </div>
        )}

        {plan && (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {Object.entries(plan).map(([category, items]) => (
              <div key={category}>
                <div style={{
                  fontSize: "11px", textTransform: "uppercase",
                  letterSpacing: "0.8px", color: "#8B8378",
                  fontWeight: 500, marginBottom: "10px"
                }}>
                  {category}
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {items.map((ing, i) => (
                    <div key={i} style={{
                      display: "flex", justifyContent: "space-between",
                      alignItems: "center", padding: "8px 12px",
                      background: "#FDFAF6", borderRadius: "8px",
                      fontSize: "13px"
                    }}>
                      <span style={{ color: "#1a1814", fontWeight: 500 }}>{ing.item}</span>
                      <span style={{ color: "#E8845A", fontWeight: 500 }}>
                        {ing.quantity} {ing.unit}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}