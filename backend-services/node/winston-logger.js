const winston = require('winston');
const DailyRotateFile = require('winston-daily-rotate-file');
const path = require('path');


const logDir = path.join(__dirname, 'logs');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        winston.format.printf(({ level, message, timestamp, ...meta }) => {
          const metaFormatted = Object.keys(meta).length
            ? `\n${JSON.stringify(meta, null, 2)}`
            : '';
          return `${timestamp} [${level}]: ${message}${metaFormatted}`;
        })
      ),
    }),
    
    new DailyRotateFile({
      filename: path.join(logDir, 'application-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxSize: '20m',
      maxFiles: '14d',
    }),
  ],
});

module.exports = logger;
