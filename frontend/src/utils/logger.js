// Frontend logging utility with color-coded console output

const COLORS = {
  INFO: '#0066cc',     // Blue
  SUCCESS: '#00aa00',   // Green
  WARNING: '#ff8800',   // Orange
  ERROR: '#cc0000',     // Red
  DEBUG: '#666666',     // Gray
  CLICK: '#9933ff',     // Purple
  API: '#0088aa'        // Teal
}

const EMOJIS = {
  INFO: 'ℹ️',
  SUCCESS: '✅',
  WARNING: '⚠️',
  ERROR: '❌',
  DEBUG: '🔍',
  CLICK: '🖱️',
  API: '📡',
  REQUEST: '📤',
  RESPONSE: '📥',
  LOADING: '⏳',
  COMPLETE: '🎉'
}

function getTimestamp() {
  const now = new Date()
  return now.toLocaleTimeString('en-US', { 
    hour12: true, 
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3
  })
}

function log(level, emoji, color, message, data) {
  const timestamp = getTimestamp()
  const prefix = `[${timestamp}] ${emoji}`
  
  if (data) {
    console.log(`%c${prefix} ${message}`, `color: ${color}; font-weight: bold;`, data)
  } else {
    console.log(`%c${prefix} ${message}`, `color: ${color}; font-weight: bold;`)
  }
}

export const logger = {
  // Button clicks and user interactions
  buttonClick: (buttonName, details) => {
    log('CLICK', EMOJIS.CLICK, COLORS.CLICK, `Button clicked: ${buttonName}`, details || '')
  },

  // Tab navigation
  tabSwitch: (tabName) => {
    log('INFO', EMOJIS.INFO, COLORS.INFO, `Switched to tab: ${tabName}`)
  },

  // API calls
  apiCall: (method, endpoint, data) => {
    console.log(`%c[${getTimestamp()}] ${EMOJIS.REQUEST} API ${method} ${endpoint}`, `color: ${COLORS.API}; font-weight: bold;`, data || '')
  },

  apiSuccess: (method, endpoint, data) => {
    console.log(`%c[${getTimestamp()}] ${EMOJIS.RESPONSE} API ${method} ${endpoint} - Success`, `color: ${COLORS.SUCCESS}; font-weight: bold;`, data || '')
  },

  apiError: (method, endpoint, error) => {
    console.log(`%c[${getTimestamp()}] ${EMOJIS.ERROR} API ${method} ${endpoint} - Error`, `color: ${COLORS.ERROR}; font-weight: bold;`, error || '')
  },

  // Loading states
  loading: (message) => {
    log('INFO', EMOJIS.LOADING, COLORS.WARNING, message)
  },

  loadingComplete: (message) => {
    log('SUCCESS', EMOJIS.COMPLETE, COLORS.SUCCESS, message)
  },

  // User actions
  urlInput: (url) => {
    log('DEBUG', EMOJIS.DEBUG, COLORS.DEBUG, `URL entered`, url)
  },

  extractStart: (url) => {
    log('INFO', EMOJIS.INFO, COLORS.INFO, `Starting extraction for: ${url}`)
  },

  extractComplete: (title, duration) => {
    log('SUCCESS', EMOJIS.SUCCESS, COLORS.SUCCESS, `Extraction complete: ${title}`, `Duration: ${duration}ms`)
  },

  extractError: (error) => {
    log('ERROR', EMOJIS.ERROR, COLORS.ERROR, `Extraction failed`, error)
  },

  recipeDetail: (recipeId, title) => {
    log('INFO', EMOJIS.INFO, COLORS.INFO, `Viewing details for: ${title} (ID: ${recipeId})`)
  },

  mealPlanStart: (count) => {
    log('INFO', EMOJIS.INFO, COLORS.INFO, `Generating meal plan with ${count} recipe(s)`)
  },

  mealPlanComplete: (shoppingItems) => {
    log('SUCCESS', EMOJIS.SUCCESS, COLORS.SUCCESS, `Meal plan generated`, `${shoppingItems} items in shopping list`)
  },

  mealPlanError: (error) => {
    log('ERROR', EMOJIS.ERROR, COLORS.ERROR, `Meal plan generation failed`, error)
  },

  recipeSelect: (recipeId, title, selected) => {
    const status = selected ? 'selected' : 'deselected'
    log('DEBUG', EMOJIS.DEBUG, COLORS.DEBUG, `Recipe ${status}: ${title} (ID: ${recipeId})`)
  },

  // Generic methods
  info: (message, data) => log('INFO', EMOJIS.INFO, COLORS.INFO, message, data),
  success: (message, data) => log('SUCCESS', EMOJIS.SUCCESS, COLORS.SUCCESS, message, data),
  warning: (message, data) => log('WARNING', EMOJIS.WARNING, COLORS.WARNING, message, data),
  error: (message, data) => log('ERROR', EMOJIS.ERROR, COLORS.ERROR, message, data),
  debug: (message, data) => log('DEBUG', EMOJIS.DEBUG, COLORS.DEBUG, message, data),
}
