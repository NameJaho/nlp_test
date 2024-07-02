import pandas as pd

INPUT_FILE = 'input/test_data/0701_2000_entity_diff.csv'
OUTPUT_FILE = 'input/res_data/0701_2000_diff_entity.csv'
SCHEMA = ['公司', '行业', '产品', '技术', '地区', '人物', '疾病', '日期']


class DiffGen:
    @staticmethod
    def get_tag_from_result(tag, res):
        tem = res.get(tag, {})
        return [i for i in tem]

    @staticmethod
    def diff_dict_format(diff_dict):
        arr = []
        for tag in SCHEMA:
            arr = arr + [diff_dict[tag]['old_new'], diff_dict[tag]['new_old'], diff_dict[tag]['old&new']]
        return arr

    def compare_diff(self, old_col, new_col, row):
        compare_tag_dict = {}

        old_res, new_res = eval(row[old_col]), eval(row[new_col])
        if 'res' in old_res:
            old_res = old_res['res']

        for tag in SCHEMA:
            compare_tag_dict[tag] = {'old_new': [], 'new_old': [], 'old&new': []}
            old_tags = self.get_tag_from_result(tag, old_res)
            new_tags = self.get_tag_from_result(tag, new_res)

            compare_tag_dict[tag]['old_new'] = list(set(old_tags) - set(new_tags))
            compare_tag_dict[tag]['new_old'] = list(set(new_tags) - set(old_tags))
            compare_tag_dict[tag]['old&new'] = list(set(old_tags) & set(new_tags))

        diff_arr = self.diff_dict_format(compare_tag_dict)
        return diff_arr

    def process(self):
        # 原始文件路径
        df = pd.read_csv(INPUT_FILE, sep='\t')
        df = df[df['len'] == True]
        df['index'] = [i for i in range(len(df))]

        old_col = '主体识别'
        new_col = 'words_by_api'
        diff_df = []
        diff_columns = ['index']
        for tag in SCHEMA:
            diff_columns = diff_columns + [tag + '_old_new', tag + '_new_old', tag + '_old&new']

        for _id, row in df.iterrows():
            diff_arr = self.compare_diff(old_col=old_col, new_col=new_col, row=row)
            index = row['index']
            diff_df.append([index] + diff_arr)

        diff_df = pd.DataFrame(diff_df, columns=diff_columns)

        # 输出对比结果
        res_df = pd.merge(df, diff_df, on='index')
        res_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
