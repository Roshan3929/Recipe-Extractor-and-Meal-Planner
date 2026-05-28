import RecipeCard from "./RecipeCard"
import { logger } from "../utils/logger"

export default function DetailsModal({ recipe, onClose }) {
  if (!recipe) return null

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(26,24,20,0.7)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      <div style={{ background: "#FDFAF6", borderRadius: "16px", width: "100%", maxWidth: "860px", maxHeight: "90vh", overflowY: "auto", padding: "32px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "18px", color: "#1a1814" }}>Recipe Details</div>
          <button
            onClick={() => {
              logger.buttonClick("Close Details Modal", { recipeId: recipe.id })
              onClose()
            }}
            style={{ background: "#1a1814", color: "#F5ECD7", border: "none", borderRadius: "8px", width: "32px", height: "32px", fontSize: "18px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
          >
            ×
          </button>
        </div>
        <RecipeCard recipe={recipe} />
      </div>
    </div>
  )
}