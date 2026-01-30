import unittest
import pandas as pd
from bs4 import BeautifulSoup
from wikiscraper import WikiScraper

class TestWikiScraper(unittest.TestCase):
    def setUp(self):
        # uruchamia się przed kazdym testem i przygotowuje swiezy obiekt
        self.scraper = WikiScraper("Test Phrase")

    def test_get_url(self):
        # sprawdz, czy faza ze spacjami zmienia sie na oczekiwanu URL
        self.scraper.phrase = "Team Rocket"
        expected_udl = "https://bulbapedia.bulbagarden.net/wiki/Team_Rocket"
        self.assertEqual(self.scraper._get_url(), expected_udl)

    def test_get_summary_offline(self):
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