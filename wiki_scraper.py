"""
WIKI SCRAPER MODULE

This module provides tools for scraping and analyzing data from Bulbapedia (or compatible MediaWiki sites. To change it
please change BASE_URL constant)

Functionalities included:
    - Fetching article summaries
    - Extracting and analyzing tables
    - Counting word frequencies
    - Recursive crawling of internal links
    - Analyzing relative word frequencies compared to general language usage

Usage:
    Run the script with appropriate command-line arguments described in `README.md`

Author:
    Hanna Kaliszuk, January 2026
"""


# --- standard library imports ---
import os
import sys
import argparse
import re
import json
import time
from collections import Counter, deque
from io import StringIO

# -- third-party imports ---
import requests
import pandas as pd
from bs4 import BeautifulSoup

# --- local imports ---
from analyzer import WordAnalyzer

# --- constants ---
BASE_URL = "https://bulbapedia.bulbagarden.net"
CONTENT_CLASS = "mw-parser-output"
CONTENT_ID = "mw-content-text"
DEFAULT_ENCODING = "utf-8"
WORD_COUNTS_FILE = "word-counts.json"


class WikiScraper:
    """
    A class to scrape data from a Wiki page.

    Atributes:
        base_url (str): the base Wiki URL
        phrase (str): the search phrase (or article title)
        use_local_file (bool): flag determining if data should be loaded from an offline file
        local_file_path (str): path to the local HTML file (if use_local_file is True)
        first_row_is_header (bool): flag indicating if the table's first row is a header
        soup (BeautifulSoup): the parsed HTML content (initialized after fetching data)
    """

    def __init__(self, phrase, use_local_file=False, local_file_path=None, first_row_is_header=False):
        self.base_url = BASE_URL
        self.phrase = phrase
        self.use_local_file = use_local_file
        self.local_file_path = local_file_path
        self.first_row_is_header = first_row_is_header
        self.soup = None

    def _get_url(self):
        """Constructs the full URL out of the given phrase."""
        return f"{self.base_url}/wiki/{self.phrase.replace(' ', '_')}"

    def _get_content_div(self):
        """Retrieves the main content div from the parsed HTML"""
        if not self.soup:
            return None

        # first try finding by class
        content_div = self.soup.find("div", {"class": CONTENT_CLASS})

        # if class is missing, try with ID
        if not content_div:
            content_div = self.soup.find("div", {"id": CONTENT_ID})

        return content_div

    def _load_from_file(self):
        """
        Loads HTML content from a local file.

        Returns content of the file or raises FileNotFound in case the specified local file does not exist.
        """
        if not self.local_file_path or not os.path.exists(self.local_file_path):
            raise FileNotFoundError(f"File {self.local_file_path} does not exist")

        with open(self.local_file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_from_web(self):
        """
        Fetches HTML content from the web.

        Returns content of the page or raises requests.exceptions.HTTPError if the HTTP request fails
        """
        url = self._get_url()
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _table_to_dataframe(self, table, first_row_is_header):
        """
        Converts an BeautifulSoup <table> Tag object into a pandas DataFrame.

        Arguments:
            - table (tag): the BeautifulSoup Tag object representing the table
            - first_row_is_header (bool): a flag determining whether the first row should be treated as headers.

        Returns:
            The resulting DataFrame or None if parsing failed.
        """
        html_str = str(table)

        header_arg = 0 if first_row_is_header else None
        index_col_arg = 0

        dfs = pd.read_html(StringIO(html_str), header=header_arg, index_col=index_col_arg, flavor='bs4')

        result = dfs[0] if dfs else None
        return result

    def _count_table_values(self, df):
        """
        Counts the occurrences of unique values in the DataFrame

        Arguments:
            - df (pd.DataFrame): the DataFrame to be analyzed

        Returns:
            pd.Series: a series containing counts of unique values
        """
        if df.empty:
            return pd.Series()
        return df.astype(str).stack().value_counts()

    def fetch_data(self):
        """
        Fetches teh HTML data and parses it.

        Returns:
            bool: True if data was successfully fetched and parsed, False otherwise
        """
        try:
            if self.use_local_file:
                html_content = self._load_from_file()
            else:
                html_content = self._load_from_web()

            self.soup = BeautifulSoup(html_content, "html.parser")
            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Error 404: The page for '{self.phrase}' was not found.")
            else:
                print(f"HTTP Error: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def get_summary(self):
        """
        Extract the summary of the article (meaning the first reasonable paragraph)

        Returns:
            str: the text of the summary or an error message
        """

        if not self.soup:
            if not self.fetch_data():
                return "Error: could not fetch data."

        content_div = self._get_content_div()
        if not content_div:
            return "Could not find content on the page."

        paragraphs = content_div.find_all('p')

        # search for the first paragraph that contains text
        for p in paragraphs:
            text = p.get_text().strip()

            if text:
                return text

        return "No summary available."

    def get_article_text(self):
        """
        Extracts the full text of the article stripped of HTML tags.

        Returns:
            str: the full text content
        """

        if not self.soup:
            if not self.fetch_data():
                return ""

        content_div = self._get_content_div()

        if not content_div:
            return ""

        return content_div.get_text(separator=' ', strip=True)

    def get_table(self, table_number, first_row_is_header=False):
        """
        Extracts the n-th table from the article.

        Arguments:
            table_number (int): the index of the table to extract (1-based)
            first_row_is_header (bool, optional): whether the first row should be treated as a header

        Returns:
            A tuple containing: the DataFrame (or an error message) & a series with value counts (or None)
        """

        if not self.soup:
            if not self.fetch_data():
                return "Error: Could not fetch data.", None

        content_div = self._get_content_div()
        if not content_div:
            return "Could not find content on the page.", None

        tables = content_div.find_all('table')

        if table_number > len(tables) or table_number < 1:
            return f"Table number {table_number} does not exist on the page.", None

        selected_table = tables[table_number - 1]

        try:
            df = self._table_to_dataframe(selected_table, first_row_is_header)

            if df is None:
                return "Could not extract table", None

            csv_filename = f"{self.phrase}.csv"
            df.to_csv(csv_filename, index=True, header=first_row_is_header, encoding='utf-8')

            freq_series = self._count_table_values(df)
            return df, freq_series

        except Exception as e:
            error_msg = f"Error processing table: {e}"
            return error_msg, None

    def count_words(self):
        """
        Counts word occurrences in the article and updates the JSON file.

        Returns:
            bool: True if success, False otherwise
        """

        if not self.soup:
            if not self.fetch_data():
                return False

        content_div = self._get_content_div()
        if not content_div:
            return False

        full_text = content_div.get_text(separator=' ', strip=True)
        # find all words (alphanumeric sequences), ignoring punctuation and replacing all upper case letters with lower
        # case ones
        words = re.findall(r'\w+', full_text.lower())

        current_counts = Counter(words)
        print(f"Found {len(current_counts)} unique words.")

        global_counts = {}

        if os.path.exists(WORD_COUNTS_FILE):
            try:
                with open(WORD_COUNTS_FILE, 'r', encoding=DEFAULT_ENCODING) as f:
                    global_counts = json.load(f)
            except json.JSONDecodeError:
                print("Could not decode JSON file. Starting fresh.")

        # update global word counts
        for word, count in current_counts.items():
            if word in global_counts:
                global_counts[word] += count
            else:
                global_counts[word] = count

        try:
            with open(WORD_COUNTS_FILE, 'w', encoding=DEFAULT_ENCODING) as f:
                json.dump(global_counts, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error saving word counts: {e}")
            return False

    def get_internal_links(self):
        """
        Extracts internal longs from the page.
        * Only the ones that point to other Wiki articles

        Returns:
            List[str]: a list of phrases found in the internal links
        """

        links = []
        if not self.soup:
            return links

        content_div = self._get_content_div()
        if not content_div:
            return links

        # search for all <a> tags
        for a_tag in content_div.find_all('a', href=True):
            href = a_tag['href']

            # thats how a standard Bulbapedia internal link looks like
            if href.startswith("/wiki/"):
                phrase = href.replace("/wiki/", "").replace("_", " ")
                links.append(phrase)

        return links


class ScraperController:
    """
    Controller class to manage the execution based on the command-line arguments.

    Attributes:
        args (argparse.Namespace): command line arguments (parsed)
    """
    def __init__(self, args):
        self.args = args

    def _handle_summary(self):
        """Handles the summary extraction"""
        phrase = self.args.summary
        print(f"--- Fetching summary for {phrase} from {BASE_URL} ---")

        scraper = WikiScraper(
            phrase,
            use_local_file=bool(self.args.file),
            local_file_path=self.args.file,
        )

        print(scraper.get_summary())
        print("-" * 60)

    def _handle_table(self):
        """Handles fetching and processing a table from an article"""
        phrase = self.args.table
        print(f"--- Fetching table for {phrase} from {BASE_URL} ---")

        scraper = WikiScraper(
            phrase,
            use_local_file=bool(self.args.file),
            local_file_path=self.args.file,
        )

        table_num = self.args.number
        use_header = self.args.first_row_is_header

        result, stats = scraper.get_table(table_num, first_row_is_header=use_header)

        if isinstance(result, str):  # there was an error
            print(result)
        else:
            print("\nExtracted Table Data:")
            print(result)
            print("\nValue Counts:")
            print(stats.to_frame("Count"))
        print("-" * 60)

    def _handle_count(self):
        """Handles counting words for a single article"""
        phrase = self.args.count_words
        print(f"--- Counting words for {phrase} from {BASE_URL} ---")

        scraper = WikiScraper(
            phrase,
            use_local_file=bool(self.args.file),
            local_file_path=self.args.file,
        )

        result = scraper.count_words()
        print(result)
        print("-" * 60)

    def _handle_analysis(self):
        """Handles the relative word frequency mode"""
        if WordAnalyzer is None:
            print("Error: Could not import 'analyzer' module. Make sure it is available.")
            return

        print(f"--- Analyzing Word Frequency (Mode: {self.args.mode}) ---")
        analyzer = WordAnalyzer()

        df = analyzer.analyze(mode=self.args.mode, count=self.args.count)
        print(df.to_string(index=False))

        if self.args.chart:
            analyzer.generate_chart(df, self.args.chart)

        print("-" * 60)
        return

    def _handle_auto_count(self):
        """Handles the recursive word count"""
        start_phrase = self.args.auto_count_words
        max_depth = self.args.depth
        wait_time = self.args.wait

        print(f"--- Auto-Scraping starting from '{start_phrase}' ---")

        queue = deque([(start_phrase, 0)])
        visited = {start_phrase}

        while queue:
            current_phrase, current_depth = queue.popleft()
            print(f"Currently processing phrase: {current_phrase} (at depth: {current_depth}) ---")

            scraper = WikiScraper(current_phrase)
            success = scraper.count_words()

            if success and current_depth < max_depth:
                links = scraper.get_internal_links()
                added_count = 0

                for link in links:
                    if link not in visited:
                        visited.add(link)
                        queue.append((link, current_depth + 1))
                        added_count += 1

                print(f"    -> Found {len(links)} links, added {added_count} new to the queue")

            if queue:
                print(f"    -> Waiting {wait_time} seconds...")
                time.sleep(wait_time)

            print("-" * 60)

        print("Auto scrapping finished")
        return

    def run(self):
        """Executes the appropriate action based on the provided arguments"""

        if self.args.summary:
            self._handle_summary()

        elif self.args.table:
            self._handle_table()

        elif self.args.count_words:
            self._handle_count()

        elif self.args.analyze_relative_word_frequency:
            self._handle_analysis()

        elif self.args.auto_count_words:
            self._handle_auto_count()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WikiScraper Tool for Bulbapedia")

    # action arguments
    parser.add_argument("--summary", type=str, metavar='"phrase"', help="Fetch summary for the given phrase")
    parser.add_argument("--table", type=str, metavar='"phrase"', help="Fetch table for the given phrase")
    parser.add_argument("--count-words", type=str, metavar='"phrase"', help="Count words in the given article and update word-counts.json")
    parser.add_argument("--auto-count-words", type=str, metavar='"phrase"', help="Recursivelu count words starting from 'phrase'")
    parser.add_argument("--analyze-relative-word-frequency", action="store_true", help="Analyze frequencies")
    # table options
    parser.add_argument("--number", type=int, default=1, help="Table number to fetch (needed with --table)")
    parser.add_argument("--first-row-is-header", action="store_true", help="Indicates if the first row of the table is a header (needed with --table)")
    # local file options
    parser.add_argument("--file", type=str, metavar="file path", help="Path to the local file to use instead of fetching from the internet")
    # auto scraping options
    parser.add_argument("--depth", type=int, default=1, help="Depth for auto-scraping (default = 1)")
    parser.add_argument("--wait", type=float, default=1.0, help="Wait time between requests (seconds)")
    # analysis options
    parser.add_argument("--mode", type=str, default="language", choices=["article", "language"], help="Sort mode for analysis")
    parser.add_argument("--count", type=int, default=10, help="Number of words to analyze")
    parser.add_argument("--chart", type=str, metavar="path.png", help="Path to save chart")

    args = parser.parse_args()

    # ensure at least one action argument is provided
    if not any([args.summary, args.table, args.count_words, args.auto_count_words, args.analyze_relative_word_frequency]):
        parser.print_help()
        sys.exit(1)

    controller = ScraperController(args)
    controller.run()