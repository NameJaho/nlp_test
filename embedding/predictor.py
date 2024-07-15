import pandas as pd
from tools.utils import get_root_path
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagModel
import numpy as np
import os

INPUT_FILE = '0626_2w4_pred_score.csv'
OUTPUT_FILE = ''
MODEL_FOLDER = 'sentence_embedding'
MODEL_NAMES = ['bge_lr4e5_0627_new_label_v1', 'bge_lr4e5_0628', 'bge_lr4e5_0704']


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
        model_name = model_path.split('/')[-1]
        if 'stella' in model_name:
            model_type = 'flagE'
        else:
            model_type = 'flagE'

        df[model_name] = self.predict_scores(query_col='query', doc_col='doc', df=df,
                                             model_path=model_path, model_type=model_type)
        return df

    def get_model_path_list(self):
        model_path_list = []
        for root, folders, files in os.walk(self.model_folder):
            for folder in folders:
                if dir in MODEL_NAMES:
                    path = os.path.join(root, folder)
                    model_path_list.append(path)
            return model_path_list

    @staticmethod
    def fix_content(row):
        content = row['doc']
        if '[' in content:
            return ''.join(eval(content))
        return content

    def process(self):
        df = self.convert()
        df['doc'] = df.apply(self.fix_content, axis=1)
        model_path_list = self.get_model_path_list()
        for model_path in model_path_list:
            df = self.model_result(model_path, df)
        return df


if __name__ == '__main__':
    predictor = Predictor()
    result_df = predictor.process()
    result_df.to_csv(predictor.output_file_path)
