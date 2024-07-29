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
    df_biz_user = df[df['nickname'].apply(lambda x: any(word in x for word in word_list))]
    df_normal_user = df[~df['user_id'].isin(df_biz_user['user_id'])]
    return df_normal_user


# 计算总积分
def calculate_score(text, whitelist, blacklist, verbose=False):
    score = 0
    keywords = []

    # if blacklist matched, score 0 and return
    if any(word in text for word in blacklist):
        return 0

    # whitelist score accumulation
    for item in whitelist:
        weight = item['weight']
        for word_list in item['words']:
            for word in word_list:
                if word in text:
                    if verbose:
                        print(f'*** whitelist matched:{word}[{weight}')
                    score += weight
                    keywords.append(word)
    return score, keywords


def filter_by_score(df, content_whitelist, content_blacklist, threshold):
    df['text'] = df.apply(lambda x: str(x['title']) + str(x['content']) + str(x['tag_list']), axis=1)
    df[['score', 'keywords']] = df.apply(lambda x: calculate_score(x['text'], content_whitelist, content_blacklist),
                                         axis=1, result_type='expand')

    # 调节积分门槛
    df = df[df['score'] >= threshold]
    return df


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
