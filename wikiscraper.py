# musimy mieć konstruktor wszystkomający - przyjmuje konfiguracje, a pobieranie danych jest osobna metoda
# obsluga trybu offline oraz online
# parsowanie html
import os
import sys

import argparse
import re
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
from collections import Counter


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
                print(f"File {self.local_file_path} does not exist")
                return False

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
                return "Error: could not fetch data."

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

    def get_table(self, table_number, first_row_is_header=None):
        """Pobiera n-tą tabelę ze strony i zwraca DataFrame oraz częstotliwości wartości

        Args:
            table_number: numer tabeli do pobrania (1-indexed)
            first_row_is_header: czy pierwszy wiersz to nagłówek kolumn
        """
        if not self.soup:
            if not self.fetch_data():
                return "Error: Could not fetch data.", None

        content_div = self.soup.find('div', class_='mw-parser-output')

        if not content_div:
            content_div = self.soup.find('div', id='mw-content-text')

        if not content_div:
            return "Could not find content on the page.", None

        tables = content_div.find_all('table')


        if table_number > len(tables):
            return f"Table number {table_number} does not exist on the page.", None

        selected_table = tables[table_number - 1]

        try:
            html_str = str(selected_table)

            header_arg = 0 if first_row_is_header else None
            index_col_arg = 0

            dfs = pd.read_html(StringIO(html_str), header=header_arg, index_col=index_col_arg, flavor='bs4')

            if not dfs:
                return "Pandas could not extract any data from the table."

            df = dfs[0]

            csv_filename = f"{self.phrase}.csv"

            # Zawsze zapisuj indeks (pierwsza kolumna = nagłówki wierszy)
            # Nagłówki kolumn zapisuj tylko jeśli first_row_is_header=True
            df.to_csv(csv_filename, index=True, header=first_row_is_header, encoding='utf-8')

            print(f"\nTable saved to {csv_filename}")

            # --- STATYSTYKI WARTOŚCI ---
            # stack() spłaszcza tabelę do jednej kolumny.
            # Ponieważ użyliśmy index_col=0, pierwsza kolumna jest w indeksie i NIE zostanie policzona (co jest poprawne).
            # Jeśli first_row_is_header=True, nagłówki są w df.columns i też NIE zostaną policzone.

            if df.empty:
                print("\nNo values to count frequencies")
                freq_series = pd.Series()
            else:
                freq_series = df.astype(str).stack().value_counts()

            return df, freq_series

        except Exception as e:
            import traceback
            error_msg = f"Error processing table: {e}\n{traceback.format_exc()}"
            return error_msg, None

    def count_words(self):
        json_filename = "word-counts.json"

        # sprawdzamy czy mamy dane. jak nie, to próbujemy je pobrać
        if not self.soup:
            if not self.fetch_data():
                return "Error: could not fetch data."

        # szukamy głównego kontenera z tekstem (w divie o klasie mw-parser-output)
        content_div = self.soup.find('div', class_='mw-parser-output')

        # jezeli nie ma klasy, szukaj po id
        if not content_div:
            content_div = self.soup.find('div', id='mw-content-text')

        if not content_div:
            return "Could not find content on the page."

        full_text = content_div.get_text(separator=' ', strip=True)
        # znajdz wszystkie slowa (litery + cyfry, bez interpunkcji)
        # regex \w+ lapie slowa, a .lower() normalizuje do malych liter
        words = re.findall(r'\w+', full_text.lower())

        # zlicz wystapienia w tekscie
        current_counts = Counter(words)
        print(f"Found {len(current_counts)} unique words.")

        # odczyt -> aktualizacja -> zapis do pliku JSON
        global_counts = {}

        if os.path.exists(json_filename):
            try:
                with open(json_filename, 'r', encoding='utf-8') as f:
                    global_counts = json.load(f)
            except json.JSONDecodeError:
                print("Could not decode JSON file. Starting fresh.")

        # dla kazdego slowa w aktualnych zliczeniach dodajemy liczbe jego wystapien do globalnych zliczen
        for word, count in current_counts.items():
            if word in global_counts:
                global_counts[word] += count
            else:
                global_counts[word] = count

        # zapisujemy zaktualizowane zliczenia do pliku JSON
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(global_counts, f, ensure_ascii=False, indent=4)
            print(f"Updated word counts saved to {json_filename}.")
            return f"Update successful. Total unique words: {len(global_counts)}."
        except Exception as e:
            return f"Error saving word counts: {e}"




class ScraperController:
    def __init__(self, args):
        self.args = args
        self.base_url = "https://bulbapedia.bulbagarden.net"

    def run(self):
        if self.args.summary:
            phrase = self.args.summary
            print(f"--- Fetching summary for {phrase} from {self.base_url} ---")

            scraper = WikiScraper(
                self.base_url,
                phrase,
                use_local_file=bool(self.args.file),
                local_file_path=self.args.file,
            )

            summary = scraper.get_summary()
            print(summary)
            print("-" * 60)

        elif self.args.table:
            phrase = self.args.table
            print(f"--- Fetching table for {phrase} from {self.base_url} ---")

            scraper = WikiScraper(
                self.base_url,
                phrase,
                use_local_file=bool(self.args.file),
                local_file_path=self.args.file,
            )

            table_num = self.args.number
            use_header = self.args.first_row_is_header

            result, stats = scraper.get_table(table_num, first_row_is_header=use_header)

            if isinstance(result, str):
                print(result) # bo byl blad
            else:
                print("\nValue Counts:")
                print(stats.to_frame("Count"))
            print("-" * 60)

        elif self.args.count_words:
            phrase = self.args.count_words
            print(f"--- Counting words for {phrase} from {self.base_url} ---")

            scraper = WikiScraper(
                self.base_url,
                phrase,
                use_local_file=bool(self.args.file),
                local_file_path=self.args.file,
            )

            result = scraper.count_words()
            print(result)
            print("-" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WikiScraper Tool for Bulbapedia")
    parser.add_argument("--summary", type=str, metavar='"phrase"', help="Fetch summary for the given phrase")
    parser.add_argument("--table", type=str, metavar='"phrase"', help="Fetch table for the given phrase")
    parser.add_argument("--number", type=int, default=1, help="Table number to fetch (needed with --table)")
    parser.add_argument("--first-row-is-header", action="store_true", help="Indicates if the first row of the table is a header (needed with --table)")
    parser.add_argument("--file", type=str, metavar="file path", help="Path to the local file to use instead of fetching from the internet")
    parser.add_argument("--count-words", type=str, metavar='"phrase"', help="Count words in the given article and update word-counts.json")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    controller = ScraperController(args)
    controller.run()