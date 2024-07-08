# import jieba
import requests
import json
import os
from tools.utils import get_root_path, get_uie_device, convert_entity_format
from uie.uie_predictor import UIEPredictor
from word_splitter.word_cutter import WordCutter

SCHEMA = ['公司', '行业', '产品', '技术', '地区', '人物', '疾病', '日期', '产业']
MODEL_PATH = os.path.join(get_root_path(), 'models/entity/model_best')


class EntityExtractor:
    def __init__(self):
        self.wc = WordCutter()
        self.device = get_uie_device()
        self.ie = None

    @staticmethod
    def extract(texts):
        url = "http://183.6.28.97:7766/entity_extractor"

        headers = {"Content-Type": "application/json"}

        data = {"query": texts}
        for _ in range(3):
            try:
                res = requests.post(url=url, headers=headers, data=json.dumps(data), timeout=10)
            except:
                print("请求接口失败")
            else:
                result = res.json()['data']['entities']
                return result
        return ''

    def extract_local(self, text):
        if not self.ie:
            self.ie = UIEPredictor(model='uie-base', task_path=MODEL_PATH, schema=SCHEMA, device=self.device)

        entities = self.ie(text)
        return convert_entity_format(entities)

    @staticmethod
    def format(result):
        ls = []
        for key, value in result.items():
            if key in ['疾病', '地区', '日期']:
                continue
            for i in value.keys():
                if i not in ls:
                    ls.append(i)
        return list(set(ls ))

    def cut_entity(self, ls):
        cut_list = [self.wc.cut(i) for i in ls]
        merged_list = [item for sublist in cut_list for item in sublist]

        return list(set(merged_list))

    @staticmethod
    def extract_test(texts):
        url = "http://183.6.28.97:7766/entity_extractor_test"

        headers = {"Content-Type": "application/json"}

        data = {"query": texts}
        for _ in range(3):
            try:
                res = requests.post(url=url, headers=headers, data=json.dumps(data), timeout=10)
            except:
                print("请求接口失败")
            else:
                print(res.json())

                result = res.json()['data']['entities']
                return result
        return ''


if __name__ == "__main__":
    text = "婴幼儿即食米糊"
    #text = "森马 vs 海澜之家"
    #text = "友望云朵洗地机"
    text = '深圳市晶存科技是nvidia cloud partner吗'

    entity_extractor = EntityExtractor()
    res = entity_extractor.extract(text)
    print(f'entity:{res}')
    format_ = entity_extractor.format(res)
    # print(res)
    print(format_)
    res = entity_extractor.extract_test(text)
    print(res)
