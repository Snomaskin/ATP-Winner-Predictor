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

function parseCsvToJson(csvData){
    const rows = csvData.trim().split('\n');
    return rows.slice(1).map(row => {
        const [Player, Index, TotalWins] = row.split(',').map(item => item.trim());
        // 'searchName' for lookup and 'Player' for display:
        return {
            Player,
            Index: parseInt(Index),
            TotalWins: parseInt(TotalWins),
            searchName: Player.toLowerCase()
        };
    });
}

function setupAutoLookup(inputField, suggestionsContainer, playerData) {
    let debounceTimeout;

    inputField.addEventListener('input', () => {
        clearTimeout(debounceTimeout);

        debounceTimeout = setTimeout(() => {
            const searchTerm = inputField.value.toLowerCase();

            if (searchTerm.length < 2) {
                suggestionsContainer.style.display = 'none';
                return;
            }

            // Find first 5 matching players
            const matchingPlayers = playerData.filter(player => 
                player.searchName.includes(searchTerm)
            ).slice(0,5);
            updatePlayerSuggestions(matchingPlayers, suggestionsContainer, inputField)
        })
    })
}

function updatePlayerSuggestions(players, container, inputField){
    if (players.length === 0){
        container.style.display = 'none';
        return;
    }

    container.innerHTML = '';
    const ul = document.createElement('ul');
    ul.className = 'suggestions-list';

    players.forEach(player => {
        const li = document.createElement('li');
        li.className = 'suggestions-item';
        li.innerHTML = `
            <div class="player-name">${player.Player}</div>
            <div class="player-stats">
                Wins: ${player.TotalWins}
            </div>
        `;
        li.addEventListener('click', () => {
            inputField.value = player.Player;
            container.style.display = 'none';
        });

        ul.appendChild(li);
    });
    container.appendChild(ul);
    container.style.display = 'block';
    container.style.position = 'absolute';
    container.style.width = inputField.offsetWidth + 'px';
}

async function initializeAutoLookup(){
    const playerData = await loadPlayerData();
    if (!playerData) return; // Prevent function from using the 'null' return from failed fetch.

    const inputFields = ['player1', 'player2', 'player_name'];

    inputFields.forEach(fieldId => {
        const inputField = document.getElementById(fieldId);

        if (!fieldId) return;
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.id = `${fieldId}-suggestion`;
        suggestionsContainer.style.display = 'none';
        inputField.insertAdjacentElement('afterend', suggestionsContainer);

        setupAutoLookup(inputField, suggestionsContainer, playerData)
    });
}

document.addEventListener('DOMContentLoaded', initializeAutoLookup);