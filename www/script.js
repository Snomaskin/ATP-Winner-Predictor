function predictWinner() {
    const formData = {
        player1: document.getElementById("player1").value,
        player2: document.getElementById("player2").value,
        court_surface: document.getElementById("court_surface").value
    };
    const jsonData = JSON.stringify(formData);

    fetchData("https://fastapi-iywl5fy4ka-lz.a.run.app/predict_winner", jsonData)
    .then(winnerName => showSpeechBubble(winnerName))
    .catch(error => showSpeechBubble(error.message));
}

function lookupPlayerStats() {
    const formData = {
        player: document.getElementById("player_name").value
    };
    const jsonData = JSON.stringify(formData);

    fetchData("https://fastapi-iywl5fy4ka-lz.a.run.app/lookup_player_stats", jsonData)
    .then(playerStats => showSpeechBubble(playerStats))
    .catch(error => showSpeechBubble(error.message));
}  

function showSpeechBubble(message) {
    const bubble = document.getElementById('speech-bubble');
    const bubbleContent = document.getElementById('speech-bubble-content');
    bubbleContent.innerText = message;
    bubble.style.display = 'block';
}

function fetchData(url, formData){
    return fetch(url, {
        method: "POST",
        body: formData,
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then (response => {
        if (response.status === 200)
            return response.text();
        else {
            return response.text().then(invalidResponse => {
                invalidResponse = invalidResponse.replace('{"detail":"', '').replace('"}', '');
                    throw new Error(invalidResponse);
            })
        }
    });
}

document.getElementById('speech-bubble').addEventListener('click', function() {
    this.style.display = 'none';
});

document.getElementById("operation-form").addEventListener("submit", (formSubmit) => {
    formSubmit.preventDefault(); showSpeechBubble('Loading...');

    const operation = document.querySelector('input[name="operation"]:checked').value;

    if (operation === "predict_winner") {
        predictWinner();
    } else if (operation === "lookup_stats") {
        lookupPlayerStats();
    }
});
//  Control which form to display:
document.querySelectorAll('input[name="operation"]').forEach(radio => {
    radio.addEventListener("change", function() {
        if (this.value === "predict_winner") {
            document.getElementById("winner-prediction-fields").style.display = "block";
            document.getElementById("player-stats-fields").style.display = "none";
        } else if (this.value === "lookup_stats") {
            document.getElementById("winner-prediction-fields").style.display = "none";
            document.getElementById("player-stats-fields").style.display = "block";
        }
    });
});