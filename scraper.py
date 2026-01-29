# musimy mieć konstruktor wszystkomający - przyjmuje konfiguracje, a pobieranie danych jest osobna metoda
# obsluga trybu offline oraz online
# parsowanie html

import requests
from bs4 import BeautifulSoup
import os

class Scraper:
    def __init__(self, base_url, phrase, use_local_file=False, local_file_path=None):
        # konstruktor, który umożliwia przechowywanie swojego stanu.
        self.base_url = base_url
        self.phrase = phrase
        self.use_local_file = use_local_file
        self.local_file_path = local_file_path
        self.soup = None # bo na razie nie ma sparsowanego HTMLa

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

if __name__ == "__main__":
    print("########test online########")
    wiki_url = "https://bulbapedia.bulbagarden.net"
    scraper = Scraper(wiki_url, "Team Rocket")
    success = scraper.fetch_data()
    if success:
        print("Data fetched successfully from the internet.")
    else:
        print("Failed to fetch data from the internet.")

    print("########test 404########")
    fake_scraper = Scraper(wiki_url, "ThisPageDoesNotExist12345")
    success = fake_scraper.fetch_data()