const redisClient = require('redis').createClient()
redisClient.connect()

const RateLimitConfig = {
    maxRequests: 10,      
    expiration: 60000,
}
    
async function checkLimit(clientKey, endpoint) {
    const key = `${clientKey}-${endpoint}`;
    
    const currentCount = await redisClient.incr(key);
    if (currentCount === 1){
        await redisClient.expire(key, RateLimitConfig.expiration / 1000); // Set TTL for first iteration
    }
    if (currentCount > RateLimitConfig.maxRequests) {
        throw new Error('Too many requests. Please wait before trying again.');
    }
}

module.exports = {
    checkLimit,
}