import { ValidationUtils, RateLimiter } from './utils.js';
import { showSpeechBubble } from './dynamic-content.js';
import { CONFIG } from './config.js';

/**
 * @param {string} player1 
 * @param {string} player2 
 * @param {string} courtSurface 
 */
export function predictWinner(player1, player2, courtSurface) {
    try {    
        const formData = {
            player1: ValidationUtils.formatPlayerName(player1, "player1", "Player 1"),
            player2: ValidationUtils.formatPlayerName(player2, "player2", "Player 2"),
            court_surface: courtSurface
        };
        const jsonData = JSON.stringify(formData);
        fetchData(CONFIG.ENDPOINTS.WINNER_PREDICTION, jsonData)
        .then(returnString => showSpeechBubble(returnString))
        .catch((serverError) => {
            showSpeechBubble(serverError.message);
            console.log(`Server Error: ${serverError}`);
        });
        } catch (clientError) {
            console.log(`Client Error: ${clientError}`);
            showSpeechBubble(clientError.message);
        }
}

/**
 * 
 * @param {string} player - "LastName FirstInitial." format
 */
export function lookupPlayerStats(player) {
    try {
    const formData = {
        player: ValidationUtils.formatPlayerName(player, "player_name", "Player Name")
    };
    const jsonData = JSON.stringify(formData);

    fetchData(CONFIG.ENDPOINTS.STATS_LOOKUP, jsonData)
    .then(returnString => showSpeechBubble(returnString))
    .catch((serverError) => {
        showSpeechBubble(serverError.message);
        console.log(`Server Error: ${serverError}`);
    });
    } catch (clientError) {
        console.log(`Client Error: ${clientError}`);
        showSpeechBubble(clientError.message);
    }
}

/**
 * @param {string} endpoint 
 * @param {string} formData 
 * @returns {Promise<string>} 
 * @throws {Error} serverError
 */
const cache = new Map();
async function fetchData(endpoint, formData) {
    const cacheKey = endpoint + formData;

    if (cache.has(cacheKey)) {
        return Promise.resolve(cache.get(cacheKey));
    }
    try {
        RateLimiter.checkLimit(endpoint);
        response = await fetch(CONFIG.API.BASE_URL + endpoint, {
            ...CONFIG.FETCH_OPTIONS,
            body: formData,
        });
        return handleResponse(response, cacheKey);
    } catch (error) {
        console.log(`Client Error: ${error}`);
        throw error;
    }
}

async function handleResponse(response, cacheKey) {
    if (response.status === 200) {
        const returnString = await response.text();
        cache.set(cacheKey, returnString);
        return returnString;
    } else {
        const invalidResponse = await response.text();
        const errorMessage = JSON.parse(invalidResponse).detail;
        const serverError = new Error(errorMessage);
        serverError.isServerError = true;
        throw serverError;
        };
}