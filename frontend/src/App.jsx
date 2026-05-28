import { useState, useEffect } from "react"
import RecipeCard from "./components/RecipeCard"
import HistoryTable from "./components/HistoryTable"
import DetailsModal from "./components/DetailsModal"
import { extractRecipe, getHistory, getRecipeDetail } from "./api/client"
import MealPlanner from "./components/MealPlanner"
import { logger } from "./utils/logger"

export default function App() {
  const [activeTab, setActiveTab] = useState("extract")
  const [url, setUrl] = useState("")
  const [recipe, setRecipe] = useState(null)
  const [history, setHistory] = useState([])
  const [modalRecipe, setModalRecipe] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (activeTab === "history" || activeTab === "planner") fetchHistory()
  }, [activeTab])

const fetchHistory = async () => {
  try {
    const res = await getHistory()
    const recipes = res.data.recipes || res.data
    console.log("Recipes to display:", recipes)
    setHistory(recipes)
  } catch (e) {
    console.log("History error:", e)
    setError("Failed to load history")
  }
}

  const handleExtract = async () => {
    if (!url.trim()) {
      logger.warning("Extract button clicked but no URL provided")
      setError({ message: "Please enter a URL", detail: "" })
      return
    }
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      logger.warning("Extract button clicked with invalid URL format")
      setError({ message: "URL must start with http:// or https://", detail: "" })
      return
    }
    logger.buttonClick("Extract Recipe", { url })
    logger.extractStart(url)
    setLoading(true)
    setError(null)
    setRecipe(null)
    const startTime = performance.now()
    try {
      const res = await extractRecipe(url)
      const duration = Math.round(performance.now() - startTime)
      setRecipe(res.data)
      logger.extractComplete(res.data.title, duration)
    } catch (e) {
      const duration = Math.round(performance.now() - startTime)
      const detail = e.response?.data?.detail
      if (typeof detail === "object") {
        setError(detail)
        logger.extractError(detail.message || detail)
      } else {
        setError({ message: detail || "Extraction failed", detail: "" })
        logger.extractError(detail || "Extraction failed")
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDetails = async (id) => {
    logger.buttonClick("View Details", { recipeId: id })
    try {
      const res = await getRecipeDetail(id)
      setModalRecipe(res.data)
      logger.recipeDetail(id, res.data.title)
    } catch {
      setError("Failed to load recipe details")
      logger.error("Failed to load recipe details")
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#FDFAF6" }}>
      {/* Header */}
      <div style={{ background: "#1a1814", padding: "18px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "22px", color: "#F5ECD7" }}>
          recipe<span style={{ color: "#E8845A", fontStyle: "italic" }}>extract</span>
        </div>
        <div style={{ fontSize: "12px", color: "#8B7355" }}>Powered by Gemini</div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1.5px solid #EDE8DF", padding: "0 32px", background: "#FDFAF6" }}>
        {[
          { key: "extract", label: "Extract Recipe" },
          { key: "history", label: "Saved Recipes" },
          { key: "planner", label: "Meal Planner" }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => {
              logger.tabSwitch(tab.label)
              setActiveTab(tab.key)
            }}
            style={{
              padding: "14px 20px",
              fontSize: "11px",
              fontWeight: 500,
              letterSpacing: "0.3px",
              textTransform: "uppercase",
              color: activeTab === tab.key ? "#1a1814" : "#8B8378",
              borderBottom: activeTab === tab.key ? "2px solid #E8845A" : "2px solid transparent",
              background: "none",
              border: "none",
              borderBottom: activeTab === tab.key ? "2px solid #E8845A" : "2px solid transparent",
              cursor: "pointer",
              marginBottom: "-1.5px",
              fontFamily: "'DM Sans', sans-serif"
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "32px", maxWidth: "900px", margin: "0 auto" }}>
        {activeTab === "extract" && (
          <div>
            {/* URL Input */}
            <div style={{ display: "flex", gap: "12px", marginBottom: "32px" }}>
              <input
                type="text"
                value={url}
                onChange={e => {
                  logger.urlInput(e.target.value)
                  setUrl(e.target.value)
                }}
                onKeyDown={e => e.key === "Enter" && handleExtract()}
                placeholder="Paste a recipe URL — e.g. allrecipes.com/recipe/..."
                style={{
                  flex: 1, padding: "14px 18px",
                  border: "1.5px solid #EDE8DF", borderRadius: "10px",
                  fontFamily: "'DM Sans', sans-serif", fontSize: "14px",
                  background: "#fff", color: "#1a1814", outline: "none"
                }}
              />
              <button
                onClick={handleExtract}
                disabled={loading}
                style={{
                  padding: "14px 28px", background: loading ? "#c4956a" : "#E8845A",
                  color: "#fff", border: "none", borderRadius: "10px",
                  fontFamily: "'DM Sans', sans-serif", fontSize: "14px",
                  fontWeight: 500, cursor: loading ? "not-allowed" : "pointer",
                  whiteSpace: "nowrap"
                }}
              >
                {loading ? "Extracting..." : "Extract Recipe →"}
              </button>
            </div>

            {error && (
              <div style={{
                padding: "14px 18px",
                background: "#FEF2F2",
                border: "1px solid #FECACA",
                borderRadius: "10px",
                marginBottom: "20px",
                display: "flex",
                alignItems: "flex-start",
                gap: "10px"
              }}>
                <span style={{ color: "#DC2626", fontSize: "16px" }}>⚠</span>
                <div>
                  <div style={{ color: "#DC2626", fontWeight: 500, fontSize: "14px", marginBottom: "2px" }}>
                    Extraction Failed
                  </div>
                  <div style={{ color: "#991B1B", fontSize: "13px" }}>
                    {typeof error === "object" ? error.message || error.detail : error}
                  </div>
                </div>
              </div>
            )}

            {loading && (
              <div style={{ background: "#fff", border: "1.5px solid #EDE8DF", borderRadius: "14px", padding: "28px 32px" }}>
                {/* skeleton header */}
                <div style={{ height: "32px", background: "#F5F0E8", borderRadius: "6px", width: "60%", marginBottom: "16px", animation: "pulse 1.5s infinite" }} />
                <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
                  {[80, 60, 90].map((w, i) => (
                    <div key={i} style={{ height: "24px", background: "#F5F0E8", borderRadius: "20px", width: `${w}px`, animation: "pulse 1.5s infinite" }} />
                  ))}
                </div>
                {/* skeleton rows */}
                {[100, 80, 90, 70, 85].map((w, i) => (
                  <div key={i} style={{ height: "14px", background: "#F5F0E8", borderRadius: "4px", width: `${w}%`, marginBottom: "10px", animation: "pulse 1.5s infinite" }} />
                ))}
                <style>{`@keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.4 } }`}</style>
              </div>
            )}

            {recipe && <RecipeCard recipe={recipe} />}
          </div>
        )}

        {activeTab === "history" && (
          <div style={{ background: "#fff", border: "1.5px solid #EDE8DF", borderRadius: "12px", padding: "24px" }}>
            <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "22px", marginBottom: "20px" }}>Saved Recipes</div>
            <HistoryTable recipes={history} onDetails={handleDetails} onClear={fetchHistory} />
          </div>
        )}

        {activeTab === "planner" && (
          <MealPlanner recipes={history} />
        )}
      </div>

      {modalRecipe && <DetailsModal recipe={modalRecipe} onClose={() => {
        logger.buttonClick("Close Details Modal", {})
        setModalRecipe(null)
      }} />}
    </div>
  )
}