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
        fetchData("/predict_winner", jsonData)
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
    try{
    const formData = {
        player: ValidationUtils.formatPlayerName(player, "player_name", "Player Name")
    };
    const jsonData = JSON.stringify(formData);

    fetchData("/lookup_player_stats", jsonData)
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
function fetchData(endpoint, formData) {
    const cacheKey = endpoint + formData;

        if (cache.has(cacheKey)) {
            return Promise.resolve(cache.get(cacheKey));
        }
        try{
            RateLimiter.checkLimit(endpoint);
            return fetch(CONFIG.API.BASE_URL + endpoint, {
                method: "POST",
                body: formData,
                headers: { "Content-Type": "application/json" },
        })
            .then((response) => {
                if (response.status === 200) {
                    return response.text().then((returnString) => {
                        cache.set(cacheKey, returnString);
                        return returnString;
                    });
                } else {
                    return response.text().then((invalidResponse) => {
                        const errorMessage = JSON.parse(invalidResponse).detail;
                        const serverError = new Error(errorMessage);
                        serverError.isServerError = true;
                        throw serverError;
                    });
                }
            });
    } catch (error) {
        console.log(`Client Error: ${error}`);
        throw error;
    }
}