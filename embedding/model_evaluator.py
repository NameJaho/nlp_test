import pandas as pd
from tools.utils import get_root_path
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagModel
import numpy as np
import os
import ast

INPUT_FILE = '0626_2w4_pred_score.csv'
OUTPUT_FILE = 'output.csv'
MODEL_FOLDER = 'sentence_embedding'
MODEL_NAMES = ['bge_lr4e5_0704','bge-small-zh-v1.5', 'bge_lr4e5_0628']


class Predictor:
    def __init__(self):
        self.input_file_path = os.path.join(get_root_path(), 'embedding/input', INPUT_FILE)
        self.output_file_path = os.path.join(get_root_path(), 'embedding/output', OUTPUT_FILE)
        self.model_folder = os.path.join(get_root_path(), 'models', MODEL_FOLDER)

    def convert(self):
        # df = pd.read_csv('./../data/mark_data/0704_18h_mark_data.csv',sep='\t')
        df = pd.read_csv(self.input_file_path)
        # query/doc/label
        return df

    @staticmethod
    def list2str(row, k):
        return ''.join(eval(row[k]))

    @staticmethod
    def calculate_score(qvs, dvs):
        scores = []
        for i in range(len(qvs)):
            qv, dv = qvs[i], dvs[i]
            qv = np.array([qv])
            dv = np.array([dv])
            score = qv @ dv.T
            score = score.tolist()[0]
            scores.append(score[0])
        return scores

    @staticmethod
    def list2vector(data, model, flag='query', max_length=512):
        if type(data) is str:
            s = [data]
        elif type(data) is list:
            s = data
        else:
            s = []
        if not s:
            return []
        if flag == 'query':
            vectors = model.encode_queries(s, batch_size=8)
            if isinstance(data, str):
                vector = vectors.tolist()[0]
            else:
                vector = vectors.tolist()
        else:

            vectors = model.encode(s, batch_size=8, max_length=max_length)
            if isinstance(data, str):
                vector = vectors.tolist()[0]
            else:
                vector = vectors.tolist()

        return vector

    def predict_scores(self, query_col, doc_col, df, model_path, model_type='flagE'):
        qs = list(df[query_col])
        ds = list(df[doc_col])

        if model_type == 'flagE':
            model = FlagModel(model_path, query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
                              use_fp16=True)
            q_vecs = self.list2vector(qs, model)
            d_vecs = self.list2vector(ds, model, flag='doc')

        else:
            model = SentenceTransformer(model_path)
            q_vecs = model.encode(qs, normalize_embeddings=True)
            d_vecs = model.encode(ds, normalize_embeddings=True)
        scores = self.calculate_score(q_vecs, d_vecs)

        return scores

    def model_result(self, model_path, df):
        model_name = model_path.split('\\')[-1]
        model_type = 'flagE'
        df[model_name] = self.predict_scores(query_col='query', doc_col='doc', df=df,
                                             model_path=model_path, model_type=model_type)
        return df

    def get_model_path_list(self):
        model_path_list = []
        for root, folders, files in os.walk(self.model_folder):
            for folder in folders:
                if folder in MODEL_NAMES:
                    path = os.path.join(root, folder)
                    model_path_list.append(path)
            return model_path_list

    @staticmethod
    def fix_content(row):
        content = row['doc']
        if '[' in content:
            try:
            # 尝试将字符串解析为 Python 对象
                parsed_content = ast.literal_eval(content)
            # 检查解析后的对象是否为列表
                if isinstance(parsed_content, list):
                    return ''.join(parsed_content)
            except (ValueError, SyntaxError):
                pass
        return content

    def process(self):
        df = self.convert()
        df['doc'] = df.apply(self.fix_content,axis=1)
        model_path_list = self.get_model_path_list()
        for model_path in model_path_list:
            df = self.model_result(model_path, df)
        return df

    @staticmethod
    def compare_rank_best(pred_col, real_col, df, range_n, filter_col=None):
        #评估模型
        if filter_col:
            df = df[df[filter_col] == 1]
        pos_arr = []
        neg_arr = []
        total_arr = []
        for name, group in df.groupby('query'):
            group = group.sort_values(by=pred_col, ascending=False)

            # 统计标注中0和1的总数
            total_label_zero_count = (group[real_col] == 0).sum()
            total_label_one_count = (group[real_col] == 1).sum()

            top_n_label_one_count = (group.head(range_n)[real_col] == 1).sum()
            tail_n_label_zero_count = (group.tail(range_n)[real_col] == 0).sum()

            top_score = (top_n_label_one_count/min(total_label_one_count, range_n))*100
            tail_score = (tail_n_label_zero_count/min(total_label_zero_count, range_n))*100

            pos_arr.append(top_score)
            neg_arr.append(tail_score)
            total_arr.append((top_score + tail_score)/2)
            #将总分数归回100区间
        # print(pred_col,query, top_score,tail_score)
        return np.array(pos_arr).mean(), np.array(neg_arr).mean(), np.array(total_arr).mean()
    
    def get_eva_info(self, df, model_names, topns, real_col='label'):
        eva_df = []
        for model_name in model_names:
            arr = [model_name]
            for topn in topns:
                pscore, nscore, tscore = self.compare_rank_best(pred_col=model_name, real_col=real_col, df=df, range_n=topn)
                arr = arr + [pscore, nscore, tscore]
            eva_df.append(arr)
        eva_names = []
        for topn in topns:
            eva_names = eva_names + [str(topn) + '_pos', str(topn) + '_neg', str(topn) + '_total']
        eva_df = pd.DataFrame(eva_df, columns=['model_name'] + eva_names)
        return eva_df   


if __name__ == '__main__':
    range_list = [5, 10]
    predictor = Predictor()
    result_df = predictor.process()
    result_df = result_df.rename({"人工标注": 'label'}, axis=1)
    result_df = predictor.get_eva_info(result_df, model_names=MODEL_NAMES, topns=range_list)
    result_df.to_csv(predictor.output_file_path)
