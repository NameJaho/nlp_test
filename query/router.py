from word_splitter.word_cutter import WordCutter
from entity.entity_extractor import EntityExtractor
from tools.timeparser.convert_time import convert_time


class Router:
    def __init__(self):
        self.word_cutter = WordCutter()
        self.entity_extractor = EntityExtractor()

    def cut_words(self, text):
        text = self.remove_when(text)
        text = self.remove_where(text)
        words = self.word_cutter.cut(text)
        return words

    @staticmethod
    def remove_when(text):
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


if __name__ == "__main__":
    _text = "2024年美妆行业"

    router = Router()
    # n_words = router.count_words(text)
    # print(f'{n_words}')

    print(convert_time(_text, test=True, fast=True))
