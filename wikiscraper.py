# musimy mieć konstruktor wszystkomający - przyjmuje konfiguracje, a pobieranie danych jest osobna metoda
# obsluga trybu offline oraz online
# parsowanie html
import os

import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO


class WikiScraper:
    def __init__(self, base_url, phrase, use_local_file=False, local_file_path=None, first_row_is_header=False):
        # konstruktor, który umożliwia przechowywanie swojego stanu.
        self.base_url = base_url
        self.phrase = phrase
        self.use_local_file = use_local_file
        self.local_file_path = local_file_path
        self.first_row_is_header = first_row_is_header
        self.soup = None  # bo na razie nie ma sparsowanego HTMLa

    def _get_url(self):
        # metoda pomocnicza do generowania URL z podanej frazy
        return f"{self.base_url}/wiki/{self.phrase.replace(' ', '_')}"

    def fetch_data(self):
        # główna metoda do pobierania danych. Decyduje czy HTML będzie pobierany z dysku czy z internetu. Zwraca true
        # jak sie uda i false jak nie
        html_content = ""

        if self.use_local_file:
            # jeżeli plik z dysku
            if not self.local_file_path or not os.path.exists(self.local_file_path):
                # jeżeli nie ma pliku lub nie ma istniejącej do niego ścieżki
                raise FileNotFoundError(f"File {self.local_file_path} does not exist")

            with open(self.local_file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

        else:
            # plik z internetu
            url = self._get_url()

            try:
                response = requests.get(url) # wyślij żądnanie do serwera

                if response.status_code == 404: # jak strona nie istnieje to powiedz o tym
                    print(f"Error 404: Page not found at {url}")
                    return False

                response.raise_for_status() # sprawdź inne błędy
                html_content = response.text # pobierz treść HTML

            except requests.RequestException as e:
                # błąd połączenia
                print(f"An error occurred while fetching data: {e}")
                return False

        self.soup = BeautifulSoup(html_content, "html.parser")
        return True

    def get_summary(self):
        # sprawdzamy czy mamy dane. jak nie, to próbujemy je pobrać
        if not self.soup:
            if not self.fetch_data():
                return None

        # szukamy głównego kontenera z tekstem (w divie o klasie mw-parser-output)
        content_div = self.soup.find('div', class_='mw-parser-output')

        # jezeli nie ma klasy, szukaj po id
        if not content_div:
            content_div = self.soup.find('div', id='mw-content-text')

        if not content_div:
            return "Could not find content on the page."

        # pobieramy wszystkie paragrafy <p>
        paragraphs = content_div.find_all('p')

        # szukamy pierwszego paragrafu, który ma tekst
        for p in paragraphs:
            text = p.get_text().strip()

            if text:
                return text

        return "No summary available."

    def get_table(self, table_number, first_row_is_header=False):
        if not self.soup:
            if not self.fetch_data():
                return None
        # szukamy głównego kontenera z tekstem (w divie o klasie mw-parser-output)
        content_div = self.soup.find('div', class_='mw-parser-output')

        # jezeli nie ma klasy, szukaj po id
        if not content_div:
            content_div = self.soup.find('div', id='mw-content-text')

        if not content_div:
            return "Could not find content on the page."

        tables = content_div.find_all('table')

        if table_number > len(tables):
            return f"Table number {table_number} does not exist on the page."

        selected_table = tables[table_number - 1]








if __name__ == "__main__":
    base_url = "https://bulbapedia.bulbagarden.net"
    scraper = WikiScraper(base_url, "Type")
    print(f"Fetching summary for {scraper.phrase} from {base_url}")
    summary = scraper.get_summary()
    table = scraper.get_table(table_number=2, first_row_is_header=True)

    print("#" * 30)
    print("SUMMARY:")
    print(summary)
    print("#" * 30)

    print("#" * 30)
    print("TABLE:")
    print(table)
    print("#" * 30)