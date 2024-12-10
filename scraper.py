import os
import re
import sqlite3
import hashlib
from hashlib import sha256

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, NoSuchElementException




'''
A web scraper to get tennis match data from www.flashscore.com and store it in an Sqlite database.
Currently it is only tuned for men's ATP singles.
There's a clickable button on each event result page to load more matches. 
I have not been able to get Selenium to click this.

TennisScraper:
Launches starting page with Selenium webdriver. 
From there it goes through the whole event list (limit this for testing) and clicks through the archive list for each
event to get to the match data. 

DataStorage:
Collects the scraped data and stores it in a local Sqlite database. It will not overwrite an existing database, only add more matches to it.
Outputs: 'data.db'

DataCleanup:
The scraped data contains a lot of old match data and all entries are missing year in MatchDate (it's in EventID).
This class of methods takes care of all that so that we can delete all old data we don't need for prediction.
Requires 'event_courtsurfaces.csv'.

PrepareDataframe:
Encodes the data for modelling.
Requires 'data.db' from previous steps.

The script will autorun and handle everything if you have all the plugins + chromedriver.exe. Just run 'scraper.py' and follow the instructions.
Final outputs: 'model_df.csv', 'player_index.csv', 'court_surface_index.csv'

'''


class TennisMatchScraper:
    def __init__(self, auto_run= False):
        self.driver = self.launch_browser()

        if auto_run:
            self.pipeline()

    def launch_browser(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://www.flashscore.com/tennis/')

        return driver
    
    def pipeline(self):
        archive_it, years_it = self.set_scraper_scope()
        event_archive_links = self.get_event_archive_links()
        scraper_link_list = self.get_link_list(event_archive_links, archive_it, years_it)
        all_source_code = self.get_source_code(scraper_link_list)
        self.process_matches(all_source_code)
    
    def set_scraper_scope(self):
        while True:
            archive_iterations = int(input("Number of tournaments to scrape: ").strip())
            years_iterations = int(input("Number of years per tournament to scrape: ").strip())

            return archive_iterations, years_iterations
            
    def get_event_archive_links(self):
        menu = WebDriverWait(self.driver, 10).until(
            expected_conditions.visibility_of_element_located((By.XPATH, '//*[@id="lmenu_5724"]')))
        self.driver.execute_script("arguments[0].click();", menu)
        event_elements = self.driver.find_elements(By.XPATH, '//a[starts-with(@href, "/tennis/atp-singles/")]')

        # List to store links for the archive directory for each event.
        event_archive_links = []

        for element in event_elements:
            event_link = element.get_attribute('href')
            # Append 'archive/' to get the right page. It's not pretty but it works.
            archive_append = "archive/"
            event_archive_link = event_link + archive_append
            event_archive_links.append(event_archive_link)

        return event_archive_links

    def get_link_list(self, event_archive_links: list[str], archive_it, years_it) -> list[str]:
        scraper_link_list = []

        for link in event_archive_links[:archive_it]:
            try:
                self.driver.get(link)
                WebDriverWait(self.driver, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "#fsbody .archive__season a.archive__text--clickable[href*='atp-singles/']")))
                elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                     "#fsbody .archive__season a.archive__text--clickable[href*='atp-singles/']")
                # Adjust number of iterations for how far back in time to scrape.
                for element in elements[:years_it]:
                    event_link = element.get_attribute('href')
                    # Append 'results/' to get the right page.
                    results_append = "results/"
                    full_link = event_link + results_append
                    scraper_link_list.append(full_link)

            except TimeoutException:
                print(f"TimeoutException occurred for link: {link}")
            except Exception as e:
                print(f"An error occurred for link {link}: {e}")

        return scraper_link_list

    def get_source_code(self, scraper_link_list: list[str]) -> list[str]:
        # List to store the source code for all events to be scraped.
        all_source_code = []

        for link in scraper_link_list:
            self.driver.get(link)
            # Some events are empty, so we need to check for 'event__match' to make sure there's data to scrape.
            try:
                WebDriverWait(self.driver, 5).until(
                    expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'event__match')))
            except TimeoutException:
                print(f"Unable to find 'event__match' element for link {link}. Skipping.")
                continue
            all_source_code.append(self.driver.page_source)

        return all_source_code
    
    def process_matches(self, all_source_code: list[str]):
        database = DataStorage()
        db_connect = database.database_connect()
        # The source code of each event is fed to the scraper and the extracted data is added to the database.
        for event in all_source_code:
            event_matches = self.scraper(event)
            if event_matches:
                database.append_data(db_connect, event_matches)

    # Does not work yet.
    def click_more_matches(self):
        try:
            more_matches = WebDriverWait(self.driver, 10).until(
                expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'event__more')))
            self.driver.execute_script("arguments[0].click();", more_matches)
        except NoSuchElementException as element:
            print(f'No clickable element for {element}')

    def scraper(self, event_source_code: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(event_source_code, 'html.parser')
        match_div = soup.find('div', class_='event__match')
        event_id = soup.find('title').text

        if match_div and match_div['id'].startswith('g_'):
            matches = soup.find_all('div', class_='event__match')

            # List to store scraped match data.
            event_matches = []

            for match in matches:
                try:
                    # MatchID and MatchDate
                    match_id = match['id']
                    match_date = match.find('div', class_='event__time').text

                    # Player1
                    player_1 = match.find('div', class_='event__participant--home').text
                    flag_player_1 = match.find('span', class_='event__logo--home')
                    player_1_country = flag_player_1.get('title')
                    # Country has to be changed for political reasons:
                    if player_1_country == 'World':
                        player_1_country = 'Russia'

                    # Player2
                    player_2 = match.find('div', class_='event__participant--away').text
                    flag_player_2 = match.find('span', class_='event__logo--away')
                    player_2_country = flag_player_2.get('title')
                    if player_2_country == 'World':
                        player_2_country = 'Russia'

                    # Collect won sets to determine winner.
                    player_1_sets = int(match.find('div', class_='event__score--home').text)
                    player_2_sets = int(match.find('div', class_='event__score--away').text)

                    if player_1_sets > player_2_sets:
                        winner = player_1
                        loser = player_2
                    else:
                        winner = player_2
                        loser = player_1

                    # Dict. to store unique values for each match.
                    event_matches.append({'event_id': event_id, 'match_id': match_id, 'match_date': match_date,
                                          'player_1': player_1, 'player_1_country': player_1_country,
                                          'player_2': player_2, 'player_2_country': player_2_country,
                                          'winner': winner, 'loser': loser})
                except Exception as e:
                    print(f"Error processing match: {e}")
                    continue
            else:
                print("Match element not found")

            return event_matches


class DataStorage():
    def database_connect(self):
        try:
            # Establish connection to database and create a new one if none exists.
            db_path = "data.db"
            db_connect = sqlite3.connect(db_path)
            create_table_query = """
            CREATE TABLE IF NOT EXISTS MensATPSingles (
            EventID TEXT,
            MatchID TEXT PRIMARY KEY,
            MatchDate TEXT, 
            Player1 TEXT,
            Player1Country TEXT,
            Player2 TEXT, 
            Player2Country TEXT,
            Winner TEXT,
            Loser TEXT
            )
            """
            db_connect.execute(create_table_query)
            db_connect.commit()

            return db_connect

        except sqlite3.Error as e:
            print(f"Database connection error: {e}")

            return None

    def append_data(self, dbconnect, event_matches: list[dict[str, str]]):
        cursor = dbconnect.cursor()
        insert_query = ("INSERT INTO MensATPSingles (EventID, MatchID, MatchDate, Player1, Player1Country, Player2, "
                        "Player2Country, Winner, Loser) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
        # Append scraped data to the database.
        # Insert query must follow the order specified in template above.
        for data in event_matches:
            try:
                # MatchID are reused over different events, so we have to create a unique PRIMARY KEY for each match.
                match_hash = self.create_match_id(data)
                cursor.execute(insert_query,
                               (data['event_id'], match_hash, data['match_date'], data['player_1'],
                                data['player_1_country'], data['player_2'], data['player_2_country'],
                                data['winner'], data['loser']))
            except sqlite3.IntegrityError:
                print(f"MatchID: {data['match_id']} already exists. Skipping to next entry.")
                continue
        dbconnect.commit()

    def create_match_id(self, data: dict[str, str]) -> str:
        hasher = sha256()
        hash = f"{data['event_id']}{data['match_id']}{data['match_date']}"
        hasher.update(hash.encode())

        return hasher.hexdigest()


class DataCleanup():
    def __init__(self, auto_run= False, year_cutoff= 2010):
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()
        self.YYYYMMDD_REGEX = re.compile(r'^\d{4}-\d{2}.\d{2}')
        self.YYYY_REGEX = re.compile(r'\d{4}')

        if auto_run:
            self.pipeline(year_cutoff)

    def __del__(self):
        self.conn.close()

    def pipeline(self, year_cutoff):
        self.append_year_to_match_date()
        self.delete_where_no_year()
        self.remove_before_year(year_cutoff)
        self.create_tournament_table()
        self.append_court_surface()

    def append_year_to_match_date(self):
        self.cursor.execute("SELECT EventID, MatchID, MatchDate FROM MensATPSingles")
        rows = self.cursor.fetchall()
        update_table_query = "UPDATE MensATPSingles SET MatchDate = ? WHERE MatchID = ?"

        # List to store new MatchDate with corresponding MatchID.
        # I tried doing the updating within the loop but the program took minutes to run. This is more efficient.
        data_to_update = []

        for row in rows:
            event_id = row[0]
            match_id = row[1]
            match_date = row[2]

            if self.YYYYMMDD_REGEX.match(match_date):
                continue

            match = self.YYYY_REGEX.search(event_id)
            if match:
                year = int(match.group())
                new_match_date = f"{year}-{match_date}"
                data_to_update.append((new_match_date, match_id))
            else:
                continue

        if data_to_update:
            self.cursor.executemany(update_table_query, data_to_update)
        self.conn.commit()

    def delete_where_no_year(self):
        self.cursor.execute("SELECT EventID, MatchDate FROM MensATPSingles")
        rows = self.cursor.fetchall()

        for row in rows:
            event_id = row[0]
            match_date = row[1]
            # Check if MatchDate already has the correct format.
            if self.YYYYMMDD_REGEX.match(match_date):
                continue

            match = self.YYYY_REGEX.search(event_id)

            if not match:
                self.cursor.execute("DELETE FROM MensATPSingles WHERE EventID = ?", (event_id,))
                continue

        self.conn.commit()

    def remove_before_year(self, year: int):
        self.cursor.execute("SELECT MatchID, MatchDate FROM MensATPSingles")
        rows = self.cursor.fetchall()

        for row in rows:
            match_id = row[0]
            match_date = row[1]
            if int(match_date[:4]) < year:  # First 4 digits is the year.
                self.cursor.execute("DELETE FROM MensATPSingles WHERE MatchID = ?", (match_id,))
        self.conn.commit()

    def create_tournament_table(self):
        self.cursor.execute("PRAGMA table_info(MensATPSingles)")
        columns = self.cursor.fetchall()
        # Returns TRUE if any column = 'EventName'
        event_name_column_exists = any(column[1] == 'EventName' for column in columns)
        if not event_name_column_exists:
            self.cursor.execute('''ALTER TABLE MensATPSingles
                                        ADD COLUMN EventName TEXT''')

        self.cursor.execute("SELECT EventID FROM MensATPSingles")
        rows = self.cursor.fetchall()

        # An empty set instead of list (to avoid duplicates) to store extracted event name
        event_names = set()
        event_name_REGEX = re.compile(r'ATP\s(.+?)\s\d{4}')
        for row in rows:
            event_id = row[0]
            match = event_name_REGEX.search(event_id)
            if match:
                event_names.add(match.group(1))
        print(event_names)
        for event_name in event_names:
            self.cursor.execute("UPDATE MensATPSingles SET EventName = ? WHERE EventID LIKE ?",
                                (event_name, f'%ATP {event_name}%'))
        self.conn.commit()

    def append_court_surface(self):
        self.cursor.execute("PRAGMA table_info(MensATPSingles)")
        columns = self.cursor.fetchall()
        court_surface_column_exists = any(column[1] == 'CourtSurface' for column in columns) # Returns True if any column = 'CourtSurface'.
        if not court_surface_column_exists:
            self.cursor.execute('''ALTER TABLE MensATPSingles
                                        ADD COLUMN CourtSurface TEXT''')
        self.conn.commit()

        df = pd.read_csv('event_courtsurfaces.csv', sep=';')
        for _, row in df.iterrows():

            event_name = row['EventName']
            court_surface = row['CourtSurface']
            self.cursor.execute('SELECT CourtSurface FROM MensATPSingles WHERE EventName = ?', (event_name,))
            existing_court_surface = self.cursor.fetchone()

            # If CourtSurface is empty or null, update it
            if not existing_court_surface or not existing_court_surface[0]:
                self.cursor.execute('UPDATE MensATPSingles SET CourtSurface = ? WHERE EventName = ?',
                                    (court_surface, event_name))
        self.conn.commit()


'''
PrepareDataframe:
Takes a dataset (format below) and endcodes it's contents for modelling.

Input: data.db
    TABLE "MensATPSingles" (
                EventID TEXT,
                MatchID TEXT PRIMARY KEY,
                MatchDate TEXT, 
                Player1 TEXT,
                Player1Country TEXT,
                Player2 TEXT, 
                Player2Country TEXT,
                Winner TEXT,
                Loser TEXT)

Output: model_df.csv, player_index.csv, court_surface_index.csv
'''


class PrepareDataframe:
    def __init__(self, auto_run= False):
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('SELECT * FROM MensATPSingles')
        results = self.cursor.fetchall()
        columns = [col[0] for col in self.cursor.description]
        self.df = pd.DataFrame(results, columns=columns)
        self.conn.close()

        if auto_run:
            self.prepare_dataframe()
        
    def prepare_dataframe(self):
        self.df = self.create_binary_target()
        self.df = self.create_player_index(self.df)
        self.df = self.calc_headtohead(self.df)
        self.create_court_surface_index()
        self.df = self.encode_df_court_surface(self.df)
        self.df = self.matchup_hash(self.df)

        self.export_dataframe(self.df)

    def create_binary_target(self):
        # Drop column not needed for the prediction algorithm.
        columns_drop = ['EventID', 'Player1Country', 'Player2Country', 'MatchDate', 'EventName']
        sub_df = self.df.drop(columns=columns_drop)

        sub_df['Target'] = 0
        # Iterate over each row in the DataFrame & assign target 1/0 based on which player won.
        # 1 = Player1 win
        # 0 = Player2 win
        for index, row in self.df.iterrows():
            if row['Winner'] == row['Player1']:
                sub_df.at[index, 'Target'] = 1
            elif row['Winner'] == row['Player2']:
                sub_df.at[index, 'Target'] = 0
        sub_df.drop(columns=['Winner', 'Loser'], inplace=True)

        return sub_df

    def create_player_index(self, df, filename= 'player_index_df.csv'):
        # Concatenate Player1 and Player2 into one list (contains duplicates).
        players = pd.concat([df['Player1'], df['Player2']], ignore_index=True)

        # Remove duplicates.
        unique_names = players.unique()

        # Create a dictionary mapping unique names to unique IDs starting from 1
        name_to_number = {name: i + 1 for i, name in enumerate(unique_names)}
        df['Player1'] = df['Player1'].map(name_to_number)
        df['Player2'] = df['Player2'].map(name_to_number)

        # Create a player index used for lookup starting from 1.
        player_index_df = pd.DataFrame({'Player': unique_names, 'Index': range(1, len(unique_names) + 1)})

        # Calculate total wins for each player to store in the player index.
        player_index_df = self.calc_total_wins(df, player_index_df)
        player_index_df.to_csv(filename, index= False)
        print(f"Player index exported to {filename}")

        merged_df = self.merge_total_wins(df, player_index_df)

        return merged_df
    
    def calc_total_wins(self, df, player_index_df):
        player_index_df['TotalWins'] = 0

        for index, row in player_index_df.iterrows():
            player_index = row['Index']
            wins_as_player1 = df.loc[(df['Player1'] == player_index) & (df['Target'] == 1), 'Target'].count()
            player_index_df.loc[index, 'TotalWins'] += wins_as_player1

        for index, row in player_index_df.iterrows():
            player_index = row['Index']
            wins_as_player2 = df.loc[(df['Player2'] == player_index) & (df['Target'] == 0), 'Target'].count()
            player_index_df.loc[index, 'TotalWins'] += wins_as_player2

        return player_index_df
    
    def merge_total_wins(self, df, player_index_df):
        merged_df = pd.merge(df, player_index_df, left_on='Player1', right_on='Index', how='left')
        merged_df.rename(columns={'TotalWins': 'TotalWins_Player1'}, inplace=True)

        merged_df = pd.merge(merged_df, player_index_df, left_on='Player2', right_on='Index', how='left',
                             suffixes=('_Player1', '_Player2'))
        merged_df.rename(columns={'TotalWins': 'TotalWins_Player2'}, inplace=True)
        merged_df.drop(columns=['Player_Player1', 'Index_Player1', 'Player_Player2', 'Index_Player2'], inplace=True)

        return merged_df
    
    def calc_headtohead(self, df):
        # Variable to measure total wins/losses in matchup between Player1 and Player2.
        df['HeadToHead'] = 0
        for index, row in df.iterrows():
            # Calculate instances of 'Player1' vs 'Player2' where 'Target' = 1.
            player1_wins = (df[(df['Player1'] == row['Player1']) & (df['Player2'] == row['Player2'])][
                                'Target'] == 1).sum()
            # Same as above but in reverse. (I know it's a bit confusing that df['Player1'] is row[PLayer2]).
            # I have another way of doing this further down which might be easier to follow.
            df.at[index, 'HeadToHead'] = player1_wins - ((df[(df['Player1'] == row['Player2']) & (
                    df['Player2'] == row['Player1'])]['Target'] == 1).sum())  # Calculate win-loss difference

        return df

    def create_court_surface_index(self, filename= 'court_surface_index_df.csv'):
        if os.path.exists(filename):
            return f"Court surface index already exists {filename}"
        
        court_surface_index_df = pd.DataFrame({'CourtSurface': ['Hard Court', 'Clay', 'Grass'], 'Index': [1, 2, 3]})
        court_surface_index_df.to_csv(filename, index=False)
        print(f"Dataframe exported to {filename}")

    def encode_df_court_surface(self, df):
        # Replace CourtSurface entries from dataset with their indexed values from above.
        # OBS this function also removes all entries where CurtSurface is missing.
        index = pd.read_csv('court_surface_index_df.csv')
        encoded_df = pd.merge(df, index, how='left', on='CourtSurface')
        encoded_df.drop(columns=['CourtSurface'], inplace=True)
        encoded_df.rename(columns={'Index': 'CourtSurface'}, inplace=True)
        encoded_df.dropna(subset=['CourtSurface'], inplace=True)

        return encoded_df

    def matchup_hash(self, df):
        # Hash Player1(index) and Player2(index). Winner first.
        # Reason for this is to even out the bias towards either Player1 or Player2 in the dataset->
        # where a player appears more in either column.
        df['WinnerLoserHash'] = 0
        for index, row in df.iterrows():
            hasher = hashlib.sha256()
            player1 = str(row['Player1'])
            player2 = str(row['Player2'])
            target = row['Target']
            if target == 1:
                player1_winner = [player1, player2]
                combined_players = "#".join(player1_winner)
                hasher.update(combined_players.encode('utf-8'))
                hash = hasher.hexdigest()
                # Hasher returns a hex value that's too long for the prediction model to handle, so it must be shortened.
                short_hash = hash[:12]
                # The prediction model also can't handle hex values, so it has to be converted to an integer.
                normalized_hash = int(short_hash, 16)
                df.at[index, 'WinnerLoserHash'] = normalized_hash

            elif target == 0:
                player2_winner = [player2, player1]
                combined_players = "#".join(player2_winner)
                hasher.update(combined_players.encode('utf-8'))
                hash = hasher.hexdigest()
                short_hash = hash[:12]
                normalized_hash = int(short_hash, 16)
                df.at[index, 'WinnerLoserHash'] = normalized_hash

        return df

    def export_dataframe(self, df, filename= 'model_df.csv'):
        if os.path.exists(filename):
            while True:
                user_response = input(f"The file {filename} already exists. Do you want to overwrite it? (y/n): ").lower().strip()

                if user_response in ['y', 'yes']:
                    df.to_csv(filename, index= False)
                    print(f"Dataframe exported to {filename}")
                    break
                elif user_response in ['n', 'no']:
                    new_filename = input("Enter new filename: ").strip() + '.csv'
                    
                    if new_filename:
                        df.to_csv(new_filename, index= False)
                        print(f"Dataframe exported to {new_filename}")
                        break
                    else:
                        print("Filename cannot be empty. Please try again.")
                else:
                    print("Invalid input. Please respond with 'y' or 'n'")
        else:
            df.to_csv(filename, index= False)
            print(f"Dataframe exported to {filename}")


def run(auto_run= True):
    TennisMatchScraper(auto_run)
    DataCleanup(auto_run)
    PrepareDataframe(auto_run)

if __name__ == "__main__":
    run()