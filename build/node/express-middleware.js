const express = require('express');
const axios = require('axios');
const {checkLimit} = require ('./rate-limiter')

const app = express();
app.use(express.json());


app.post('*', async (req, res, next) => {
    try {
        const clientKey = req.ip;
        const endpoint = req.path;

        const response = await axios({
            method:req.method, 
            url: `http://localhost:8080${req.path}`,
            data: req.body, 
            headers: {'content-type': 'application/json'}
        });
        
        res.middlewareResponse = response;
        await checkLimit(clientKey, endpoint);
        
        next();
    } catch (error) {
        res.status(error.middlewareResponse?.status || 429).send(error.message);
    }
});

app.use(async (req, res) => {
    if (res.middlewareResponse) {
        res .status(res.middlewareResponse.status)
            .set(res.middlewareResponse.headers)
            .send(res.middlewareResponse.data);
    } else {
        res.status(500).send('Internal Server Error');
    }
});

app.listen(3000, () => console.log('Server running on port 3000'));