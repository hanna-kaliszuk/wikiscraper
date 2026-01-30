import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from wordfreq import word_frequency, top_n_list

class WordAnalyzer:
    def __init__(self, json_path="word-counts.json", lang="en"):
        self.json_path = json_path
        self.lang = lang
        self.wiki_counts = self._load_json()

    def _load_json(self):
        if not os.path.exists(self.json_path):
            print(f"Warning: {self.json_path} not found. Starting with empty data.")
            return {}

        try:
            with open(self.json_path, 'r', encoding='utf-8') as json_file:
                return json.load(json_file)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return {}

    def analyze(self, mode, count):
        data = []

        if mode == 'article':
            # sortuje z jsona malejaco; x[1] = liczba wystapien
            sorted_wiki = sorted(self.wiki_counts.items(), key=lambda x: x[1], reverse=True)
            top_words = [item[0] for item in sorted_wiki[:count]]
        elif mode == 'language':
            # top n najczęstszych slow w angielskim
            top_words = top_n_list(self.lang, count)
        else:
            raise ValueError("Mode must be 'article' or 'language'")

        max_wiki_count = max(self.wiki_counts.values()) if self.wiki_counts else 1

        most_common_word = top_n_list(self.lang, 1)[0]
        max_lang_freq = word_frequency(most_common_word, self.lang)

        for word in top_words:
            wiki_raw = self.wiki_counts.get(word)
            lang_freq = word_frequency(word, self.lang)

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
        if df.empty:
            print("No data to plot.")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        x = range(len(df))
        width = 0.35

        ax.bar([i - width/2 for i in x], df['wiki_freq_norm'], width, label='Wiki Frequency (Normalized)')
        ax.bar([i + width/2 for i in x], df['lang_freq_norm'], width, label='Language Frequency (Normalized)')

        ax.set_ylabel('Relative Frequency')
        ax.set_title('Word Frequency Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(df['word'])
        ax.legend()

        plt.tight_layout()

        try:
            plt.savefig(output_path)
            print(f"Chart saved to {output_path}")
        except Exception as e:
            print(f"Error saving chart: {e}")
