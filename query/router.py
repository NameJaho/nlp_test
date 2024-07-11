from word_splitter.word_cutter import WordCutter
from entity.entity_extractor import EntityExtractor
from tools.timeparser.convert_time import convert_time
from tools.utils import get_root_path
import pandas as pd
import os

INTENT_DICT_FILE_NAME = 'intent_dict.csv'


class Router:
    def __init__(self):
        self.word_cutter = WordCutter()
        self.entity_extractor = EntityExtractor()
        self.root_path = get_root_path()
        self.intent_dict_path = os.path.join(self.root_path, 'query/dict', INTENT_DICT_FILE_NAME)

    def cut_words(self, text):
        text = self.remove_when(text)
        text = self.remove_where(text)
        words = self.word_cutter.cut(text)
        return words

    @staticmethod
    def remove_when(text):
        remove_items = convert_time(text, test=True, fast=True)
        if remove_items:
            text_to_remove = str(remove_items[0]['text'])
            text = text.replace(text_to_remove, '')
        return text

    @staticmethod
    def remove_where(text):
        return text

    def process(self, text):
        # Step 1: count words
        words = self.cut_words(text)
        word_cnt = len(words)

        # Step 2: match intent dictionary

        return text

    def search_for_synonyms(self, word, position):
        # query为关键字， position为对应的位置(prefix,suffix,both)
        df = pd.read_csv(self.intent_dict_path)

        word_lower = word.lower()
        matching_rows = df[(df['word'].str.lower() == word_lower) & (df['position'] == position)]

        synonyms, related = [], []

        # 如果找到匹配的行,提取同义词和近义词列
        if not matching_rows.empty:
            synonyms = matching_rows['synonyms'].tolist()
            related = matching_rows['related'].tolist()

        return synonyms, related


if __name__ == "__main__":
    _text = "2024年一季度美妆行业"

    router = Router()
    # n_words = router.count_words(text)
    # print(f'{n_words}')

    print(convert_time(_text, test=True, fast=True))
    print(router.remove_when(_text))
    # synonyms, related = router.search_for_synonyms('AI', 'prefix')
    # print(synonyms, related)
