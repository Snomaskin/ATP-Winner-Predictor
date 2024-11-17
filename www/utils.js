/**
 * @param {string} player1 
 * @param {string} player2 
 * @param {string} courtSurface 
 * @throws {Error} 
 */
export function predictWinner(player1, player2, courtSurface) {
    try {    
        const formData = {
            player1: ValidationUtils.formatPlayerName(player1, "Player 1"),
            player2: ValidationUtils.formatPlayerName(player2, "Player 2"),
            court_surface: courtSurface
        };
        const jsonData = JSON.stringify(formData);
        fetchData("/predict_winner", jsonData);
    } catch (clientError) {
        showSpeechBubble(clientError.message);
    }
}

/**
 * @param {string} player - "LastName FirstInitial." format
 * @throws {Error} 
 */
export function lookupPlayerStats(player) {
    try{
    const formData = {
        player: ValidationUtils.formatPlayerName(player, "Player Name")
    };
    const jsonData = JSON.stringify(formData);

    fetchData("/lookup_player_stats", jsonData);
    } catch (clientError) {
        showSpeechBubble(clientError.message);
    }
}

/**
 * @param {string} endpoint 
 * @param {string} formData 
 * @returns {Promise<string>} 
 * @throws {Error} 
 */
function fetchData(endpoint, formData){
        const BASE_URL = "https://fastapi-iywl5fy4ka-lz.a.run.app";
        fetch(BASE_URL + endpoint, {
            method: "POST",
            body: formData,
            headers: {"Content-Type": "application/json"}
        })
        .then (response => {
            if (response.status === 200)
                return response.text();
            else {
                return response.text().then(invalidResponse => {
                    invalidResponse = invalidResponse.replace('{"detail":"', '').replace('"}', ''); // Remove server error message prefix and suffix
                        throw new Error(invalidResponse);
                })
            }
        })
        .then(returnString => showSpeechBubble(returnString))
        .catch(serverError => showSpeechBubble(serverError.message));
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

const ValidationUtils = {
    /**
     * Formats a player's name as "LastName FirstInitial."
     * @param {string} name 
     * @param {string} inputField 
     * @returns {string} 
     * @throws {Error}
     */
    formatPlayerName(name, inputField) {
        if (!this.canFormatAsPlayerName(name)) {
            throw new Error(`Invalid input for "${inputField}". Please follow the name format instructions.`)
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

    // Validate format: "LastName FirstInitial."
    canFormatAsPlayerName(input) {
        return input.trim()
        .length >= 3 && input.includes(' ') && /^[A-Za-z\s.]*$/.test(input);
    },
}