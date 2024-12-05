const logger = require('./winston-logger');


const logValidRequest = (req, res, startTime) => {
  const duration = Date.now() - startTime;
  
  logger.info('API Request', {
    method: req.method,
    path: req.path.split('/').pop(),
    statusCode: res.statusCode,
    responseTime: duration,
    requestBody: req.body,
    userAgent: req.get('User-Agent'),
    ipAddress: req.ip,
    responseBody: res.data
  });

}
x
const logInvalidRequest = (req, res, startTime) => {
  const duration = Date.now() - startTime;

  logger.error('API Error', {
    method: req.method,
    path: req.path.split('/').pop(),
    statusCode: res.statusCode,
    responseTime: duration,
    requestBody: req.body,
    userAgent: req.get('User-Agent'),
    ipAddress: req.ip,
    responseBody: res.data
  });

}

module.exports = {
  logValidRequest, 
  logInvalidRequest
}