"""
INTEGRATION TEST MODULE

This module performs an end-to-end integration test fot the WikiScraper class. It verifies the entire scraping logic
using a dummy HTML file.

Usage:
    Run via command line: python integration_test.py

Author:
    Hanna Kaliszuk, January 2026
"""

# --- standard library imports ---
import sys
import os

# --- local imports ---
from wiki_scraper import WikiScraper

# --- constants ---
TEST_FILENAME = "integration_test_doc.html"
DEFAULT_ENCODING = "utf-8"
FAKE_HTML = """
<html>
        <body>
            <div class="mw-parser-output">
                <table class="infobox">
                    <tr><td>Infobox (ignore)</td></tr>
                </table>
                <p>
                    <b>Test Pokemon</b> is a digital creature used for integration testing. It lives in the Python script.
                </p>
                <table class="wikitable">
                    <tr><th>Stat</th><th>Value</th></tr>
                    <tr><td>HP</td><td>100</td></tr>
                </table>
            </div>
        </body>
    </html>
"""
def run_integration_test():
    """Executes the integration test."""
    print("--- RUNNING INTEGRATION TEST ---")

    # create dummy data
    with open(TEST_FILENAME, 'w', encoding=DEFAULT_ENCODING) as f:
        f.write(FAKE_HTML)

    print(f"    [OK] Created temporary test file: {TEST_FILENAME}")

    try:
        scraper = WikiScraper(
            phrase = "Test Pokemon",
            use_local_file=True,
            local_file_path=TEST_FILENAME
        )

        print("    [OK] WikiScraper running offline")

        summary = scraper.get_summary()
        expected_summary = "Test Pokemon is a digital creature used for integration testing. It lives in the Python script."

        if not summary.startswith(expected_summary):
            print(f"ERROR: summary does not match the expected one")
            print(f"    Expected: {expected_summary}")
            print(f"    Actual: {summary}")
            print("--- ENDING THE INTEGRATION TEST WITH ERROR ---")
            sys.exit(1)

        df, stats = scraper.get_table(2, first_row_is_header=True)
        if df is None or df.empty:
            print(f"ERROR: extracted table does not match the expected one ({expected_summary})")
            print("--- ENDING THE INTEGRATION TEST WITH ERROR ---")
            sys.exit(1)
        print("    [OK] WikiScraper extracted the right table")
        print("--- SUCCESSFUL END OF THE INTEGRATION TEST ---")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        sys.exit(1)

    # cleanup
    finally:
        if os.path.exists(TEST_FILENAME):
            os.remove(TEST_FILENAME)
            print("    [OK] Removed temporary test file")


if __name__ == "__main__":
    run_integration_test()