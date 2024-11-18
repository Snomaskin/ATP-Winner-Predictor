import { showSpeechBubble, predictWinner, lookupPlayerStats } from './utils.js';

/**
 * @returns {Promise<Array<Object>>}
 */
async function loadPlayerData() {
    const PLAYERS_CSV_URL = "player_index_df.csv";

    try {
        const fetchCSV = await fetch(PLAYERS_CSV_URL);
        const csvData = await fetchCSV.text();
        return parseCsvToJson(csvData);
    } catch (error) {
        console.error('Error loading player data:', error);
        return null;
    }
}

/**
 * @param {string} csvData
 * @returns {Array<Object>}
 */
function parseCsvToJson(csvData) {
    const rows = csvData.trim().split('\n');
    return rows.slice(1).map(row => { // Skip the first row (header)
        const [Player, Index, TotalWins] = row.split(',').map(item => item.trim());
        // 'searchName' for lookup and 'Player' for display:
        return {
            Player,
            Index: parseInt(Index),
            TotalWins: parseInt(TotalWins),
            searchName: Player.toLowerCase()
        }
    });
}

// Handler function. It's called when the DOM is loaded.
async function initializeDynamicElements() {
    setupFormSelect(); setupFormSubmit();

    const playerData = await loadPlayerData();

    if (!playerData) return; // Prevent function from continuing with 'null' return from a failed fetch.

    const inputFields = ['player1', 'player2', 'player_name'];

    // Setup auto-lookup and clear button for each input field:  
    inputFields.forEach(fieldId => {
        const inputField = document.getElementById(fieldId);
        
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.id = `${fieldId}-suggestion`;
        suggestionsContainer.classList.add('suggestions-container');

        setupClearInputButton(inputField); // Append clear button to the input field
        inputField.insertAdjacentElement('afterend', suggestionsContainer);
        setupPlayerSuggestions(inputField, suggestionsContainer, playerData);
    });
}

function setupFormSelect() {
    document.querySelectorAll('input[name="form_selector"]').forEach((radio) => {
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
}

function setupFormSubmit() {
    document.getElementById("form").addEventListener("submit", (formSubmit) => {
        formSubmit.preventDefault(); showSpeechBubble('Loading...');

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

/**
 * @param {HTMLInputElement} inputField
 */
function setupClearInputButton(inputField) {
    const clearButton = inputField.parentNode.querySelector('.clear-button');
    clearButton.style.display = 'none';
   
    function toggleClearButtonVisibility() {
        clearButton.style.display = inputField.value ? 'flex' : 'none'; // Show clear button if input field has a value
    }
  
    inputField.addEventListener('input', toggleClearButtonVisibility);
    inputField.addEventListener('blur', toggleClearButtonVisibility);
    inputField.addEventListener('focus', toggleClearButtonVisibility);
  
    clearButton.addEventListener('click', () => { // Clear the input field and focus on it
      inputField.value = '';
      inputField.focus();
    });
  }

/**
 * Sets up the auto-lookup functionality for a given input field.
 * @param {HTMLInputElement} inputField - The input field to monitor for changes
 * @param {HTMLDivElement} suggestionsContainer - The container for displaying suggestions
 * @param {Array<Object>} playerData - An array of player objects
 */
function setupPlayerSuggestions(inputField, suggestionsContainer, playerData) {
    // Debounce the search to make sure the function is only called for the last keystroke
    let debounceTimeout;

    inputField.addEventListener('input', () => {
        clearTimeout(debounceTimeout);

        debounceTimeout = setTimeout(() => {
            const searchTerm = inputField.value;

            if (searchTerm.length < 2) {
                suggestionsContainer.style.display = 'none';
                return;
            }
            
            const matchingPlayers = matchPlayers(searchTerm, playerData);
            setupSuggestionsContainer(matchingPlayers, suggestionsContainer, inputField);
        });
    });
}

function matchPlayers(searchTerm, playerData) {
    return playerData.filter(player => 
        player.searchName.includes(searchTerm.toLowerCase()) // searchName is lowercase for case-insensitive search
    ).slice(0,5); // Find first 5 matching players
}

/**
 * Updates the player suggestions display based on the matching players. 
 * @param {Array<Object>} players
 * @param {HTMLDivElement} suggestionsContainer
 * @param {HTMLInputElement} inputField
 */
function setupSuggestionsContainer(players, suggestionsContainer, inputField){
    if (players.length === 0){
        suggestionsContainer.style.display = 'none';
        return;
    }

    suggestionsContainer.innerHTML = '';
    const ul = document.createElement('ul');
    ul.className = 'suggestions-list';

    appendPlayerSuggestions(players, inputField, suggestionsContainer, ul);

    suggestionsContainer.appendChild(ul);
    suggestionsContainer.style.display = 'block';
}

/**
* @param {Array<Object>} players
* @param {HTMLInputElement} inputField 
* @param {HTMLElement} suggestionsContainer 
* @param {HTMLUListElement} ul 
*/
function appendPlayerSuggestions(players, inputField, suggestionsContainer, ul) {
    players.forEach(player => {
        const li = document.createElement('li');
        li.className = 'suggestions-item';
        // Use the correctly capitalized player name for display:
        li.innerHTML = `
            <div class="player-name">${player.Player}<br>
                Wins: ${player.TotalWins}
            </div>
        `;
        li.addEventListener('click', () => {
            inputField.value = player.Player; // Use the correctly capitalized player name for input
            suggestionsContainer.style.display = 'none';
            inputField.parentNode.querySelector('.clear-button').style.display = 'flex';
        });

        ul.appendChild(li);
    });
}


document.addEventListener('DOMContentLoaded', initializeDynamicElements);