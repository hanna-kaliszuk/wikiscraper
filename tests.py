"""
UNIT TEST MODULE

This module contains unit tests for the WikiScraper class.

Verifies:
    - URL generation
    - content parsing
    - table extraction and conversion to DataFrame

Usage:
    Run via command line: python tests.py

Author:
    Hanna Kaliszuk, January 2026
"""

# --- standard library imports ---
import unittest

# -- third-party imports ---
import pandas as pd
from bs4 import BeautifulSoup

# --- local imports ---
from wiki_scraper import WikiScraper, table_to_dataframe


class TestWikiScraper(unittest.TestCase):
    def setUp(self):
        """
        Setting up the test environment.
        Initializes a WikiScraper instance before every test method.
        """
        self.scraper = WikiScraper("Test Phrase")

    def test_get_url(self):
        """Tests if the URL is generated correctly from the given phrase."""
        self.scraper.phrase = "Team Rocket"
        expected_url = "https://bulbapedia.bulbagarden.net/wiki/Team_Rocket"
        self.assertEqual(self.scraper._get_url(), expected_url)

    def test_get_summary_offline(self):
        """Tests if the summary is being extracted correctly using an offline HTML structure."""
        html_content = """
        <div class="mw-parser-output">
            <p></p>
            <p>
                <b>Team Rocket</b> is a villainous team.
            </p>
        </div>
        """

        expected_text = "Team Rocket is a villainous team."
        self.scraper.soup = BeautifulSoup(html_content, "html.parser")
        result = self.scraper.get_summary()

        self.assertEqual(result, expected_text)

    def test_get_internal_links(self):
        """Tests the extraction of internal Wiki links"""
        html_content = """
        <div class="mw-parser-output">
            <a href="/wiki/Pikachu">Link 1</a>
            <a href="https://google.com">Zewnętrzny</a>
            <a href="/wiki/File:Image.png">Plik</a>
            <a href="/wiki/Ash_Ketchum">Link 2</a>
        </div>
        """

        self.scraper.soup = BeautifulSoup(html_content, "html.parser")

        links = self.scraper.get_internal_links()
        expected_links = ["Pikachu", "Ash Ketchum", "File:Image.png"]

        for link in expected_links:
            self.assertIn(link, links)

        self.assertNotIn("https://google.com", links)

    def test_table_parsing(self):
        """Tests the convertion of HTML table to DataFrame."""
        html_content = """
        <table>
            <tr><th>Col1</th><th>Col2</th></tr>
            <tr><td>A</td><td>10</td></tr>
            <tr><td>B</td><td>20</td></tr>
        </table>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table")

        df = table_to_dataframe(table, first_row_is_header=True)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2) # should have 2 data rows

        self.assertEqual(df.iloc[0, 0], 10)
        self.assertEqual(df.index[0], 'A')


if __name__ == '__main__':
    unittest.main()