// All fetch calls in one place
import axios from "axios"
import { logger } from "../utils/logger"

const BASE_URL = "http://localhost:8000"

// generate or retrieve session id
export const getSessionId = () => {
  let id = localStorage.getItem("session_id")
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem("session_id", id)
    logger.debug("New session created", id)
  }
  return id
}

export const extractRecipe = (url) => {
  logger.apiCall("POST", "/extract", { url, sessionId: getSessionId() })
  return axios.post(`${BASE_URL}/extract`, {
    url,
    session_id: getSessionId()
  }).then(res => {
    logger.apiSuccess("POST", "/extract", { title: res.data.title })
    return res
  }).catch(err => {
    logger.apiError("POST", "/extract", err.response?.data?.detail || err.message)
    throw err
  })
}

export const getHistory = () => {
  logger.apiCall("GET", "/recipes", { sessionId: getSessionId() })
  return axios.get(`${BASE_URL}/recipes`, {
    params: { session_id: getSessionId() }
  }).then(res => {
    logger.apiSuccess("GET", "/recipes", { count: res.data.recipes?.length || 0 })
    return res
  }).catch(err => {
    logger.apiError("GET", "/recipes", err.response?.data?.detail || err.message)
    throw err
  })
}

export const clearHistory = () =>
  axios.delete(`${BASE_URL}/recipes/clear`, {
    params: { session_id: getSessionId() }
  })

  
export const getRecipeDetail = (id) => {
  logger.apiCall("GET", `/recipes/${id}`, { sessionId: getSessionId() })
  return axios.get(`${BASE_URL}/recipes/${id}`, {
    params: { session_id: getSessionId() }
  }).then(res => {
    logger.apiSuccess("GET", `/recipes/${id}`, { title: res.data.title })
    return res
  }).catch(err => {
    logger.apiError("GET", `/recipes/${id}`, err.response?.data?.detail || err.message)
    throw err
  })
}

export const generateMealPlan = (recipeIds) => {
  logger.apiCall("POST", "/meal-plan", { recipeCount: recipeIds.length, sessionId: getSessionId() })
  return axios.post(`${BASE_URL}/meal-plan`, {
    recipe_ids: recipeIds,
    session_id: getSessionId()
  }).then(res => {
    const itemCount = Object.values(res.data.combined_shopping_list || {}).flat().length
    logger.apiSuccess("POST", "/meal-plan", { shoppingItems: itemCount })
    return res
  }).catch(err => {
    logger.apiError("POST", "/meal-plan", err.response?.data?.detail || err.message)
    throw err
  })
}
