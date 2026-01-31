# WikiScraper & Language Analyzer 

A command-line tool for scraping data from a chosen Wiki-page and conducting statistical analysis based on word frequency. 

Developed as a final project for *Kurs Pythona 2025/26* at the University of Warsaw. 

## About the project 
WikiScraper is a Python application designed to:
1. **Fetch Summaries**: Retrieve the introductory paragraph of the chosen Wiki article
2. **Extract Tables**: Parse specific HTML tables into CSV files and generate value distribution statistics. 
3. **Count Words**: Build a word-frequencies base across the analyzed articles in a separate `json` file. The program 
supports recursive crawling as well. 
4. **Analyze Language**: Compare the vocabulary of scraped articles against general language corpora using frequency 
analysis

### **Author**: Hanna Kaliszuk

#### **Date**: January 2026

#### **License**: MIT (Code) / CC BY-NC-SA 2.5 (Data from Bulbapedia)


## Requirements & Installation 
The project requires Python 3.8+ and external libraries. 
1. **Clone the repository:**
```bash 
git clone <>
cd <folder-name>
```
2. **Install dependencies**:
```bash
pip install -r requirements.txt
```
*(Ensure `requirements.txt` contains: `requests`, `pandas`, `beautifulsoup4`, `wordfreq`, `matplotlib`, `seaborn`, `lxml`)*

## Usage
The program is executed via the command line using:
```bash 
python wiki_scraper.py <arguments>
```
Depending on the given arguments, the following operations will occur:
*Please note that `[--argument]` means that this argument is optional and each `"phrase"` is the user's input*

### Fetch Summary 
Retrieves the first paragraph of an article (stripping HTML tags).
```bash 
python wiki_scraper.py --summary "phrase"
```

### Extract Table 
Fetches the n-th table from an article, saves it to a CSV file and prints value counts
- `--number`: the number of the table (1-based)
- `--first-row-is-header`: determines whether the first row of the table should be treated as a headliner
```bash 
python wiki_scraper.py --table "phrase" --number n [--first-row-is-header]
```

### Count Words
Counts word occurrences in the given article and updates `word-counts.json` file
```bash
python wiki_scraper.py --count-words "phrase"
```

## Analyze Relative Word Frequency
Compares the relative frequency of words in scraped articles vs their frequency in standard language.
- `--mode`: 
`article` sorts words according to top frequent words from wiki 
`language` sorts words according to top frequent words in the language
- `--count`: number of words to be included 
- `--chart` (optional): path to save the output chart 
```bash 
python wiki_scraper.py --analyze-relative-word-frequency --mode "mode" [--chart "file/path.png"]
```

### Auto-Scraping (Crawler)
Recursively visits internal links starting from the given article
- `--depth`: how many levels deep to crawl 
*Must be an integer > 0.*
- `--wait`: how many seconds to wait between requests 
*Must be a float > 0. Warning: Setting this value too low might result in the server blocking your IP*
```bash 
python wiki_scraper.py --auto-count-words "phrase" --depth n --wait t
```

## Testing
The project includes a set of unit test and an integration test to ensure reliability. 

### Unit Tests
These tests verify individual methods without making network requests.
```bash 
python tests.py
```

### Integration Test
This test performs an end-to-end check using a local dummy HTML file to verify the scraper's logic safely.
```bash 
python integration_test.py
```

## Analysis Report
A detailed Jupiter Notebook report (`analysis.ipynb`) investigates the effectiveness of language detection method.
