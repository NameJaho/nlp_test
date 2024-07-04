import json

import requests
from loguru import logger

from tools.utils import timer


def extract(texts):
    url = "http://183.6.28.97:8010/extract"

    headers = {"Content-Type": "application/json"}

    data = {"text": texts}
    try:
        res = requests.post(url=url, headers=headers, data=json.dumps(data))
    except:
        logger.error("请求接口失败")
        return ""
    else:
        r = res.json()['result']
    return r


@timer
def extract_from_platform(texts):
    url = "http://183.6.28.97:7766/entity_extractor"

    headers = {"Content-Type": "application/json"}

    data = {"query": texts}
    try:
        res = requests.post(url=url, headers=headers, data=json.dumps(data))
    except:
        logger.error("请求接口失败")
        return ""
    else:
        r = res.json()['data']['entities']
    return r


if __name__ == '__main__':
    print(extract_from_platform('Dr钻戒'))
