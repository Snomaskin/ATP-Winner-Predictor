import { CONFIG } from './config.js';

export const ValidationUtils = {
    _validationCallbacks: new Map(),

    /**
     * Formats a player's name as "LastName FirstInitial."
     * @param {string} name 
     * @param {string} inputFieldId 
     * @param {string} displayString 
     * @returns {string} 
     * @throws {Error} clientError
     */
    formatPlayerName(name, inputFieldId, displayString) {
        const isValid = this.canFormatAsPlayerName(name);

        const callback = this._validationCallbacks.get(inputFieldId);
        if (callback) {
            callback(isValid);
        }

        if (!isValid) {
            const clientError = new Error(`Invalid input for "${displayString}". Please follow the name format instructions.`);
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
        return  input.trim().length >= 3 &&
                input.includes(' ') && 
                CONFIG.VALIDATION.NAME_REGEX.test(input);
    },

    registerValidationCallback(inputFieldId, callback) {
        this._validationCallbacks.set(inputFieldId, callback);
    },
}

export const RateLimiter = {
    requests: new Map(), // Endpoint -> [timestamp]
    maxRequests: 10,      
    timeWindow: 60000,   
    
    checkLimit(endpoint) {
        const now = Date.now();
        const recentRequests = this.requests.get(endpoint) || [];
        
        // Remove old requests
        const validRequests = recentRequests.filter(
            timeStamp => now - timeStamp < this.timeWindow
        );
        
        if (validRequests.length >= this.maxRequests) {
            throw new Error('Too many requests. Please wait before trying again.');
        }

        validRequests.push(now);
        this.requests.set(endpoint, validRequests);
    }
};