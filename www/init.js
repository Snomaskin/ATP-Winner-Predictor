import { DataUtils } from "./utils.js";
import { setupFormSelect, setupFormSubmit, 
        setupClearInputButton, setupInputValidationStyles,
        setupPlayerSuggestions } from "./dynamic-content.js";

// Handler function. It's called when the DOM is loaded.
async function initializeDynamicElements() {
    setupFormSelect(); 
    setupFormSubmit();

    const playerData = await DataUtils.loadPlayerData();

    if (!playerData) return; // Prevent function from continuing with 'null' return from a failed fetch.

    const inputFields = ['player1', 'player2', 'player_name'];

    // Setup for input fields:  
    inputFields.forEach(fieldId => {
        const inputField = document.getElementById(fieldId);
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.id = `${fieldId}-suggestion`;
        suggestionsContainer.classList.add('suggestions-container');

        setupInputValidationStyles(inputField);
        setupClearInputButton(inputField);
        inputField.insertAdjacentElement('afterend', suggestionsContainer);
        setupPlayerSuggestions(inputField, suggestionsContainer, playerData);
    });
}

document.addEventListener('DOMContentLoaded', initializeDynamicElements);