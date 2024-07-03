import requests
import json


class EntityExtractor:
    def __init__(self):
        pass

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


if __name__ == "__main__":
    text = "抖音电商中国"
    entity_extractor = EntityExtractor()
    res = entity_extractor.extract(text)
    print(res)
