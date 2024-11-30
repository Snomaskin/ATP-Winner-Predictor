import { predictWinner, lookupPlayerStats } from './comms.js';
import { ValidationUtils } from './utils.js';


export function setupFormSelect() {
    document.querySelectorAll('input[name="form_selector"]').forEach((radio) => {
        radio.addEventListener("change", function() {
            const predictionContainer = document.getElementById("winner-prediction-fields");
            const statsContainer = document.getElementById("player-stats-fields");
            const predictionInput = document.querySelectorAll("#winner-prediction-fields input");
            const statsInput = document.querySelectorAll("#player-stats-fields input");

            if (this.value === "predict_winner") {
                predictionContainer.style.display = "block";
                statsContainer.style.display = "none";
                predictionInput.forEach(input => input.required = true);
                statsInput.forEach(input => input.required = false);

            } else if (this.value === "lookup_stats") {
                predictionContainer.style.display = "none";
                statsContainer.style.display = "block";
                predictionInput.forEach(input => input.required = false);
                statsInput.forEach(input => input.required = true);
            }
        });
    });
}

export function setupFormSubmit() {
    document.getElementById("form").addEventListener("submit", (formSubmit) => {
        formSubmit.preventDefault(); loaderVisibility('showLoaderHideBubble');

        const selectedForm = document.querySelector('input[name="form_selector"]:checked').value;

        if (selectedForm === "predict_winner") {
            const player1 = document.getElementById("player1").value;
            const player2 = document.getElementById("player2").value;
            const courtSurface = document.getElementById("court_surface").value;
            predictWinner(player1, player2, courtSurface);

        } else if (selectedForm === "lookup_stats") {
            const player = document.getElementById("player_name").value;
            lookupPlayerStats(player);
            }
    });
}

export function showSpeechBubble(message) {
    const bubble = document.getElementById('speechBubble');
    const bubbleContent = document.getElementById('speechBubbleContent');
    bubbleContent.innerHTML = '';
    bubbleContent.innerText = message;
    bubble.style.display = 'block';
    loaderVisibility('hideLoader');

    bubble.addEventListener('click', () => {
        bubble.style.display = 'none';
    });
}

function loaderVisibility(mode = '') {
    const loader = document.getElementById('tennisLoader');
    const speechBubble = document.getElementById('speechBubble');

    if (mode === 'showLoaderHideBubble') {
        loader.style.display = 'block';
        speechBubble.style.display = 'none';
    } else if (mode === 'hideLoader') {
        loader.style.display = 'none';
    }
}

/**
 * @param {HTMLInputElement} inputField
 */
export function setupClearInputButton(inputField) {
    const clearButton = inputField.parentNode.querySelector('.clear-button');
    clearButton.style.display = 'none';
   
    function toggleClearButtonVisibility() {
        clearButton.style.display = inputField.value ? 'flex' : 'none'; 
    }
  
    inputField.addEventListener('input', toggleClearButtonVisibility);
    inputField.addEventListener('blur', toggleClearButtonVisibility);
    inputField.addEventListener('focus', toggleClearButtonVisibility);
  
    clearButton.addEventListener('click', () => { 
      inputField.value = '';
      inputField.focus();
    });
  }

export function setupInputValidationStyles(inputField) {
    ValidationUtils.registerValidationCallback(inputField.id, (isValid) => {
        if (!isValid) {
            inputField.classList.add('invalid');
        } else {
            inputField.classList.remove('invalid');
        }
    });
}

/**
 * Sets up the auto-lookup functionality for a given input field.
 * @param {HTMLInputElement} inputField - The input field to monitor for changes
 * @param {HTMLDivElement} suggestionsContainer - The container for displaying suggestions
 * @param {Array<Object>} playerData - An array of player objects
 */
export function setupPlayerSuggestions(inputField, suggestionsContainer, playerData) {
    inputField.addEventListener('input', () => {
        const searchTerm = inputField.value;
        if (searchTerm.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        const matchingPlayers = matchPlayers(searchTerm, playerData);
        setupSuggestionsContainer(matchingPlayers, inputField, suggestionsContainer);
        });
}

function matchPlayers(searchTerm, playerData) {
    return playerData.filter(player => 
        player.searchName.includes(searchTerm.toLowerCase()) // searchName is lowercase for case-insensitive search
    ).slice(0,5); // Find first 5 matching players
}

/**
 * Updates the player suggestionsContainer with matching players. 
 * @param {Array<Object>} players
 * @param {HTMLDivElement} suggestionsContainer
 * @param {HTMLInputElement} inputField
 */
function setupSuggestionsContainer(matchingPlayers, inputField, suggestionsContainer){
    if (matchingPlayers.length === 0){
        suggestionsContainer.style.display = 'none';
        return;
    }

    suggestionsContainer.innerHTML = '';
    const ul = document.createElement('ul');
    ul.className = 'suggestions-list';

    appendPlayerSuggestions(matchingPlayers, inputField, suggestionsContainer, ul);

    suggestionsContainer.appendChild(ul);
    suggestionsContainer.style.display = 'block';
}

/**
* @param {Array<Object>} players
* @param {HTMLInputElement} inputField 
* @param {HTMLElement} suggestionsContainer 
* @param {HTMLUListElement} ul 
*/
function appendPlayerSuggestions(matchingPlayers, inputField, suggestionsContainer, ul) {
    matchingPlayers.forEach(player => {
        const li = document.createElement('li');
        li.className = 'suggestions-item';
        // Use the correctly capitalized player name for display:
        li.innerHTML = `<div class="player-name">${player.Player}<br>
        Wins: ${player.TotalWins}
        </div>`;

        li.addEventListener('click', () => {
            inputField.value = player.Player; // Use the correctly capitalized player name for input
            suggestionsContainer.style.display = 'none';
            inputField.parentNode.querySelector('.clear-button').style.display = 'flex';
        });

        ul.appendChild(li);
    });
}