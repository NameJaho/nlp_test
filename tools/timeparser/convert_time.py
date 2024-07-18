import re
import time
from datetime import datetime

import arrow
import timeparser as tp
from tools.utils import timer

# Precompiled regex patterns
re_fy = re.compile(r'FY(\d{2})')
re_qh = re.compile(r'(\d{1})([QHqh])(2\d{1})')
re_full_date = re.compile(r'20\d{2}\.\d{2}\.\d{2}')
re_short_date = re.compile(r'20\d{2}\.\d{2}')
re_year_month = re.compile(r'(\d{4})(\d{2})')
re_qd = re.compile(r'(2\d{1})Q\d{1}')
re_simple_year = re.compile(r'(20\d{2}|19\d{2}|21\d{2})')
re_year_term = re.compile(r'(20\d{2})第.季度')
re_small_year = re.compile(r'(2\d{1})(Q\d{1}|q\d{1}|H\d{1}|h\d{1})')
re_inner_year = re.compile(r'(20\d{2}年内|19\d{2}年内|21\d{2}年内)')
re_year_range = re.compile(r'(20\d{2})年-(20\d{2})年')

re_quarter_keywords = re.compile(r'[一|二|三|四]季度')
re_quarter_prefix = re.compile(r'第[一|二|三|四]季')
re_quarter_middle = re.compile(r'第[一|二|三|四|1|2|3|4]季度中')

re_match_one_q = re.compile(r'^(第)?[一二三四]季度$')

re_rule1 = re.compile(r'20\d{2}-20\d{2}')
re_rule2 = re.compile(r'20\d{2}年\d-\d{1,2}月')
re_rule3 = re.compile(r'\d-\d')
re_rule4 = re.compile(r'\d{1,2}个月(内|以内)')
re_rule5 = re.compile(r'^(上半年|下半年)$')

replace_keywords_common = {
    "\xa0": " ",
    "Q1": "第一季度",
    "Q2": "第二季度",
    "Q3": "第三季度",
    "Q4": "第四季度",
    "H1": "上半年",
    "H2": "下半年",
    "h1": "H1",
    "h2": "H2",
    '三月': "3月",
    '最近一年': "近一年",
    '最近': "近一年",
    '近期': "近一年",
    '过去一年': "近一年",
    '双11': "双十一",
    '11.11': "双十一",
    '6.18': "六一八",
}


def get_quarter(date_str):
    date = arrow.get(date_str)
    month = date.month
    # 计算季度
    quarter = (month - 1) // 3 + 1
    return quarter


def rewrite_year(query):
    if re_fy.findall(query):
        year = re_fy.findall(query)[0]
        query = re_fy.sub(f'20{year}', query)
    if re_qh.findall(query):  # 1Q23 1H23
        num, q_or_h, year = re_qh.findall(query)[0]
        query = query.replace(num + q_or_h + year, year + q_or_h.upper() + num)
        print(query)

    # 匹配202303 替换成 2023年3月
    if re_full_date.findall(query):
        format_time = re_full_date.findall(query)[0]
        query = query.replace(format_time,
                              format_time.split('.')[0] + '年' + str(int(format_time.split('.')[1])) + '月' + str(
                                  int(format_time.split('.')[2])) + '日')
    elif re_short_date.findall(query):
        format_time = re_short_date.findall(query)[0]
        query = query.replace(format_time,
                              format_time.split('.')[0] + '年' + str(int(format_time.split('.')[1])) + '月')

    if re_year_month.match(query):
        query = re_year_month.sub(lambda x: f"{x.group(1)}年{int(x.group(2))}月", query)

    item = re_qd.findall(query)
    if item:
        query = query.replace(item[0], item[0] + "年")
        print('error6' if '20年19年' in query else "")

    year = re_simple_year.findall(query)
    if year:
        for item in year:
            if item + '年' not in query and item + '元' not in query and item + '万' not in query and item + '亿' not in query and item + '人民币' not in query:
                query = query.replace(item, item + '年')

    year2 = re_year_term.findall(query)  # '2022第一季度大环境不好，对2022年-2023年作出经济分析'
    if year2:
        for item in year2:
            query = query.replace(item, item + '年').replace('年年', '年')

    small_year = re_small_year.findall(query)
    if small_year:
        for item in small_year:
            if '年' not in ''.join(list(small_year[0])):
                query = query.replace(item[0], item[0] + '年')

    year2 = re_inner_year.findall(query)
    if year2:
        for item in year2:
            query = query.replace(item, item.replace('年内', '年'))

    year2 = re_year_range.findall(query)
    if year2:
        query = re_year_range.sub(f'{year2[0][0]}-{year2[0][1]}年', query)
    return re.sub(r'年{2,}', '年', query)  # 替换多个年


def rewrite_query(query):
    # if re.findall('\d{2,}年?Q\d-(\d)', query):
    #     print('-'+re.findall('\d{2,}年?Q\d-(\d)', query)[0])
    for word in replace_keywords_common:
        if word in query:
            query = re.sub(word, replace_keywords_common[word], query, flags=re.IGNORECASE)
    if re_quarter_keywords.match(query) and '第' not in query:
        query = re_quarter_keywords.sub('第\g<0>', query)
    if re_quarter_prefix.match(query) and '度' not in query:
        query = re_quarter_prefix.sub('\g<0>度', query).replace('度季', '季度')
    if re_quarter_middle.findall(query):
        query = query.replace('季度中', '季度')
    return query


def rewrite_black_list(text):
    quarter_dict = ['春天', '夏天', '秋天', '冬天']
    for q in quarter_dict:
        text = text.replace(q, "")
    return text


def format_time_frame(time_frame, text=None, pre_year=None, time_base=None):
    try:
        if isinstance(time_frame, list) and len(time_frame) == 2:
            start_date = datetime.strptime(time_frame[0], "%Y-%m-%d %H:%M:%S")
            end_date = datetime.strptime(time_frame[1], "%Y-%m-%d %H:%M:%S")
            start_year, end_year = start_date.year, end_date.year
            start_month, end_month = start_date.month, end_date.month
            if text in [
                '最近一年', '过去一年', '近一年', '近半年', '上一年', '上年', '前一年', '前年',
                '近两年', '近三年', '近四年', '近五年', '近两个月', '近三个月', '近四个月', '近五个月',
                '近六个月', '近七个月', '近八个月', '近九个月', '近十个月', '近十一个月', '近十二个月',
                '近1个月', '近2个月', '近3个月', '近4个月', '近5个月', '近6个月', '近7个月', '近8个月',
                '近9个月', '近10个月', '近11个月', '近12个月'
            ]:
                # start_month = start_month + 1
                if start_month > 12:
                    start_year += 1
                    start_month = start_month - 12

            start_quarter, end_quarter = (start_month - 1) // 3 + 1, (end_month - 1) // 3 + 1

            if not str(start_year).startswith('20') or not str(end_year).startswith('20'):
                return None
            if end_year - start_year > 3:  # 年跨度不能超过3
                return None
            if (start_year < 2015 and end_year < 2015) or (start_year > 2050 and end_year > 2050):
                return None
                # 匹配单季度
            if re_match_one_q.match(text.strip()):
                q = re_match_one_q.match(text.strip()).group()
                if not pre_year:
                    year = arrow.get(time_base).format('YYYY')
                    text = year + q
                    start_year = end_year = int(year)
                else:
                    text = str(pre_year) + q
                    start_year = end_year = pre_year

                print('match q  ' + text)
            if end_year < start_year:
                return None
            return {
                'year': (start_year, end_year),
                'quarter': (start_quarter, end_quarter),
                'month': (start_month, end_month),
                'text': text
            }
        return None

    except Exception as e:
        print(str(e))
        return None


# @timer
def convert_time(text, time_base=time.time(), test=False, fast=False):
    # 1. 时间关键词处理：
    text = rewrite_year(text.replace('\n', ''))
    # 2. 替换关键词
    text = rewrite_query(text)
    rewrite_text = rewrite_black_list(text)
    print(rewrite_text)
    if test:
        time_frame_list = tp.extract_time_modify(rewrite_text, time_base=time_base, fast=fast)  # 测试用
    else:
        time_frame_list = tp.extract_time(rewrite_text, time_base=time_base)
    print(time_frame_list)
    time_list = []
    pre_year = None
    for index, tim_frame in enumerate(time_frame_list):
        # print(tim_frame['text'])
        # print(tim_frame['type'])

        if '日' in tim_frame['text'] and tim_frame['type'] == 'time_point':
            continue
        if not re_rule1.findall(tim_frame['text'].strip()):
            # 2024年1-4月
            if re_rule2.findall(tim_frame['text'].strip()):
                print(tim_frame['text'])
            # 去年11-12月
            elif re_rule3.findall(tim_frame['text'].strip()):
                if not tim_frame['text'].endswith('月') and not tim_frame['text'].endswith('年'):
                    print(tim_frame['text'] + '  pass')
                    continue
                if '年' not in tim_frame['text']:
                    year = str(pre_year)
                    if not pre_year:
                        year = arrow.get(time_base).format('YYYY')
                    tim_frame['text'] = str(year) + '年' + tim_frame['text']
            # 过滤n个月内
            elif re_rule4.findall(tim_frame['text'].strip()):
                print(tim_frame['text'] + '  pass')
                continue
            elif re_rule5.findall(tim_frame['text'].strip()):
                print(tim_frame['text'] + '  pass')

                year = str(pre_year)
                if not pre_year:
                    year = arrow.get(time_base).format('YYYY')
                tim_frame['text'] = str(year) + '年' + tim_frame['text']

        if tim_frame['type'] in ['time_point', 'time_span']:
            time_range = tim_frame['detail']['time']
            if time_range[-1] == 'inf':
                time_range[-1] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elif time_range[0] == '-inf':
                continue
                # time_range[0] = arrow.get(time_range[-1], tzinfo='local').shift(years=-1).format("YYYY-MM-DD HH:mm:ss")
            time_list.append(format_time_frame(time_range, tim_frame['text'], pre_year, time_base=time_base))
        elif tim_frame['type'] == 'time_period':
            if tim_frame['detail']['time']['point']:
                time_range = tim_frame['detail']['time']['point']['time']
                time_list.append(format_time_frame(time_range, tim_frame['text'], pre_year, time_base=time_base))
            else:  # 手机天猫平台每个月的销售
                time_list = convert_time('最近一年')
        if time_list and time_list[-1]:
            if time_list[-1]['year'][0] == time_list[-1]['year'][1]:
                pre_year = time_list[-1]['year'][0]
        # elif tim_frame['type'] == 'time_delta': # 三年未处理
        #     # delta =
        #     start = arrow.get(time_base).shift()
    # print(time_list)
    return [i for i in time_list if i]


if __name__ == '__main__':
    ts_sample = [
        """
        9只公募REITs发售在即，继续推荐“混改”标的一兴证建筑每周观点（2021.5.22-2021.5.28）。
O本周首批9只公募REITs完成线下询价，预计募资314.03亿元。 本周9，评级只公募REITs完成线下询价，平均有效认购倍数超7倍，认购较为火g审慎增持爆； 并且参与REITs的配售对象类型多样，首批公募REITs将在5月3130买入日启动公众投资者认购。 本周我们发布深度报告《基建REITs系列深度审慎增持报告之五：投资篇一【REITs上市的一小步，存量盘活的一大步】》，强1烈建议重视REITs对中游建企构成“估值+业绩双重利好”的逻辑。 53审慎增持。绿色建筑市场和产业工人队伍发展利好钢结构行业，继续推荐规模优势审慎增持不断加深的钢结构制造龙头【鸿路钢构】。 从宏观和产业角度来看，“七3审慎增持普”数据表明老龄化，叠加产业工人政策将加快抬升建筑用工成本，钢结32审慎增持构受益政策大力推广绿色建筑，未来相对传统钢混建筑的用人成本优势将进一步突出。 从公司角度来看，【鸿路钢构】规模优势极大增强了公司对下游谈判和转嫁钢价上涨的能力，继续看好公司中长期逻辑。

1、行业观点与投资建议。
、本周观点：9只公募REITs发售在即，继续推荐“混改”标的。
本周首批9只公募REITs完成线下询价，预计募资314.03亿元。 本周张江REIT、浙江杭徽、东吴苏园、普洛斯、盐港REIT、首钢绿能、首创水务、广州广河、蛇口产园9只公募REITs完成线下询价，平均有效认购倍数超7倍，认购较为火爆； 并且参与REITs的配售对象类型多样，包括机构自营投资账户、保险资金证券投资账户、基金公司或者资管子公司的专户产品、集合信托计划、私募基金、证券公司集合资产管理计划。 首批公募REITs将在5月31日启动公众投资者认购。
本周我们发布深度报告《基建REITs系列深度报告之五：投资篇一【REITs上市的一小步，存量盘活的一大步】》，强烈建议重视REITs对中游建企构成“估值+业绩双重利好”的逻辑：REITs产品股息率高于权益产品和无风险利率，长期回报率接近权益。 从新加坡经验来看，RETIs流动性可能不差于权益产品：
（1）收益率方面：从美国REITs市场长期经验来看，REITs较其他投资品种具有稳定股息和长期回报率优势，是股债之外的一大重要投资品种，理论最佳配置比例达到17%，契合长期资金需求。 我们进一步考察过去5~15年间的美国、日本、新加坡、中国香港四地的REITs产品收益率表现，从股息率来看，REITs指数股息率约为4%~6%，较无风险利率高约1.5~3.5pct，较权益指数股息率高约0~2pct。 从10年期整体回报率来看，REITs指数整体回报率与权益指数较为接近。
        """,
        # '2022年adc，近一年又adb，下半年adb',
        # '届时预计国内废塑料回收再生量将达到2500万吨，较2020年1600万吨增长56%。'
        # '我国现制茶市场规模有望从2020年1136亿复合增长25%达到2025年3400亿元',
        # '我们预计国内单车玻璃价值有望从2019年646元提升至2025年1147元',
        # '预计24年4680的材料和工艺还会继续迭代，2代4680将有可能在材料选择上做突破。',
        '2019年abcd干了什么，2020Q1又做了什么，20Q3又做了什么'

    ]
    t = 0
    for keyword in ts_sample:
        s = time.time()

        res = convert_time(keyword, arrow.get('2022-08-13').timestamp(), test=True, fast=True)
        print(time.time() - s)
        print(f" len: {len(res)}   {res}" )
