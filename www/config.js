export const CONFIG = {
    API: {
        BASE_URL: "http://localhost:8000/",
        TIMEOUT: 5000,
        CACHE_DURATION: 1000 * 60 * 5
    },
    VALIDATION: {
        NAME_MIN_LENGTH: 3,
        NAME_REGEX: /^[A-Za-z\s.-]*$/
    },
    DOCS: {
        PLAYERS_DF: "./player_index_df.csv"
    },
};