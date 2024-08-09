import sys
project_root = "F:\\inter\\nlp_test"
sys.path.append(project_root)
import re
import pandas as pd
import warnings
from user_profile.profile_service import *
warnings.filterwarnings('ignore')
OFFLINE_FILE = "F:\\inter\\nlp_test\\my_tools\\offline100_300.xlsx"
ONLINE_FILE = "F:\\inter\\nlp_test\\my_tools\\240805_天猫品牌销额2405月份数据统计_v2_cut.xlsx"

def label_string(input_string):
    if not isinstance(input_string, str):
        input_string = str(input_string)
    
    # Check if the string is pure Chinese (allowing numbers)
    if all('\u4e00' <= char <= '\u9fff' or char.isdigit() for char in input_string):
        return 1
    
    # Check if the string is pure English (allowing numbers)
    if all('a' <= char <= 'z' or 'A' <= char <= 'Z' or char.isdigit() for char in input_string):
        return 2
    
    # Mixed or other types
    return 0

df_offline = pd.read_excel(OFFLINE_FILE)
df_online = pd.read_excel(ONLINE_FILE)

df_offline['label'] = df_offline['brand'].apply(label_string)
df_online['label'] = df_online['out_brand'].apply(label_string)

combined_df = pd.DataFrame({
    'offline_brand': df_offline['brand'],
    'offline_label': df_offline['label'],
    'offline_cat1' : df_offline['cat1'],
    'offline_cat2' : df_offline['cat2'],
    'offline_cat3' : df_offline['cat3'],
    'online_brand': df_online['out_brand'],
    'online_label': df_online['label']
})

combined_df.to_csv('combined_labeled_columns_v1.csv', index=False)