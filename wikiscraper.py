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
try:
    from analyzer import WordAnalyzer
except ImportError:
    WordAnalyzer = None

# --- constants ---
BASE_URL = "https://bulbapedia.bulbagarden.net"
CONTENT_CLASS = "mw-parser-output"
CONTENT_ID = "mw-content-text"

class WikiScraper:
    def __init__(self, phrase, use_local_file=False, local_file_path=None, first_row_is_header=False):
        # konstruktor, który umożliwia przechowywanie swojego stanu.
        self.base_url = BASE_URL
        self.phrase = phrase
        self.use_local_file = use_local_file
        self.local_file_path = local_file_path
        self.first_row_is_header = first_row_is_header
        self.soup = None  # bo na razie nie ma sparsowanego HTMLa

    def _get_url(self):
        # metoda pomocnicza do generowania URL z podanej frazy
        return f"{self.base_url}/wiki/{self.phrase.replace(' ', '_')}"

    def _get_content_div(self):
        if not self.soup:
            return None

        content_div = self.soup.find("div", {"class": CONTENT_CLASS})

        if not content_div:
            content_div = self.soup.find("div", {"id": CONTENT_ID})

        return content_div

    def _load_from_file(self):
        if not self.local_file_path or not os.path.exists(self.local_file_path):
            raise FileNotFoundError(f"File {self.local_file_path} does not exist")

        with open(self.local_file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_from_web(self):
        url = self._get_url()
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _table_to_dataframe(self, table, first_row_is_header):
        html_str = str(table)

        header_arg = 0 if first_row_is_header else None
        index_col_arg = 0

        dfs = pd.read_html(StringIO(html_str), header=header_arg, index_col=index_col_arg, flavor='bs4')

        result = dfs[0] if dfs else None
        return result

    def _count_table_values(self, df):
        if df.empty:
            return pd.Series()
        return df.astype(str).stack().value_counts()

    def fetch_data(self):
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
        # sprawdzamy czy mamy dane. jak nie, to próbujemy je pobrać
        if not self.soup:
            if not self.fetch_data():
                return "Error: could not fetch data."

        content_div = self._get_content_div()
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
        """Pobiera n-tą tabelę ze strony i zwraca DataFrame oraz częstotliwości wartości

        Args:
            table_number: numer tabeli do pobrania (1-indexed)
            first_row_is_header: czy pierwszy wiersz to nagłówek kolumn
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

            # Zawsze zapisuj indeks (pierwsza kolumna = nagłówki wierszy)
            # Nagłówki kolumn zapisuj tylko jeśli first_row_is_header=True
            df.to_csv(csv_filename, index=True, header=first_row_is_header, encoding='utf-8')

            # --- STATYSTYKI WARTOŚCI ---
            # stack() spłaszcza tabelę do jednej kolumny.
            # Ponieważ użyliśmy index_col=0, pierwsza kolumna jest w indeksie i NIE zostanie policzona (co jest poprawne).
            # Jeśli first_row_is_header=True, nagłówki są w df.columns i też NIE zostaną policzone.

            freq_series = self._count_table_values(df)

            return df, freq_series

        except Exception as e:
            error_msg = f"Error processing table: {e}"
            return error_msg, None

    def count_words(self):
        json_filename = "word-counts.json"

        # sprawdzamy czy mamy dane. jak nie, to próbujemy je pobrać
        if not self.soup:
            if not self.fetch_data():
                return False

        content_div = self._get_content_div()
        if not content_div:
            return False

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
            return True
        except Exception as e:
            print(f"Error saving word counts: {e}")
            return False

    def get_internal_links(self):
        # pobiera liste fraz z linkow wewnetrznych
        links = []
        if not self.soup:
            return links

        content_div = self._get_content_div()
        if not content_div:
            return links

        # szukamy wszystking tagow <a>
        for a_tag in content_div.find_all('a', href=True):
            href = a_tag['href']

            if href.startswith("/wiki/"):
                phrase = href.replace("/wiki/", "").replace("_", " ")

                links.append(phrase)

        return links


class ScraperController:
    def __init__(self, args):
        self.args = args

    def run(self):
        if self.args.analyze_relative_word_frequency:
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

        if self.args.auto_count_words:
            start_phrase = self.args.auto_count_words
            max_depth = self.args.depth
            wait_time = self.args.wait

            print(f"--- Auto-Scraping starting from '{start_phrase}' ---")

            queue = deque([(start_phrase, 0)])
            visited = set([start_phrase])

            while queue:
                current_phrase, current_depth = queue.popleft()

                print(f"Currently processing phrase: {current_phrase}")

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

        if self.args.summary:
            phrase = self.args.summary
            print(f"--- Fetching summary for {phrase} from {BASE_URL} ---")

            scraper = WikiScraper(
                phrase,
                use_local_file=bool(self.args.file),
                local_file_path=self.args.file,
            )

            summary = scraper.get_summary()
            print(summary)
            print("-" * 60)

        elif self.args.table:
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

            if isinstance(result, str):
                print(result) # bo byl blad
            else:
                print("\nValue Counts:")
                print(stats.to_frame("Count"))
            print("-" * 60)

        elif self.args.count_words:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WikiScraper Tool for Bulbapedia")

    parser.add_argument("--summary", type=str, metavar='"phrase"', help="Fetch summary for the given phrase")
    parser.add_argument("--table", type=str, metavar='"phrase"', help="Fetch table for the given phrase")
    parser.add_argument("--count-words", type=str, metavar='"phrase"', help="Count words in the given article and update word-counts.json")
    parser.add_argument("--auto-count-words", type=str, metavar='"phrase"', help="Recursivelu count words starting from 'phrase'")
    parser.add_argument("--analyze-relative-word-frequency", action="store_true", help="Analyze frequencies")

    parser.add_argument("--number", type=int, default=1, help="Table number to fetch (needed with --table)")
    parser.add_argument("--first-row-is-header", action="store_true", help="Indicates if the first row of the table is a header (needed with --table)")
    parser.add_argument("--file", type=str, metavar="file path", help="Path to the local file to use instead of fetching from the internet")

    parser.add_argument("--depth", type=int, default=1, help="Depth for auto-scraping (default = 1)")
    parser.add_argument("--wait", type=float, default=1.0, help="Wait time between requests (seconds)")

    parser.add_argument("--mode", type=str, default="language", choices=["article", "language"], help="Sort mode for analysis")
    parser.add_argument("--count", type=int, default=10, help="Number of words to analyze")
    parser.add_argument("--chart", type=str, metavar="path.png", help="Path to save chart")


    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    controller = ScraperController(args)
    controller.run()