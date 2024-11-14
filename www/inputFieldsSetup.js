/**
 * @returns {Array<Object>} An array of player objects
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
    };
};

/**
 * @param {string} csvData - The CSV data to parse
 * @returns {Array<Object>} An array of player objects
 */
function parseCsvToJson(csvData){
    const rows = csvData.trim().split('\n');
    return rows.slice(1).map(row => { // Skip the first row (header)
        const [Player, Index, TotalWins] = row.split(',').map(item => item.trim());
        // 'searchName' for lookup and 'Player' for display:
        return {
            Player,
            Index: parseInt(Index),
            TotalWins: parseInt(TotalWins),
            searchName: Player.toLowerCase()
        };
    });
};

// Handler function for initializing the input fields. It's called when the DOM is loaded.
async function setupInputFields(){
    const playerData = await loadPlayerData();
    if (!playerData) return; // Prevent function from continuing with 'null' return from a failed fetch.

    const inputFields = ['player1', 'player2', 'player_name'];

    // Setup auto-lookup and clear button for each input field:  
    inputFields.forEach(fieldId => {
        const inputField = document.getElementById(fieldId);
        
        const suggestionsContainer = document.createElement('div');

        suggestionsContainer.id = `${fieldId}-suggestion`;
        suggestionsContainer.style.display = 'none';

        setupClearInputButton(inputField); // Append clear button to the input field

        inputField.insertAdjacentElement('afterend', suggestionsContainer);
        setupAutoLookup(inputField, suggestionsContainer, playerData)
    });
};
/**
 * @param {HTMLInputElement} inputField - The input field to add the clear button to
 */
function setupClearInputButton(inputField) {
    const clearButton = document.createElement('span');
    clearButton.classList.add('clear-button');
    clearButton.textContent = 'X';
    clearButton.style.display = 'none';
    inputField.parentNode.appendChild(clearButton); // Append clear button to the input field
  
    function toggleClearButtonVisibility() {
        clearButton.style.display = inputField.value ? 'flex' : 'none'; // Show clear button if input field has a value
    };
  
    inputField.addEventListener('input', toggleClearButtonVisibility);
    inputField.addEventListener('blur', toggleClearButtonVisibility);
    inputField.addEventListener('focus', toggleClearButtonVisibility);
  
    clearButton.addEventListener('click', () => { // Clear the input field and focus on it
      inputField.value = '';
      inputField.focus();
    });
  };

/**
 * Sets up the auto-lookup functionality for a given input field.
 * @param {HTMLInputElement} inputField - The input field to monitor for changes
 * @param {HTMLDivElement} suggestionsContainer - The container for displaying suggestions
 * @param {Array<Object>} playerData - An array of player objects
 */
function setupAutoLookup(inputField, suggestionsContainer, playerData) {
    // Debounce the search to make sure function is only called for the last keystroke
    let debounceTimeout;

    inputField.addEventListener('input', () => {
        clearTimeout(debounceTimeout);

        debounceTimeout = setTimeout(() => {
            const searchTerm = inputField.value;

            if (searchTerm.length < 2) { // Prevent search if input is less than 2 characters
                suggestionsContainer.style.display = 'none';
                return;
            };

            const matchingPlayers = playerData.filter(player => 
                player.searchName.includes(searchTerm.toLowerCase()) // searchName is lowercase for case-insensitive search
            ).slice(0,5); // Find first 5 matching players
            updatePlayerSuggestions(matchingPlayers, suggestionsContainer, inputField);
        });
    });
};

/**
 * Updates the player suggestions display based on the matching players. 
 * @param {Array<Object>} players - An array of player objects
 * @param {HTMLDivElement} container - The container for displaying suggestions
 * @param {HTMLInputElement} inputField - The input field to monitor for changes
 */
function updatePlayerSuggestions(players, suggestionsContainer, inputField){
    if (players.length === 0){
        suggestionsContainer.style.display = 'none';
        return;
    };

    suggestionsContainer.innerHTML = '';
    const ul = document.createElement('ul');
    ul.className = 'suggestions-list';

    players.forEach(player => {
        const li = document.createElement('li');
        li.className = 'suggestions-item';
        // Use the correctly capitalized player name for display:
        li.innerHTML = `
            <div class="player-name">${player.Player}</div>
                Wins: ${player.TotalWins}
            </div>
        `;
        li.addEventListener('click', () => {
            inputField.value = player.Player; // Use the correctly capitalized player name for input
            suggestionsContainer.style.display = 'none';
        });

        ul.appendChild(li);
    });
    suggestionsContainer.appendChild(ul);
    suggestionsContainer.style.display = 'block';
    suggestionsContainer.style.position = 'absolute';
    suggestionsContainer.style.width = inputField.offsetWidth + 'px';
};

document.addEventListener('DOMContentLoaded', setupInputFields);