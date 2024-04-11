# ATP-Winner-Predictor
Predict who wins a matchup between two ranked tennis players.

This is my first project and it was only developed for my own learning experience.
Please don't use the program for betting. It's just for fun and the predictions are not that accurate.


Use TennisScraper to collect and sort data. The code follows a step-by-step process from top to bottom. 
Once all the source code has been gathered you only have to run it through 'process_matches' and it will scrape the relevant data and add it to an SQLite database. 

Output from the the scraper contains a lot of old data so we have to make some adjustments with DataCleanup before it can be fed to the prediction algorithm. 

From there the data has to be encoded so it can be understood by the Scikit-learn RandomForest prediction algorithm. Just follow all the steps in PredictionModel -> PrepareDataframe.

Now you can run UserInterface and, if all has gone well, you should be able make prediction requests to ModelOperations by following the on-screen instructions.



If you have suggestions for how things can be done better I would be glad to hear them :-)