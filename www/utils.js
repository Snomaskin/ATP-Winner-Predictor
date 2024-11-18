/**
 * @param {string} player1 
 * @param {string} player2 
 * @param {string} courtSurface 
 */
export function predictWinner(player1, player2, courtSurface) {
    try {    
        const formData = {
            player1: ValidationUtils.formatPlayerName(player1, "Player 1"),
            player2: ValidationUtils.formatPlayerName(player2, "Player 2"),
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
        player: ValidationUtils.formatPlayerName(player, "Player Name")
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

export function showSpeechBubble(message) {
    const bubble = document.getElementById('speech-bubble');
    const bubbleContent = document.getElementById('speech-bubble-content');
    bubbleContent.innerText = message;
    bubble.style.display = 'block';

    bubble.addEventListener('click', () => {
        bubble.style.display = 'none';
    });

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
    const BASE_URL = "https://fastapi-iywl5fy4ka-lz.a.run.app";

    if (cache.has(cacheKey)) {
        return Promise.resolve(cache.get(cacheKey));
    }

    return fetch(BASE_URL + endpoint, {
        method: "POST",
        body: formData,
        headers: {"Content-Type": "application/json"}
    })
    .then (response => {
        if (response.status === 200) {
            return response.text().then(returnString =>{
                cache.set(cacheKey, returnString);
                return returnString;
            });
        } else {
            return response.text().then(invalidResponse => {
                const errorMessage = JSON.parse(invalidResponse).detail;
                const serverError = new Error(errorMessage);
                serverError.isServerError = true;
                    throw serverError;
            });
        }
    });
} 

const ValidationUtils = {
    /**
     * Formats a player's name as "LastName FirstInitial."
     * @param {string} name 
     * @param {string} inputField 
     * @returns {string} 
     * @throws {Error} clientError
     */
    formatPlayerName(name, inputField) {
        if (!this.canFormatAsPlayerName(name)) {
            const clientError = new Error(`Invalid input for "${inputField}". Please follow the name format instructions.`);
            clientError.isClientError = true;
            throw clientError
        }

        return name.trim().split(' ')
            .map((part, index, arr) => {
                // Format FirstInitial.
                if (index === arr.length -1) {
                    return part.charAt(0).toUpperCase() + ".";
                }
                // Format LastName.
                return part.charAt(0).toUpperCase() + part.slice(1).toLowerCase();
            })
            .join(" ");
    },

    canFormatAsPlayerName(input) {
        return input.trim()
        .length >= 3 && input.includes(' ') && /^[A-Za-z\s.]*$/.test(input);
    },
}