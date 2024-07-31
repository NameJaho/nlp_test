import yaml
import re
import pandas as pd


def load_config(file_path):
    # 加载 YAML 配置
    with open(file_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config


def concat_dict(yaml_node):
    merged_list = []
    for item in yaml_node:
        merged_list.extend(item)
    return merged_list


def concat_nested_dict(yaml_node):
    merged_list = []
    for item_list in yaml_node.values():
        for item in item_list:
            merged_list.extend(item)
    return merged_list


# 获取全局 nickname 黑名单
def get_global_nickname_blacklist(config):
    global_nickname_blacklist_yaml = config['GLOBAL']['nickname_blacklist']
    global_nickname_blacklist = concat_nested_dict(global_nickname_blacklist_yaml)
    return global_nickname_blacklist


# load domain nickname blacklist
def get_domain_nicknames_blacklist(config, domain):
    domain_nicknames_blacklist_yaml = config[domain]['domain_nickname_blacklist']
    domain_nicknames_blacklist = concat_dict(domain_nicknames_blacklist_yaml)
    return domain_nicknames_blacklist


def get_content_whitelist(config, domain='', sub_domain=''):
    if sub_domain:
        cat_content_whitelist_yaml = config[domain][sub_domain]['content_whitelist']
    else:
        cat_content_whitelist_yaml = config[domain]['content_whitelist']
    return cat_content_whitelist_yaml


def get_content_blacklist(config, domain='', sub_domain=''):
    if sub_domain:
        cat_content_blacklist_yaml = config[domain][sub_domain]['content_blacklist']
    else:
        cat_content_blacklist_yaml = config[domain]['content_blacklist']
    cat_content_blacklist = concat_dict(cat_content_blacklist_yaml)
    return cat_content_blacklist


def is_tags_only(content):
    # 匹配标签的正则表达式模式
    tag_pattern = r'#[^#\s]+\[话题\]#'

    # 找到所有匹配的标签
    tags = re.findall(tag_pattern, content)

    # 移除所有匹配的标签
    cleaned_content = re.sub(tag_pattern, '', content)

    # 移除所有空白字符
    cleaned_content = re.sub(r'\s', '', cleaned_content)

    # 如果清理后的内容为空，则原内容只包含标签
    return len(cleaned_content) == 0


def remove_tag_list(row):
    content = row['content']
    tag_list = row['tag_list']
    for tag in tag_list.split(';'):
        content = content.replace(f"#{tag}[话题]#", '')
    return content


def remove_tag_only_posts(df):
    # 创建一个布尔序列，标记不仅仅包含标签的帖子
    mask = ~df['content'].apply(is_tags_only)

    # 使用这个掩码来过滤DataFrame
    df_filtered = df[mask]

    # 重置索引
    df_filtered = df_filtered.reset_index(drop=True)

    # 移除正文中的标签
    df_filtered['content'] = df_filtered.apply(remove_tag_list, axis=1)

    return df_filtered


def load_data(input_file):
    df = pd.read_csv(input_file)

    # remove duplicates
    df_dedup = df.drop_duplicates(subset=['user_id', 'content'])

    # fill na
    df_dedup['nickname'] = df_dedup['nickname'].fillna('')
    df_dedup['content'] = df_dedup['content'].fillna('')
    df_dedup['title'] = df_dedup['title'].fillna('')
    df_dedup['tag_list'] = df_dedup['tag_list'].fillna('')

    # drop na on content
    df_dedup = df_dedup[df_dedup['content'] != '']

    # filter tag only post
    df_dedup = remove_tag_only_posts(df_dedup)

    return df_dedup


# remove business user by global nickname blacklist
def remove_biz_user(df, word_list):
    df_biz_user = df[df['nickname'].apply(lambda x: any(word.upper() in x.upper() for word in word_list))]
    df_normal_user = df[~df['user_id'].isin(df_biz_user['user_id'])]
    return df_normal_user


# 计算总积分
def calculate_score(text, whitelist, blacklist, verbose=False):
    score = 0
    keywords = []

    # if blacklist matched, score 0 and return
    if any(word in text for word in blacklist):
        return 0, []

    # whitelist score accumulation
    for item in whitelist:
        weight = item['weight']
        for word_list in item['words']:
            for word in word_list:
                if word.upper() in text.upper():
                    # drop keyword which is contained by any keyword
                    if any([word in i for i in keywords]):
                        continue
                    if verbose:
                        print(f'*** whitelist matched:{word}[{weight}]')
                    score += weight
                    keywords.append(word)
    return score, keywords


def filter_by_score(df, content_whitelist, content_blacklist, threshold=None):
    df['text'] = df.apply(lambda x: str(x['title']) + str(x['content']) + str(x['tag_list']), axis=1)
    if threshold:
        df[['score', 'keywords']] = df.apply(lambda x: calculate_score(x['text'], content_whitelist, content_blacklist),
                                             axis=1, result_type='expand')
        # 调节积分门槛
        df = df[df['score'] >= threshold]
    else:
        df[['score', 'keywords']] = df.apply(
            lambda x: calculate_score_v2(x['text'], content_whitelist, content_blacklist),
            axis=1, result_type='expand')
        df = df[df['score'].apply(lambda x: any(i['score'] > 0 for i in x))]
        df['score'] = df['score'].apply(lambda x: [i for i in x if i['score'] != 0])

    return df


def calculate_score_v2(text, whitelist, blacklist, verbose=False):
    score_list = []
    keywords = []

    # if blacklist matched, score 0 and return
    if any(word in text for word in blacklist):
        return [{'score': 0, 'type': ''}], []

    # whitelist score accumulation
    for item in whitelist:
        # 非消费
        # if item.get('weight'):
        for type_, term in item.items():  # 'hotel',[{'weight':xx,'words':[[]]}]
            score = 0
            for term_ in term:
                weight = term_['weight']
                for word_list in term_['words']:
                    for word in word_list:
                        if '|' not in word:
                            if word.upper() in text.upper():
                                # drop keyword which is contained by any keyword
                                if any([word in i for i in keywords]):
                                    continue
                                if verbose:
                                    print(f'*** whitelist matched:{word}[{weight}]')
                                score = weight if weight > score else score
                                keywords.append(word)
                        else:
                            base_word = word.split('|')[0]
                            others = word.split('|')[1:]
                            if base_word.upper() in text.upper() and any(i in text.upper() for i in others):
                                if any([word in i for i in keywords]):
                                    continue
                                if verbose:
                                    print(f'*** whitelist matched:{word}[{weight}]')
                                score += weight
                                kw = base_word + '|' + '|'.join([i for i in others if i.upper() in text.upper()])
                                keywords.append(kw)
            score_list.append({'score': score, 'type': type_})

    return score_list, keywords


def group_by_user_v2(df):
    aggregated_df = df.groupby('user_id').agg({
        'text': lambda x: '||'.join(x),
        'nickname': 'first',
        'score': merge_arrays,  # note: this only return the score of first post
        'keywords': merge_kw,

    }).reset_index()
    return aggregated_df


def merge_kw(kw):
    merged_array = [item for sublist in kw for item in sublist]
    return merged_array


def merge_arrays(arrays):
    merged_array = [item for sublist in arrays for item in sublist]
    filtered_array = [score for score in merged_array if score['score'] > 0]
    return filtered_array


def group_by_user(df):
    aggregated_df = df.groupby('user_id').agg({
        'text': lambda x: '||'.join(x),
        'nickname': 'first',
        'score': 'max',  # note: this only return the score of first post
        'keywords': lambda x: x,

    }).reset_index()
    return aggregated_df


def show_content_by_user_id(df, content_whitelist, content_blacklist, user_id):
    text = df[df['user_id'] == user_id]['text'].values[0]
    score = calculate_score(text, content_whitelist, content_blacklist, True)
    print(f'score: {score}, text: {text}')


def show_all_contents(df, content_whitelist, content_blacklist):
    for index, row in df.iterrows():
        text = row['text']
        score = calculate_score(text, content_whitelist, content_blacklist)
        print(f'========== user[{index}]: {row["nickname"]}, score: {score}')
        print(text)


def get_unique_nicknames(df):
    unique_nicknames = df['nickname'].unique()
    return unique_nicknames


if __name__ == '__main__':
    # calculate_score('什么汽车', [{'weight': 1, "words": [['汽车', '车']]}], [], verbose=True)
    whitelist = [
        {'hotel': [{'weight': 5,
                    'words': [['四季酒店',
                               '丽思卡尔顿',
                               '文华东方',
                               '安缦',
                               '悦榕庄',
                               '洲际',
                               '半岛酒店',
                               '瑞吉',
                               'W酒店',
                               '君悦',
                               '文华东方',
                               '宝格丽酒店']]},
                   {'weight': 3, 'words': [['亚朵']]},
                   {'weight': 1, 'words': [['桔子酒店', '锦江之星']]}]},
        {'restaurant': [{'weight': 5, 'words': [['怀石料理', '米其林', '大董']]},
                        {'weight': 3, 'words': [['黑珍珠', '毋米粥', '星巴克', 'shake shack']]},
                        {'weight': 2, 'words': [['九毛九']]},
                        {'weight': 1, 'words': [['兰州拉面', '千里香馄炖', '蜜雪冰城']]}]},
        {'supermarket': [{'weight': 5,
                          'words': [['Whole Foods', 'SKP', 'BLT', 'City Super']]},
                         {'weight': 3, 'words': [['盒马', '七鲜', 'ALDI', 'LIDL']]}]},
        {'brand': [{'weight': 5,
                    'words': [['卡地亚',
                               'Cartier',
                               '宝格丽',
                               '纪梵希',
                               'Givenchy',
                               '爱马仕',
                               '香奈儿',
                               'Hermes']]},
                   {'weight': 4,
                    'words': [['Loewe',
                               'Celine',
                               'Balenciaga',
                               'Chloe',
                               'Dior',
                               'Versace',
                               'Burberry',
                               '阿玛尼',
                               '迪奥',
                               '菲拉格慕',
                               '罗意威',
                               'lululemon']]},
                   {'weight': 3,
                    'words': [['Coach',
                               'Tory Burch',
                               'MCM',
                               '悦诗丽莎',
                               '雅诗兰黛',
                               '兰蔻',
                               '耐克',
                               '阿迪达斯',
                               '匡威',
                               'laprairie']]},
                   {'weight': 2, 'words': [['优衣库', 'H&M', '娇兰佳人', '花西子', 'lamer']]},
                   {'weight': 1, 'words': [['百雀羚']]}]}]
    blacklist = ['业主',
                 '蜜雪冰城隔壁',
                 '蜜雪冰城对面',
                 'SKP附近',
                 'iapm',
                 '代买',
                 '代购',
                 '发布会',
                 '资讯',
                 '合集',
                 '看展',
                 '街拍',
                 '指南',
                 '儿童照',
                 '家居灵感',
                 '明星',
                 '时尚单品',
                 '夏季穿搭',
                 '春夏系列',
                 '春夏穿搭',
                 '新款穿搭',
                 '时尚包包',
                 '夏日穿搭',
                 '时尚穿搭',
                 '极简穿搭',
                 '日常穿搭',
                 '学穿搭',
                 '春季穿搭',
                 '春夏新款',
                 '发箍推荐',
                 '折扣分享',
                 '高级现货',
                 '现货秒发',
                 '配饰分享',
                 '香水分享',
                 '前卫设计',
                 '报名',
                 '线下活动',
                 '工作室',
                 '秀场',
                 '时尚博主',
                 '流行趋势',
                 '今日分享',
                 'vintage',
                 '评测',
                 '帮您',
                 'TED演讲',
                 '关键词',
                 '时髦单品',
                 '艺术中心',
                 '期刊',
                 '招聘',
                 '中的爱马仕',
                 '中的香奈儿',
                 '原单',
                 '原版',
                 '中爱马仕',
                 '首展',
                 '时装',
                 '回收',
                 '高仿',
                 '中古',
                 '成色',
                 '家人们',
                 '宝子',
                 '99新',
                 '公价',
                 '拼手速',
                 '杂志',
                 '找我代',
                 '闲置',
                 '私聊',
                 '福利价',
                 '时尚潮流',
                 '盘点',
                 '全新',
                 '爱马仕橙',
                 '来袭',
                 '吴磊',
                 '林亦扬',
                 '刘亦菲',
                 '推荐分享',
                 '周年',
                 '界的爱马仕',
                 '穿搭灵感',
                 '壁纸',
                 '现货喵发',
                 '爱马仕自行车',
                 '购买攻略',
                 '行情',
                 '细节实拍',
                 '项链推荐',
                 '项链分享']
    threshold = [{'score': 2, 'type': 'hotel'}]
    df = pd.read_csv('./tmp.csv')
    # 如果是expense score 为 [{'score':3,'type':'hotel'}]
    # threshold = [{'score': 1.2, 'type': 'hotel'}, {'score': 1.5, 'type': 'pet'}, {'score': 1.8, 'type': 'dog'}]
    threshold_dict = {item['type']: item['score'] for item in threshold}
    print(threshold_dict)
    print(df[['score', 'keywords']])

    # 调节积分门槛
    # df = df[df['score'] >= threshold]
    # 筛选 score 大于 threshold 中对应 type 的 score 的行

    filtered_df = df[df['score'].apply(lambda scores: any(
        score['type'] in threshold_dict and score['score'] > threshold_dict[score['type']] for score in eval(scores)))]

    print(filtered_df)
