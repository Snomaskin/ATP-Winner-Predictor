export const CONFIG = {
    API: {
        BASE_URL: "http://localhost:8080",
        TIMEOUT: 5000,
        CACHE_DURATION: 1000 * 60 * 5,
    },
    VALIDATION: {
        NAME_MIN_LENGTH: 3,
        NAME_REGEX: /^[A-Za-z\s.-]*$/,
    },
    DOCS: {
        PLAYERS_DF: "./player_index_df.csv",
    },
    ENDPOINTS: {
        WINNER_PREDICTION: "/predict_winner",
        STATS_LOOKUP: "/lookup_player_stats",
    },
    FETCH_OPTIONS: {
        method: "POST",
        headers: { "Content-Type": "application/json" },
    }
};