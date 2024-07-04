import json
import time
import os
import re
import unicodedata

import jieba
import requests
# import torch
# import pyhocon
import pkg_resources

from loguru import logger
from collections.abc import Sequence


def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        class_name = args[0].__class__.__name__
        end_time = time.time()
        execution_time = end_time - start_time
        logger.debug(f"{class_name}.{func.__name__} executed in {execution_time:.4f} seconds.")
        return result

    return wrapper


def load_text(*file_paths, by_lines=False):
    with open(f_join(*file_paths), "r", encoding="utf-8") as fp:
        if by_lines:
            return fp.readlines()
        else:
            return fp.read()


def f_join(*file_paths):
    """
    join file paths and expand special symbols like `~` for home dir
    """
    file_paths = pack_varargs(file_paths)
    fpath = f_expand(os.path.join(*file_paths))
    if isinstance(fpath, str):
        fpath = fpath.strip()
    return fpath


def f_expand(fpath):
    return os.path.expandvars(os.path.expanduser(fpath))


def pack_varargs(args):
    """
    Pack *args or a single list arg as list

    def f(*args):
        arg_list = pack_varargs(args)
        # arg_list is now packed as a list
    """
    assert isinstance(args, tuple), "please input the tuple `args` as in *args"
    if len(args) == 1 and is_sequence(args[0]):
        return args[0]
    else:
        return args


def is_sequence(obj):
    """
    Returns:
      True if the sequence is a collections.Sequence and not a string.
    """
    return isinstance(obj, Sequence) and not isinstance(obj, str)


def get_root_path():
    package_path = pkg_resources.resource_filename(__name__, "")
    parent_path = os.path.dirname(package_path)
    return parent_path


def flatten(_list):
    """展平list"""
    return [item for sublist in _list for item in sublist]


def read_config(run_experiment, file_name):
    """读取配置文件"""
    name = str(run_experiment)
    config = pyhocon.ConfigFactory.parse_file(file_name)[name]
    return config


def get_device():
    """
    Get the current device (MPS, CPU, or GPU).

    Returns:
        str: The current device.
    """

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    return device


def get_uie_device():
    if torch.cuda.is_available():
        device = "gpu"
    else:
        device = "cpu"

    return device


def to_cuda(x):
    """ GPU-enable a tensor """
    device = get_device()
    if device == "cuda":
        return x.cuda()
    else:
        return x


def convert_entity_format(entities):
    _entities = {}
    for item in entities:
        for key, values in item.items():
            count_dict = {}
            for value in values:
                text = value['text']
                count_dict[text] = count_dict.get(text, 0) + 1
            _entities[key] = count_dict
    return _entities


def is_chinese(string):
    for char in string:
        if unicodedata.category(char) == 'Lo':
            return True
    return False


def load_stopwords():
    base_dict = 'word_splitter/base_stopwords.txt'
    biz_dict = 'word_splitter/biz_stopwords.txt'
    merged_dict = 'word_splitter/merged_stopwords.txt'

    base_dict_path = os.path.join(get_root_path(), base_dict)
    biz_dict_path = os.path.join(get_root_path(), biz_dict)
    merged_dict_path = os.path.join(get_root_path(), merged_dict)

    # Check if output file already exists
    if os.path.exists(merged_dict_path):
        os.remove(merged_dict_path)

    with open(base_dict_path) as f1, open(biz_dict_path) as f2:
        with open(merged_dict_path, 'a') as f3:
            for line in f1:
                f3.write(line)
            for line in f2:
                f3.write(line)

    return merged_dict_path


@timer
def get_core_word(query):
    words = jieba.cut(query)  # 分词
    print(words)
    w = ' '.join(words)
    print(w)
    url = 'http://47.99.56.228:8020/get_entity_core_word'  # 外网
    # url = 'http://192.168.1.177:8149/get_term_weight' # 内网
    data = {"query": w, 'trace_id': '123456'}

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=data, headers=headers)
    # print(response.text)
    print(response.status_code)
    res = json.loads(response.text)
    # print('res = ',res)
    return res


@timer
def get_core_word_by_words(words):
    # words = jieba.cut(query)  # 分词
    # print(words)
    # w = ' '.join(words)
    # print(w)
    url = 'http://47.99.56.228:8020/get_entity_core_word'  # 外网
    # url = 'http://192.168.1.177:8149/get_term_weight' # 内网
    data = {"query": words, 'trace_id': '123456'}

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=data, headers=headers)
    # print(response.text)
    # print(response.status_code)
    res = json.loads(response.text)
    # print('res = ',res)
    return res


def load_prompt_template(prompt_name):
    root_path = get_root_path()
    prompt_path = f'{root_path}/prompts/' + prompt_name
    prompt = load_text(prompt_path)
    return prompt


def fill_prompt(args, prompt_name=''):
    prompt = load_prompt_template(prompt_name)
    prompt = prompt.format(**args)
    logger.debug(f"prompt: {prompt}")
    return prompt


def is_no_chinese_and_max_one_space(text):
    # 使用正则表达式匹配不包含汉字的字符串
    if re.search(r'[\u4e00-\u9fff]', text):
        return False

    # 计算空格数量
    space_count = text.count(' ')

    # 判断空格数量是否小于等于1
    if space_count <= 1:
        return True
    else:
        return False


if __name__ == '__main__':
    # print(get_core_word('阿里云在欧洲云计算市场的市占率？'))
    print(get_core_word('2024年3月热搜'))
    # fill_prompt({"query": "dddd", "summary": "xxx"}, prompt_name='scores.txt')
