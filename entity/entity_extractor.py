# import jieba
import requests
import json

from word_splitter.word_cutter import WordCutter


class EntityExtractor:
    def __init__(self):
        self.wc = WordCutter()

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

    @staticmethod
    def format(result):
        ls = []
        for key, value in result.items():
            if key in ['疾病', '地区', '日期']:
                continue
            ls.append([i for i in value.keys()][0]) if value not in ls else ''
        # cut_list = [jieba.lcut(i) for i in ls ]
        # merged_list = [item for sublist in cut_list for item in sublist]
        # list(set(merged_list))
        return list(set(ls))

    def cut_entity(self, result):
        ls = []
        for key, value in result.items():
            if key in ['疾病', '地区', '日期']:
                continue
            ls.append([i for i in value.keys()][0]) if value not in ls else ''
        cut_list = [self.wc.cut(i) for i in ls]
        merged_list = [item for sublist in cut_list for item in sublist]

        return list(set(merged_list))


if __name__ == "__main__":
    text = "森马 vs 海澜之家"
    entity_extractor = EntityExtractor()
    res = entity_extractor.extract(text)
    format_ = entity_extractor.cut_entity(res)
    # print(res)
    print(format_)
