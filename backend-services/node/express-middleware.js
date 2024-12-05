const express = require('express');
const cors = require('cors');
const axios = require('axios');
const { checkLimit } = require('./rate-limiter')
const { logValidRequest, logInvalidRequest } = require('./log-body-config')

const app = express();

app.use(express.json());

app.use(cors({
    origin: '*',
    methods: 'POST',
}))

app.post('*', async (req, res) => {
    const startTime = Date.now();

    try {
        const clientKey = req.ip;
        const endpoint = req.path;
        await checkLimit(clientKey, endpoint);

        const response = await axios({ // Axios calls the server
            method:req.method, 
            url: `http://localhost:8080${req.path}`,
            data: req.body, 
            headers: { "Content-Type": "application/json" }      
        });

        logValidRequest(req, res, startTime);        
        res.status(response.status).send(response.data);

    } catch (error) {
        logInvalidRequest(req, res, startTime);
        res.status(error.response.status).send(error.response.message);
    }
});

app.options('*', cors())

app.listen(3000, () => console.log('Server running on port 3000'));