import sys
project_root = "F:\\inter\\nlp_test"
sys.path.append(project_root)
import re
import pandas as pd
import warnings
from word_splitter.word_cutter import WordCutter
from user_profile.profile_service import *
INPUT_FILE = "F:\\inter\\nlp_test\\user_profile\\data\\xhs-T1-40W.csv"
TRAGET_FILE = "F:\\inter\\nlp_test\\my_tools\\combined_labeled_columns_v1.csv"

def process_string(input_string):

    if not isinstance(input_string, str):
        input_string = str(input_string)
# 检查是否是纯中文
    if all('\u4e00' <= char <= '\u9fff' or char.isdigit() for char in input_string):
        return input_string

# 检查是否是纯英文
    if all('a' <= char <= 'z' or 'A' <= char <= 'Z' or char.isdigit() for char in input_string):
        return input_string

# 移除英文字符和标点符号
    cleaned_text = re.sub(r'[^\u4e00-\u9fff]', '', input_string)
    return cleaned_text


df_new = pd.DataFrame(columns=['text', 'brand'])

#读取40w帖子
df = pd.read_csv(INPUT_FILE)
df['text'] = df.apply(lambda x: str(x['title']) + str(x['content']) + str(x['tag_list']), axis=1)

#读取offine和online品牌
df_target = pd.read_csv(TRAGET_FILE)

#对label为0的进行删除除了中文以外字符的操作
df_target['brand'] = df_target.apply(lambda row: process_string(row['offline_brand']) if row['offline_label'] == 0 else row['offline_brand'], axis=1)
#去除空数据
df_target = df_target[~df_target['brand'].isnull()]


#小范围测试，先跑1000看效果
texts_to_process = df['text'].head(1000)


# 遍历 df['text'] 中的每一行
for text in texts_to_process:
    matches = []
    # 检查 text 是否与 df_target['brand'] 中的任何一个值匹配
    for brand in df_target['brand'].astype(str).values:
        if brand == '':
            continue
        if brand in text:
            matches.append(brand)
    if matches:
        # 如果找到匹配,则将 text 和对应的 brand 存入 df_new
        new_row = pd.DataFrame({'text': [text], 'brand': [matches]})
        df_new = pd.concat([df_new, new_row], ignore_index=True)

df_new.to_csv('F:\\inter\\nlp_test\\my_tools\\df_new_offline.csv', index=False)