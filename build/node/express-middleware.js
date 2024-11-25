const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());


app.post('*', async (req, res, next) => {
    try {
        const response = await axios({
            method:req.method, 
            url: `http://localhost:8080${req.path}`,
            data: req.body, 
            headers: {'content-type': 'application/json'}
        });
        
        res.fastapiResponse = response;
        next();
    } catch (error) {
        res.status(error.response?.status || 500).send(error.message);
    }
});

app.use(async (req, res) => {
    if (res.fastapiResponse) {
        res .status(res.fastapiResponse.status)
            .set(res.fastapiResponse.headers)
            .send(res.fastapiResponse.data);
    } else {
        res.status(500).send('Internal Server Error');
    }
});

app.listen(3000, () => console.log('Server running on port 3000'));