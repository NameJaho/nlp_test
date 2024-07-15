import sys
project_root ="F:\\inter\\nlp_test"
sys.path.append(project_root)
import gensim
import pandas as pd
from tools import utils
import os
import ast
from gensim.models import KeyedVectors
from word_splitter.word_cutter import WordCutter
from tools.utils import get_root_path

class synonyms:
    def __init__(self):
        self.word_cutter = WordCutter()

    @staticmethod
    def extract_from_string(s):
        if pd.isna(s):
            return None
        try:
            # 将字符串转换为列表
            actual_list = ast.literal_eval(s)
            # 判断列表中的元素是否都是字符串类型
            if all(isinstance(item, str) for item in actual_list):
            # 返回列表中的所有元素
                len(actual_list)
                return actual_list
            else:
                return None
        except (ValueError, SyntaxError):
            return None

    @staticmethod
    def find_similar_words_with_filtering(model, test_words,flag):
        word_cutter = WordCutter()
        filtered_res = []
        try:
            if flag:
                res = model.wv.most_similar(test_words, topn=20)
            else:
                res=model.most_similar(test_words, topn=20)
            for i in range(len(res)):
                if test_words not in word_cutter.cut(res[i][0]):
                    filtered_res.append(res[i][0])
        except KeyError:
            filtered_res = []
        return filtered_res

    def handle_different_models(self,input_file,output_file):
        #得到三个模型的输出
        model1_name = 'word2vec_baike'
        model2_name = 'word2vec_wx'
        model3_name = 'word2vec_tencent'
        root_path = utils.get_root_path()
        path1 = os.path.join(root_path, 'models/vector', model1_name)
        path2 = os.path.join(root_path, 'models/vector', model2_name)
        path3 = os.path.join(root_path, 'models/vector','tencent-ailab-embedding-zh-d100-v0.2.0-s.bin')
        model1 = gensim.models.Word2Vec.load(path1)
        model2 = gensim.models.Word2Vec.load(path2)
        model3 = KeyedVectors.load("F:\\inter\\nlp_test\\models\\vector\\tencent-ailab-embedding-zh-d200-v0.2.0-s.bin") 
        df = pd.read_csv(input_file)
        df[model1_name] = ''
        df[model2_name] = ''
        df[model3_name] = ''
        for i in range(len(df['textwords'])):
            testwords=df['textwords'][i]
            res1 = self.find_similar_words_with_filtering(model1,testwords,1)
            res2 = self.find_similar_words_with_filtering(model2,testwords,1)
            res3 = self.find_similar_words_with_filtering(model3,testwords,0)
            df.at[i,model1_name] = res1 
            df.at[i,model2_name] = res2 
            df.at[i,model3_name] = res3
        df.to_csv(output_file,index=False) 

    def combine_remove_filter(self,input_file_model,input_file_llm,outputfile):
        #处理llm和model结果合并，切词过滤，去重处理
        word_cutter = WordCutter()
        df1 = pd.read_csv(input_file_model)
        df2 = pd.read_csv(input_file_llm)
        merged_df = pd.concat([df1, df2], ignore_index=True)
        merged_df = merged_df.drop_duplicates(subset='textwords')
        # merged_df['merged_cols'] = ''
        cols_to_merge = ['word2vec_baike','word2vec_wx','word2vec_tencent','llm(gpt-4o)']
        merged_df['merged_cols'] = merged_df[cols_to_merge].apply(lambda row: [self.extract_from_string(str(row[col])) for col in cols_to_merge], axis=1)
        for i in range(len(merged_df['merged_cols'])):
            flat_list = []
            for sublist in merged_df['merged_cols'][i]:
                flat_list.extend(sublist)
            for j in range(len(flat_list)):
                try:
                    if len(word_cutter.cut(flat_list[j]))!=1:
                        word_cut = set(word_cutter.cut(flat_list[j]))
                        textword_cut = set(word_cutter.cut(merged_df['textwords'][i]))
                        if textword_cut.issubset(word_cut):
                            flat_list.remove(flat_list[j])
                except IndexError:
                    continue
                merged_df.at[i,'merged_cols'] = set(flat_list)
        merged_df.to_csv(outputfile, index=True)


    
if __name__ == '__main__':
    sy = synonyms()
    root_path = get_root_path()
    file_name = 'input.csv'
    outputfile_name='models_output.csv'
    file_path = os.path.join(root_path, 'embedding/word2vec/data/input', file_name)
    outputfile_path_model=os.path.join(root_path, 'embedding/word2vec/data/output', outputfile_name)
    sy.handle_different_models(file_path,outputfile_path_model)
    # sy.combine_remove_filter()
    print("处理已完成")
