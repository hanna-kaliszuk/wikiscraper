"""
ANALYZER MODULE

This module provides tools for analyzing word frequencies from scraped data from Bulbapedia (or compatible MediaWiki
sites. To change it please change BASE_URL constant) and compare them against general language usage.

Functionalities included:
    - Loading and parsing word count data from JSON files
    - Normalizing frequencies for accurate comparison
    - Comparing local vocabulary against global usage
    - Generating visual bar charts using Seaborn and Matplotlib

Usage:
    This module is intended to be imported and used by `wiki_scraper.py`

Author:
    Hanna Kaliszuk, January 2026
"""

# --- standard library imports ---
import json
import os

# -- third-party imports ---
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordfreq import word_frequency, top_n_list

DEFAULT_ENCODING = "utf-8"
WORD_COUNTS_FILE = "word-counts.json"


class WordAnalyzer:
    """
    A class to analyze and visualize word frequency data.

    Attributes:
        json_path (str): path to the JSON file with word counts
        lang (str): ISO code of the analyzed language
        wiki_counts (Dict[str, int]): loaded dictionary of word counts from the article
    """
    def __init__(self, json_path=WORD_COUNTS_FILE, lang="en"):
        self.json_path = json_path
        self.lang = lang
        self.wiki_counts = self._load_json()

    def _load_json(self):
        """
        Loads word counts from the specified JSON file

        Returns:
            Dict[str, int]: a dictionary mapping words to their frequency count.
            Returns an empty one in case of providing a missing or invalid file.
        """
        if not os.path.exists(self.json_path):
            print(f"Warning: {self.json_path} not found. Starting with empty data.")
            return {}

        try:
            with open(self.json_path, 'r', encoding=DEFAULT_ENCODING) as json_file:
                return json.load(json_file)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return {}

    def analyze(self, mode, count):
        """
        Analyzes word frequencies based on the selected mode.

        It normalizes frequencies from the article (local) and the language (global) to make them comparable
        (relative to the most frequent word in each dataset).

        Arguments:
            mode (str): sorting mode:
                        - 'article' = top words from the scraped article
                        - 'language' = top words from the general language dicitionary
            count (int): how many top words will be taken into consideration

        Returns:
            pd.DataFrame: a DataFrame containing raw and normalized frequencies

        Raises:
            ValueError: if the provided mode is invalid
        """

        if mode == 'article':
            # sort by wiki frequency descending
            sorted_wiki = sorted(self.wiki_counts.items(), key=lambda x: x[1], reverse=True)
            top_words = [item[0] for item in sorted_wiki[:count]]

        elif mode == 'language':
            # get top n words from the general language
            top_words = top_n_list(self.lang, count)
        else:
            raise ValueError("Mode must be 'article' or 'language'")

        # normalization factors
        max_wiki_count = max(self.wiki_counts.values()) if self.wiki_counts else 1
        most_common_word = top_n_list(self.lang, 1)[0]
        max_lang_freq = word_frequency(most_common_word, self.lang)

        data = []

        for word in top_words:
            # get raw values
            wiki_raw = self.wiki_counts.get(word, 0)
            lang_freq = word_frequency(word, self.lang)

            # calculate normalized values
            wiki_norm = wiki_raw / max_wiki_count
            lang_norm = lang_freq / max_lang_freq if max_lang_freq else 0

            data.append({
                "word": word,
                "wiki_freq_norm": wiki_norm,
                "lang_freq_norm": lang_norm,
                "wiki_raw": wiki_raw,
                "lang_freq": lang_freq
            })

        df = pd.DataFrame(data)
        return df

    def generate_chart(self, df, output_path):
        """
        Generates and saves a bar chart comparing relative frequencies.

        Arguments:
            df (pd.DataFrame): the data to plot
            output_path (str): path to output file where the chart will be saved
        """

        if df.empty:
            print("No data to plot.")
            return

        # make data suitable for the plot
        df_melted = df.melt(
            id_vars="word",
            value_vars=["wiki_freq_norm", "lang_freq_norm"],
            var_name="source",
            value_name="frequency"
        )

        # change labels for the legend
        df_melted["source"] = df_melted["source"].replace({
            "wiki_freq_norm": "Wiki Article",
            "lang_freq_norm": "General Language"
        })

        sns.set_theme(style="white", font_scale=1.2)
        plt.figure(figsize=(12, 6))

        # create bars
        ax = sns.barplot(
            data=df_melted,
            x="word",
            y="frequency",
            hue="source",
            palette="cubehelix",
            edgecolor="black"
        )


        plt.title(
            'Relative Word Frequency Comparison',
            fontsize=22,
            fontweight='bold'
        )
        plt.xlabel("")
        plt.ylabel("")
        plt.xticks(rotation=45)
        plt.legend(title=None, loc='upper right')

        # remove plot borders and hide Y-axis as the values will be displayed on bars
        sns.despine(left=True, right=True, top=True, bottom=False)
        ax.yaxis.set_visible(False)

        # Y-axis limit adjustment so that the label fits on the highest bar
        max_val = df_melted["frequency"].max()
        if max_val > 0:
            ax.set_ylim(0, max_val * 1.2)

        for p in ax.patches:
            height = p.get_height()

            if height <= 0.001:
                continue

            # add data labels to bars formating them as percentages
            ax.annotate(
                f"{height:.1%}",
                (p.get_x() + p.get_width() / 2, height),  # so that the label is exactly in the middle of the bar
                ha="center",
                va="bottom",
                fontsize=13,
                fontweight="bold",
                color="black",
                xytext=(0, 5),
                textcoords="offset points"
            )

        plt.tight_layout()

        try:
            print(f"Chart successfully saved to: {output_path}")
        except Exception as e:
            print(f"Error saving chart: {e}")