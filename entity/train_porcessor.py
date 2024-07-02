from entity.diff_gen import DiffGen
from entity.csv_extractor import CSVExtractor

csv_extractor = CSVExtractor()
diff_gen = DiffGen()

_input_file = './input/qc_query_train_0525-0623.csv'
_output_file = './output/qc_query_train_extract_0525-0623.csv'
_diff_output_file = 'output/qc_query_train_diff_0525-0623.csv'

csv_extractor.process(_input_file, _output_file)
print('csv_extractor done')
diff_gen.process(_output_file, _diff_output_file)
print('diff_gen done')
