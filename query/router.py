import sys
project_root ='F:\\inter\\nlp_test'
sys.path.append(project_root)         
from word_splitter.word_cutter import WordCutter
from entity.entity_extractor import EntityExtractor
from tools.timeparser.convert_time import convert_time
import pandas as pd
import os
from tools.utils import get_root_path
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
    
    @staticmethod
    def search_for_synonyms(word,position): ##query为关键字， position为对应的位置(prefix,suffix,both)
        # file_path='./dict/intent_dict.csv'
        current_dir = os.path.dirname(__file__)
        print(current_dir)
        input_file='dict\\intent_dict.csv'
        file_path = os.path.join(current_dir, input_file)
        df=pd.read_csv(file_path)
        word_lower = word.lower()
        position_lower = position.lower()
        matching_rows = df[(df['word'].str.lower() == word_lower) & (df['position'].str.lower() == position_lower)]
        # 如果找到匹配的行,提取同义词和近义词列
        if not matching_rows.empty:
            synonyms = matching_rows['synonyms'].tolist()
            related = matching_rows['related'].tolist()
            return synonyms,related
        else:
            return [],[]
        

if __name__ == "__main__":
    _text = "2024年美妆行业"

    router = Router()
    # n_words = router.count_words(text)
    # print(f'{n_words}')

    # print(convert_time(_text, test=True, fast=True))
    synonyms,related=router.search_for_synonyms('AI','prefix')
    print(synonyms,related)