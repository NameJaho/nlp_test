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
            for i in value.keys():
                if i not in ls:
                    ls.append(i)
        return list(set(ls ))

    def cut_entity(self, ls):
        cut_list = [self.wc.cut(i) for i in ls]
        merged_list = [item for sublist in cut_list for item in sublist]

        return list(set(merged_list))


if __name__ == "__main__":
    text = "赛百味 vs 麦当劳"
    entity_extractor = EntityExtractor()
    res = entity_extractor.extract(text)
    print(f'entity:{res}')
    format_ = entity_extractor.format(res)
    # print(res)
    print(format_)
