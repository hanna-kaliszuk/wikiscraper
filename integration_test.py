import sys
import os
from wiki_scraper import WikiScraper

def run_integration_test():
    print("--- RUNNING INTEGRATION TEST ---")

    # przygotowanie fake danych
    test_filename = "integration_test_doc.html"
    fake_html = """
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

    with open(test_filename, "w", encoding="utf-8") as f:
        f.write(fake_html)

    print(f"    Created test file: {test_filename}")

    try:
        scraper = WikiScraper(
            phrase = "Test Pokemon",
            use_local_file=True,
            local_file_path=test_filename
        )

        print("    WikiScraper running offline")

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

        print("--- SUCCESSFUL END OF THE INTEGRATION TEST ---")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        sys.exit(1)

    finally:
        if os.path.exists(test_filename):
            os.remove(test_filename)


if __name__ == "__main__":
    run_integration_test()