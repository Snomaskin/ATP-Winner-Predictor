function predictWinner(player1, player2, courtSurface) {
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
function lookupPlayerStats(player) {
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
                    invalidResponse = invalidResponse.replace('{"detail":"', '').replace('"}', '');
                        throw new Error(invalidResponse);
                })
            };
        })
        .then(returnString => showSpeechBubble(returnString))
        .catch(serverError => showSpeechBubble(serverError.message));
} 

function showSpeechBubble(message) {
    const bubble = document.getElementById('speech-bubble');
    const bubbleContent = document.getElementById('speech-bubble-content');
    bubbleContent.innerText = message;
    bubble.style.display = 'block';
}

const ValidationUtils = {
    // Validate format: "LastName FirstInitial."
    canFormatAsPlayerName(input) {
        return input.trim()
        .length >= 3 && input.includes(' ') && /^[A-Za-z\s.]*$/.test(input);
    },
    /**
     * Formats a player's name as "LastName FirstInitial."
     * @param {string} name - The player's name to format.
     * @param {string} inputField - The name of the input field (used for error messages).
     * @returns {string} The formatted name in the required format.
     * @throws {Error} Throws an error if the name format is invalid.
     */
    formatPlayerName(name, inputField) {
        if (!this.canFormatAsPlayerName(name)) {
            throw new Error(`Invalid input for "${inputField}". Please follow the name format instructions.`)
        };

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
    }
};

// Reset speech bubble when clicked
document.getElementById('speech-bubble').addEventListener('click', function() {
    this.style.display = 'none';
});

// Control which form to submit:
document.getElementById("form").addEventListener("submit", function(event) {
    event.preventDefault(); showSpeechBubble('Loading...');

    const selectedForm = document.querySelector('input[name="form_selector"]:checked').value;

    if (selectedForm === "predict_winner") {
        const player1 = document.getElementById("player1").value;
        const player2 = document.getElementById("player2").value;
        const courtSurface = document.getElementById("court_surface").value;
        predictWinner(player1, player2, courtSurface);

    } else if (selectedForm === "lookup_stats") {
        const player = document.getElementById("player_name").value;
        lookupPlayerStats(player);
    };
});

//  Control which form to display:
document.querySelectorAll('input[name="form_selector"]').forEach((radio) => {
    radio.addEventListener("change", function() {
        if (this.value === "predict_winner") {
            document.getElementById("winner-prediction-fields").style.display = "block";
            document.getElementById("player-stats-fields").style.display = "none";
        } else if (this.value === "lookup_stats") {
            document.getElementById("winner-prediction-fields").style.display = "none";
            document.getElementById("player-stats-fields").style.display = "block";
        };
    });
});