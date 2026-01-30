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

    def test_get_internal_links(self):
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
        html_content = """
        <table>
            <tr><th>Col1</th><th>Col2</th></tr>
            <tr><td>A</td><td>10</td></tr>
            <tr><td>B</td><td>20</td></tr>
        </table>
        """

        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.find("table")

        df = self.scraper._table_to_dataframe(table, first_row_is_header=True)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2) # 2 wiersze danych

        self.assertEqual(df.iloc[0, 0], 10) # pierwszy wiersz pierwsza kolumna danych
        self.assertEqual(df.index[0], 'A') # indeks pierwszego wiesza

if __name__ == '__main__':
    unittest.main()