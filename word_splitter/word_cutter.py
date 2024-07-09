import os
import re
import jieba
from tools import utils


WHITE_DICT = 'white_list_v2.5.txt'


class WordCutter:
    def __init__(self):
        white_dict_path = os.path.join(utils.get_root_path(), 'word_splitter', WHITE_DICT)
        jieba.load_userdict(white_dict_path)

    @staticmethod
    def cut(text):
        # TODO: 标点符号替换为空格，但有些特殊字符需保留，如-
        # text = re.sub('\W*', ' ', ''.join(text))
        words = jieba.lcut(text)
        return [i for i in words if i != ' ']


if __name__ == '__main__':
    sentences = [
        # '大数据分析',
        # 'BMW电动宝马新能源',
        # '为什么海外品牌需要在中国电商代运营模式',
        # '空刻意面',
        # '腾讯视频号规模',
        # '柠檬共和国鸭屎香柠檬茶；兰芳园冻柠茶；维他柠檬茶',
        # '桑葚玫瑰红茶',
        # '菲诺生椰小拿铁',
        # '擦窗机器人',
        # 'BIOCENTA第五代白番茄',
        # '爱鱼者酸菜鱼饭人均价格',
        # '鱼拿酸菜鱼人均价格',
        # '月之暗面 算力',
        # '% ARABICA 温哥华拿铁',
        # '达美乐薯角',
        # '迈美希美白饮',
        # '字节跳动的番茄小说2018-2023年收入是多少',
        # '客户包括泰科、漠视和阿菲诺等全球知名公司',
        # '菲诺 利润',
        # '主要客户有艾菲诺莫世泰科等海外龙头公司',
        # '马尼埃里计划与她的一些布斯校友一起访问意大利的波多菲诺',
        # '发泡硅胶片',
        # '2023国潮新茶饮产业洞察报告',
        # '运维外包',
        # '新能源汽车 低线城市的发展',
        '银发经济'
        '抖品牌'
        ]

    wc = WordCutter()
    for sentence in sentences:
        print(wc.cut(sentence))
