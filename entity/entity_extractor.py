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
        try:
            res = requests.post(url=url, headers=headers, data=json.dumps(data))
        except:
            print("请求接口失败")
            return ""
        else:
            result = res.json()['data']['entities']
        return result


if __name__ == "__main__":
    text = "喜茶快要上市了"
    entity_extractor = EntityExtractor()
    res = entity_extractor.extract(text)
    print(res)
