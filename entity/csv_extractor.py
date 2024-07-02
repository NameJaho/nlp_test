import pandas as pd
from entity.entity_extractor import EntityExtractor


class CSVExtractor:
    def __init__(self):
        self.entity_extractor = EntityExtractor()

    def process(self, input_file, output_file):
        df = pd.read_excel(input_file)
        df['len'] = df['搜索词'].apply(lambda x: True if len(str(x)) >= 6 else False)
        df['words_by_api'] = df[df['len']]['搜索词'].apply(self.entity_extractor.extract)
        df.fillna('', inplace=True)
        df['who_by_api'] = df['words_by_api'].apply(lambda x:x.get('intent_who') if x else [])
        df.to_csv(output_file)


if __name__ == '__main__':
    csv_extractor = CSVExtractor()
    input_file = '../input/240525-240623_jieba切词每日监测总表_QC.xlsx'
    output_file = '../output/240525-240623_jieba切词每日监测总表_QC_cut_0701_v3.csv'
    csv_extractor.process(input_file, output_file)
