const NodeCache = require('node-cache')
const cache = new NodeCache()

const RateLimitConfig = {
    maxRequests: 10,      
    expiration: 60,
}
    
async function checkLimit(clientKey, endpoint) {
    const key = `${clientKey}-${endpoint}`;
    let currentCount = cache.get(key) || 0;

    if (currentCount > RateLimitConfig.maxRequests) {
        throw new Error('Too many requests. Please wait before trying again.');
    }

    cache.set(key, currentCount + 1, RateLimitConfig.expiration)
}

module.exports = {
    checkLimit,
}