from bs4 import BeautifulSoup
from selenium import webdriver
import sqlite3
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from hashlib import sha256
import re
import pandas as pd


'''
A web scraper to scrape tennis match data from www.flashscore.com and store it in an SQLite database.
Currently it is only tuned for men's ATP singles.
There's a clickable button on each event result page to load more matches. 
I have not been able to get Selenium to click this.

TennisScraper:
First launches starting page with Selenium webdriver. 
From there it goes through the whole event list (limit this for testing) and clicks through the archive list for each
event to get to the match data.  
Getting Selenium to select the right DOMs was tricky and took a lot of trial and error.

DataStorage:
Collects the scraped data and stores it in a local database.

DataCleanup:
The scraped data contains a lot of old match data and all entries are missing year in MatchDate (it's in EventID).
This class of methods takes care of all that so that we can delete all old data we don't need for prediction.
I have also looked up the court surface for each tournament (manually) so this data also can be used for prediction.
'''


class TennisScraper:
    def __init__(self):
        self.driver = self.launch_browser()

    def launch_browser(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("webdriver.chrome.driver=chromedriver.exe")
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://www.flashscore.com/tennis/')

        return driver

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

    def get_link_list(self, event_archive_links: list[str]) -> list[str]:
        # List to store the links that will be scraped.
        scraper_link_list = []

        for link in event_archive_links[:2]:
            try:
                self.driver.get(link)
                WebDriverWait(self.driver, 10).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "#fsbody .archive__season a.archive__text--clickable[href*='atp-singles/']")))
                elements = self.driver.find_elements(By.CSS_SELECTOR,
                                                     "#fsbody .archive__season a.archive__text--clickable[href*='atp-singles/']")
                # Adjust number of iterations for how far back in time to scrape.
                for element in elements[:3]:
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

    # Does not work yet.
    def click_more_matches(self):
        try:
            more_matches = WebDriverWait(self.driver, 10).until(
                expected_conditions.element_to_be_clickable((By.CLASS_NAME, 'event__more')))
            self.driver.execute_script("arguments[0].click();", more_matches)
        except NoSuchElementException as element:
            print(f'No clickable element for {element}')

    def process_matches(self, all_source_code: list[str]):
        database = DataStorage()
        db_connect = database.database_connect()
        # The source code of each event is fed to the scraper and the extracted data is added to the database.
        for event in all_source_code:
            event_matches = self.scraper(event)
            if event_matches:
                database.append_data(db_connect, event_matches)

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


class DataCleanup:
    def __init__(self):
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()
        self.YYYYMMDD_REGEX = re.compile(r'^\d{4}-\d{2}.\d{2}')
        self.YYYY_REGEX = re.compile(r'\d{4}')

    def __del__(self):
        self.conn.close()

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


