import yaml
import re
import pandas as pd
import itertools

from pandarallel import pandarallel

pandarallel.initialize()


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


def get_ignore_blacklist(config, domain):
    domain_nicknames_blacklist_yaml = config[domain]['ignore_blacklist']
    domain_nicknames_blacklist = concat_dict(domain_nicknames_blacklist_yaml)
    return domain_nicknames_blacklist


def get_content_whitelist(config, domain='', sub_domain=''):
    if sub_domain:
        cat_content_whitelist_yaml = config[domain][sub_domain]['content_whitelist']
    else:
        cat_content_whitelist_yaml = config[domain]['content_whitelist']
        for category in cat_content_whitelist_yaml:
            if category.get('weight'):
                break
            for key, items in category.items():
                for item in items:
                    item['words'] = list(itertools.chain.from_iterable(item['words']))
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
    mask = ~df['content'].parallel_apply(is_tags_only)

    # 使用这个掩码来过滤DataFrame
    df_filtered = df[mask]

    # 重置索引
    df_filtered = df_filtered.reset_index(drop=True)

    # 移除正文中的标签
    df_filtered['content'] = df_filtered.parallel_apply(remove_tag_list, axis=1)

    return df_filtered


def load_data(input_file, file_format='csv'):
    if file_format == 'csv':
        df = pd.read_csv(input_file)
    elif file_format == 'xlsx':
        df = pd.read_excel(input_file)
    elif file_format == 'pkl':
        df = pd.read_pickle(input_file)

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
    df_biz_user = df[df['nickname'].parallel_apply(lambda x: any(word.upper() in x.upper() for word in word_list))]
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


def filter_by_score(df, content_whitelist, content_blacklist, ignore_blacklist=None, threshold=None):
    df['text'] = df.parallel_apply(lambda x: str(x['title']) + str(x['content']) + str(x['tag_list']), axis=1)
    if threshold:
        df[['score', 'keywords']] = df.parallel_apply(
            lambda x: calculate_score(x['text'], content_whitelist, content_blacklist),
            axis=1, result_type='expand')
        # 调节积分门槛
        df = df[df['score'] >= threshold]
    else:
        df[['score', 'keywords']] = df.parallel_apply(
            lambda x: calculate_score_v2(x['text'], content_whitelist, content_blacklist, ignore_blacklist),
            axis=1, result_type='expand')
        df = df[df['score'].parallel_apply(lambda x: any(i['score'] > 0 for i in x))]
        df['score'] = df['score'].parallel_apply(lambda x: [i for i in x if i['score'] != 0])

    return df


def filter_ignore_list(text, word, ignore_blacklist, keywords, weight, verbose):
    index = text.upper().find(word.upper())
    near = text[index - 5:index + len(word) + 5]

    if any(i.upper() in near.upper() for i in ignore_blacklist):
        # confuses = [i for i in ignore_blacklist if i.upper() in near.upper()]
        print(f'***[{word}] [{near}] ')
        return False

        # drop keyword which is contained by any keyword
    if any([word in i for i in keywords]):
        return False

    if verbose:
        print(f'*** whitelist matched:{word}[{weight}]')
    # return word, score
    return True


def calculate_score_v2(text, whitelist, blacklist, ignore_blacklist, verbose=False):
    score_list = []
    keywords = []
    ignore_blacklist = [] if ignore_blacklist is None else ignore_blacklist

    # if blacklist matched, score 0 and return
    if any(word in text for word in blacklist):
        return [{'score': 0, 'type': ''}], []

    # whitelist score accumulation
    for item in whitelist:
        # 非消费
        for type_, term in item.items():  # 'hotel',[{'weight':xx,'words':[[]]}]
            score = 0
            for term_ in term:
                weight = term_['weight']
                for word in term_['words']:
                    base_word = word.split('|')
                    if base_word[0].upper() not in text.upper():
                        continue

                    if len(base_word) == 1:
                        flag = filter_ignore_list(text, word, ignore_blacklist, keywords, weight, verbose)
                        if not flag:
                            continue

                        score = weight if weight > score else score
                        keywords.append(word)
                    else:
                        others = base_word[1:]
                        if any(i in text.upper() for i in others):
                            flag = filter_ignore_list(text, word, ignore_blacklist, keywords, weight, verbose)
                            if not flag:
                                continue

                            score = weight if weight > score else score
                            kw = base_word[0] + '|' + '|'.join([i for i in others if i.upper() in text.upper()])
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


# find tag; true or false


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


def filter_user_by_type(df_user, count):
    df_user['unique_type'] = df_user['score'].apply(lambda x: list(set([i['type'] for i in x])))
    df_user['type_cnt'] = df_user['unique_type'].apply(lambda x: len(x))
    return df_user[df_user['type_cnt'] >= count]


if __name__ == '__main__':
    # calculate_score('什么汽车', [{'weight': 1, "words": [['汽车', '车']]}], [], verbose=True)
    whitelist = [
        {'hotel': [{'weight': 10,
                    'words': [
                        ['四季酒店', '丽思卡尔顿隐世', '文华东方', '安缦', '悦榕庄', '文华东方', '宝格丽酒店'],
                        ['隐世酒店', '六善', '璞富腾'],
                        ['崇左秘境丽世度假村', '碧玥酒店', '东驿敦煌酒店', '响沙湾莲花酒店']]},
                   {'weight': 8,
                    'words': [['洲际', '半岛酒店', '瑞吉', 'W酒店', '君悦'],
                              ['丽思卡尔顿',
                               '艾迪逊',
                               'JW万豪',
                               '华尔道夫',
                               '康莱德',
                               '莱佛士',
                               '悦榕庄',
                               '索菲特传奇',
                               '费尔蒙',
                               '宋品',
                               '嘉佩乐'],
                              ['四季酒店',
                               '瑰丽',
                               '美高梅',
                               '香樟华苹',
                               '博舍',
                               '安麓',
                               '璞丽',
                               '钓鱼台酒店',
                               '尼依格罗',
                               'Club Med',
                               'ClubMed',
                               '柏联',
                               '松赞'],
                              ['画山云舍', '悦榕庄', '糖舍|度假酒店', '潼乡|度假酒店', '在野宿集']]},
                   {'weight': 6,
                    'words': [['万怡',
                               '德尔塔',
                               'AC酒店',
                               '福朋喜来登',
                               '皇冠假日',
                               'VOCO',
                               '华邑',
                               '逸衡',
                               '凯悦尚萃',
                               '凯悦悠选',
                               '美爵',
                               '美居',
                               '诗铂',
                               '美憬阁'],
                              ['诺富特', '希尔顿逸林', '希尔顿花园', '施柏阁', '美居', '美伦美奂', '花间堂',
                               '万达文华', '万达嘉华'],
                              ['白公馆', '云舞|度假酒店|阳朔', '河畔|度假酒店|阳朔', '水印长廊|酒店']]},
                   {'weight': 4, 'words': [['亚朵']]},
                   {'weight': 3,
                    'words': [['喜达屋',
                               'Moxy',
                               '普罗蒂亚',
                               '万枫',
                               '雅乐轩',
                               '源宿',
                               '假日酒店',
                               '智选假日',
                               '逸扉',
                               '凯悦嘉轩',
                               '希尔顿欢朋',
                               '桔子水晶',
                               '漫心'],
                              ['华美达', '亚朵', '万达嘉华']]},
                   {'weight': 1,
                    'words': [['锦江之星'],
                              ['凯悦嘉寓',
                               '宜必思',
                               '惠庭',
                               '汉庭',
                               '星程',
                               '海友',
                               '汉庭优佳',
                               '如家',
                               'Days Inn',
                               '万达锦华',
                               '希岸deluxe',
                               '丽枫',
                               '七天|酒店',
                               '新维也纳'],
                              ['维也纳国际',
                               '维纳斯皇家',
                               '凯里亚德',
                               '锦江都城',
                               '喆啡',
                               '云居',
                               '潮漫酒店',
                               '康铂',
                               '白玉兰',
                               '欧瑕.地中海',
                               '欧瑕地中海',
                               '郁锦香酒店',
                               '丽柏'],
                              ['丽怡',
                               'ZMAX满兮',
                               '非繁城品',
                               '7天优品',
                               '格林豪泰',
                               '如家精选',
                               '速8',
                               '都市118',
                               '尚客优',
                               '富驿时尚',
                               '铂涛特品',
                               '瑞享',
                               '99旅馆',
                               '铂尔曼'],
                              ['美豪', '汉庭', '原拓', '城市便捷']]}]},
        {'restaurant': [{'weight': 10, 'words': [['怀石料理', '米其林', '大董']]},
                        {'weight': 7, 'words': [['毋米粥', '星巴克', 'shake shack', 'Wagas']]},
                        {'weight': 3, 'words': [['九毛九']]},
                        {'weight': 1, 'words': [['兰州拉面', '千里香馄炖', '蜜雪冰城']]}]},
        {'supermarket': [{'weight': 8,
                          'words': [['Whole Foods', 'BLT', 'City Super']]},
                         {'weight': 5, 'words': [['盒马', '七鲜', 'ALDI', 'LIDL']]}]},
        {'brand': [{'weight': 10, 'words': [['爱马仕｜包｜鞋', 'Hermes｜包｜鞋']]},
                   {'weight': 9,
                    'words': [['卡地亚',
                               'Cartier',
                               '宝格丽',
                               '纪梵希',
                               'Givenchy',
                               '香奈儿｜包|鞋',
                               '巴黎世家',
                               'Balenciaga',
                               '杰尼亚',
                               'Zegna',
                               '博柏利',
                               'Burberry',
                               'LV|包',
                               '普拉达',
                               'Prada',
                               'Bottega veneta',
                               'Rimowa ',
                               '普拉达',
                               'Prada'],
                              ['华伦天奴', 'Valentino', '古驰', 'Gucci']]},
                   {'weight': 8,
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
                               'lululemon',
                               'laprairie'],
                              ['浪凡',
                               'Lanvin',
                               'HOGAN',
                               '沙驰',
                               'Satchi',
                               'Michael Kors',
                               '其乐',
                               'Clarks',
                               '爱步',
                               'Ecco',
                               'Hush Huppies',
                               '暇步士',
                               '73小时',
                               '阿玛尼',
                               'armani',
                               'Y-3',
                               '范思哲',
                               'Versace'],
                              ['Lululemon', 'Lulu lemon', '始祖鸟', 'Arcteryx']]},
                   {'weight': 6,
                    'words': [['爱马仕｜丝巾|香水'],
                              ['Coach',
                               '蔻驰',
                               'Tory Burch',
                               '汤丽柏琦',
                               'MCM',
                               '悦诗丽莎',
                               '雅诗兰黛',
                               '兰蔻',
                               '耐克',
                               'Nike',
                               '阿迪达斯',
                               'Adidas',
                               '匡威',
                               'lamer',
                               'Lacoste',
                               '健乐士',
                               'Geox',
                               '乐步',
                               'Rockport',
                               '亚瑟士',
                               'Asics',
                               '斐乐',
                               'Fila',
                               '萨洛蒙',
                               'Salomon'],
                              ['北面',
                               '鬼塚虎',
                               'Onitsuka',
                               '迪桑特',
                               'Descente',
                               '万宝龙',
                               'Montblanc',
                               '途明',
                               'Tumi',
                               '新秀丽',
                               'Samsonite',
                               '迪赛',
                               'Diesel',
                               '昂跑',
                               'UGG']]},
                   {'weight': 5,
                    'words': [['迪奥｜丝巾|香水', '香奈儿｜丝巾|香水'],
                              ['优衣库',
                               '匡威',
                               'Converse',
                               '迪卡侬',
                               'Decathlon',
                               '无印良品',
                               '添柏岚',
                               'Timberland',
                               '百思图',
                               '思加图',
                               '接吻猫',
                               '星期六',
                               'MCM',
                               '哥伦比亚',
                               'Columbia',
                               '百丽']]},
                   {'weight': 4,
                    'words': [['H&M',
                               '娇兰佳人',
                               '花西子',
                               '大嘴猴',
                               '莫斯奇诺',
                               'Moschino',
                               '李宁',
                               'Lining',
                               '安踏',
                               'Anta',
                               '美津浓',
                               'Mizuno',
                               '迪桑娜',
                               'CHARLES&KEITH']]},
                   {'weight': 3,
                    'words': [['斯凯奇',
                               '达芙妮',
                               '卓诗尼',
                               '金利来',
                               '锐步',
                               'Reebok',
                               '彪马',
                               'Puma',
                               '乐途',
                               'Lotto',
                               '不莱玫']]},
                   {'weight': 2,
                    'words': [['回力',
                               '奥古狮登',
                               '三福',
                               '人本｜鞋',
                               '木林森',
                               '奥康',
                               '卡帝乐',
                               '南极人',
                               '花路仕',
                               '海澜之家',
                               '意尔康',
                               '足力健',
                               '稻草人|鞋',
                               '花花公子',
                               'ULDUM',
                               '特步',
                               'Xtep',
                               '鸿星尔克',
                               'Erke',
                               '匹克',
                               'Peak',
                               '361度',
                               '卡帕',
                               'Kappa']]},
                   {'weight': 1, 'words': [['百雀羚']]}]},
        {'milk': [{'weight': 7, 'words': [['朝日唯品', 'a2']]},
                  {'weight': 6,
                   'words': [['香满楼',
                              '简爱酸奶',
                              '金典',
                              '悦鲜活',
                              '认养一头牛',
                              '北海牧场',
                              '卡士',
                              '特仑苏',
                              '优诺',
                              '吾岛',
                              '圣牧',
                              '新希望|奶']]},
                  {'weight': 5,
                   'words': [['伊利',
                              '蒙牛',
                              '每日鲜语',
                              '君乐宝',
                              '简醇',
                              '天润',
                              '光明|奶',
                              '德亚',
                              '三元|奶',
                              '欧亚|奶']]},
                  {'weight': 1, 'words': [['燕塘', '花花牛', '真零', '兰格格', '西域春', '味全']]}]},
        {'bicycle': [{'weight': 10,
                      'words': [['崔克',
                                 'Specialized',
                                 'Brompton',
                                 '小布|自行车|山地车|公路车|单车',
                                 '闪电|自行车|山地车|公路车|单车']]},
                     {'weight': 6,
                      'words': [['捷安特',
                                 '迪卡侬|自行车|山地车|公路车|单车',
                                 '佳沃|自行车|山地车|公路车|单车',
                                 '喜德盛|自行车|山地车|公路车|单车',
                                 '大行|自行车|山地车|单车｜折叠']]},
                     {'weight': 2,
                      'words': [['凤凰|自行车|山地车|公路车|单车',
                                 '永久|自行车|山地车|公路车|单车',
                                 '菲利普|自行车|山地车|公路车|单车',
                                 '飞鸽|自行车|山地车|公路车|单车']]}]}]
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
                 '原单',
                 '原版',
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
                 '来袭',
                 '吴磊',
                 '林亦扬',
                 '刘亦菲',
                 '推荐分享',
                 '周年',
                 '穿搭灵感',
                 '壁纸',
                 '现货喵发',
                 '购买攻略',
                 '行情',
                 '细节实拍',
                 '项链推荐',
                 '项链分享',
                 '每日穿搭',
                 '大揭密']
    ignore_blacklist = ['隔壁', '楼下', '附近', '楼上', '旁边', '对面', '中的']
    df = pd.read_csv('./cleanup_5w_users.csv')

    df_filtered = filter_by_score(df, whitelist, blacklist, ignore_blacklist)
    print(df_filtered[['text', 'score', 'keywords']].__len__())
