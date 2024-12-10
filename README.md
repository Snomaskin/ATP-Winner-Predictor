## Project Overview
This repository contains a comprehensive toolset for building a simple prediction application using self-collected data. The project is a personal learning experience that demonstrates a complete data processing and machine learning workflow, ultimately presented in an interactive web-based interface. 

## Project Structure
```
/
├── scraper.py
├── backend-services/
│   ├── fastapi/
│   │   └── api.py
│   │   └── prediction_model.py
│   └── node/
└── www/
│   └── webapp.html
```
### Data Collection and Processing 
`scraper.py`
#### Includes:
- **Scraper Tool**: Collect raw match data. Tuned for www.flashscore.com
- **Data Storage Tool:** Store scraped data in an SQLite database
- **Cleanup Tool**: Process and clean the collected data
- **Encoding Tool**: Prepare data for machine learning algorithms


### Machine Learning
`prediction_model.py`
- Uses Scikit-Learn Random Forest Classifier for predictions
- **Note**: Don't use predictions for anything serious. The project emphasis is on showcasing the integration of data processing and model prediction in a real-world application, rather than achieving high prediction accuracy.


### Interactive Web GUI
`webapp.html`
- **Dynamic UI**: Reactive design principles for seamless user interaction
- **User Input Handling**: Allow users to input data and receive instant (when run locally) predictions through API routing
- **Custom loading animation**: Made with CSS


### Server components
`/backend-services`
#### Includes:
- **FastAPI Server:** Handles prediction logic and data processing
- **Node.js Middleware:** For requests logging and rate limiting
- **Containerization:** Docker builds available for both backend services


## Getting Started
1. Install the required python modules from `requirements.txt`. Preferably in a virtual environment
2. Run the `scraper.py` and follow the instructions in the terminal to collect and process match data
3. Run `api.py`
4. Host a server locally and use the GUI in `webapp.html` to predict match outcomes with the match data

 
## Disclaimer
**This project is only for educational purposes.** The predictions are not reliable or accurate enough for practical applications.


## Contributions
Suggestions and improvements are welcome! If you have ideas on how to enhance the project, please feel free to open an issue or submit a pull request. Happy coding! 🚀
