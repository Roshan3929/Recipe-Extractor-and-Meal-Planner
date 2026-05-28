import { useEffect } from "react"
import { logger } from "../utils/logger"

export default function RecipeCard({ recipe }) {
  useEffect(() => {
    if (recipe) {
      logger.info(`Recipe card displayed: ${recipe.title}`)
    }
  }, [recipe])

  if (!recipe) return null

  return (
    <div>
      {/* Hero Header */}
      <div style={{ background: "#1a1814", borderRadius: "14px", padding: "28px 32px", marginBottom: "16px" }}>
        <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "32px", color: "#F5ECD7", marginBottom: "12px", lineHeight: 1.1 }}>
          {recipe.title}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "16px" }}>
          {recipe.cuisine && <Badge label={recipe.cuisine} type="cuisine" />}
          {recipe.difficulty && <Badge label={recipe.difficulty} type={recipe.difficulty} />}
          {recipe.servings && <Badge label={`${recipe.servings} servings`} type="neutral" />}
        </div>
        <div style={{ display: "flex", gap: "24px" }}>
          {[["Prep", recipe.prep_time], ["Cook", recipe.cook_time], ["Total", recipe.total_time]].map(([label, val]) =>
            val && (
              <div key={label} style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: "10px", color: "#8B7355", textTransform: "uppercase", letterSpacing: "0.8px" }}>{label}</span>
                <span style={{ fontSize: "15px", color: "#F5ECD7", fontWeight: 500, marginTop: "2px" }}>{val}</span>
              </div>
            )
          )}
        </div>
      </div>

      {/* Ingredients + Nutrition */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
        <Card title="Ingredients">
          {recipe.ingredients?.map((ing, i) => (
            <div key={i} style={{ display: "flex", alignItems: "baseline", gap: "8px", padding: "7px 0", borderBottom: i < recipe.ingredients.length - 1 ? "1px solid #F5F0E8" : "none", fontSize: "14px" }}>
              <span style={{ color: "#E8845A", fontWeight: 500, minWidth: "32px", fontSize: "13px" }}>{ing.quantity}</span>
              <span style={{ color: "#8B8378", fontSize: "12px", minWidth: "40px" }}>{ing.unit}</span>
              <span style={{ color: "#1a1814" }}>{ing.item}</span>
            </div>
          ))}
        </Card>

        <Card title="Nutrition per serving">
          {recipe.nutrition_estimate && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "10px" }}>
              {Object.entries(recipe.nutrition_estimate).map(([key, val]) => (
                <div key={key} style={{ background: "#FDFAF6", border: "1.5px solid #EDE8DF", borderRadius: "10px", padding: "14px", textAlign: "center" }}>
                  <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "20px", color: "#E8845A" }}>{val}</div>
                  <div style={{ fontSize: "11px", color: "#8B8378", textTransform: "uppercase", letterSpacing: "0.5px", marginTop: "4px" }}>{key}</div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Instructions */}
      <Card title="Instructions" style={{ marginBottom: "16px" }}>
        {recipe.instructions?.map((ins, i) => (
          <div key={i} style={{ display: "flex", gap: "14px", padding: "10px 0", fontSize: "14px", lineHeight: 1.6, color: "#3D3830" }}>
            <div style={{ minWidth: "26px", height: "26px", background: "#E8845A", color: "#fff", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 500, flexShrink: 0, marginTop: "1px" }}>
              {ins.step_number}
            </div>
            <div>{ins.instruction_text}</div>
          </div>
        ))}
      </Card>

      {/* Substitutions + Shopping */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
        <Card title="Substitutions">
          {recipe.substitutions?.map((sub, i) => (
            <div key={i} style={{ padding: "10px 14px", background: "#FDFAF6", borderRadius: "8px", fontSize: "13px", color: "#3D3830", marginBottom: "8px", borderLeft: "3px solid #E8845A" }}>
              {sub}
            </div>
          ))}
        </Card>

        <Card title="Shopping List">
          {Object.entries(recipe.shopping_list || {}).map(([cat, items]) => (
            <div key={cat} style={{ marginBottom: "14px" }}>
              <div style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.8px", color: "#8B8378", marginBottom: "8px", fontWeight: 500 }}>{cat}</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {items.map((item, i) => (
                  <span key={i} style={{ background: "#F5ECD7", color: "#6B4F2A", padding: "5px 12px", borderRadius: "20px", fontSize: "12px" }}>{item}</span>
                ))}
              </div>
            </div>
          ))}
        </Card>
      </div>

      {/* Related */}
      <Card title="You might also like">
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {recipe.related_recipes?.map((r, i) => (
            <span key={i} style={{ background: "#1a1814", color: "#F5ECD7", padding: "8px 16px", borderRadius: "20px", fontSize: "13px" }}>{r}</span>
          ))}
        </div>
      </Card>
    </div>
  )
}

function Card({ title, children, style }) {
  """Display a styled card container."""
  return (
    <div style={{ background: "#fff", border: "1.5px solid #EDE8DF", borderRadius: "12px", padding: "22px", marginBottom: "0", ...style }}>
      <div style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.8px", color: "#8B8378", fontWeight: 500, marginBottom: "14px" }}>{title}</div>
      {children}
    </div>
  )
}

function Badge({ label, type }) {
  """Display a styled badge label."""
  const styles = {
    cuisine: { background: "#E8845A22", color: "#E8845A", border: "1px solid #E8845A44" },
    easy: { background: "#22c55e22", color: "#16a34a", border: "1px solid #22c55e44" },
    medium: { background: "#f59e0b22", color: "#d97706", border: "1px solid #f59e0b44" },
    hard: { background: "#ef444422", color: "#dc2626", border: "1px solid #ef444444" },
    neutral: { background: "#F5ECD722", color: "#F5ECD7", border: "1px solid #F5ECD733" }
  }
  return (
    <span style={{ padding: "5px 12px", borderRadius: "20px", fontSize: "12px", fontWeight: 500, ...styles[type] || styles.neutral }}>
      {label}
    </span>
  )
}