import pandas as pd
from tools.utils import get_root_path
import os
from llms.llm import ChatLlm


SYSTEM_PROMPT_DEEPSEEK = """
     你是DeepSeek V2 Chat，一个乐于助人且注重安全的语言模型。你会尽可能的提供详细、符合事实、格式美观的回答。
     请作为一位专业的数据分析员，根据以下标准对给定的Query和Summary进行相关性评估，同样的问题多次回答必须保持一致，不要随意修改答案。
    """

SYSTEM_PROMPT_QWEN = """
"""


root_path = get_root_path()
file_name = 'similarity_300_labels_validation.csv'
outputfile_name='similarity_300_labels_validation_test_output.csv'
file_path = os.path.join(root_path, 'test/data', file_name)
outputfile_path=os.path.join(root_path, 'test/output', outputfile_name)
prompt_path = os.path.join(root_path, 'llms/prompt', 'similar_judge_deepseek.txt')

df = pd.read_csv(file_path)
llm = ChatLlm('ds')

with open(prompt_path, 'r') as file:
    prompt_template = file.read()


def build_user_prompt(template, query, doc):
    return template.format(query=query, doc=doc)


def score(query, doc):
    user_prompt = build_user_prompt(prompt_template, query, doc)
    response = llm.generate(user_prompt, system_prompt=SYSTEM_PROMPT_DEEPSEEK)
    print(response)
    score = int(response.split(": ")[1].split(",")[0])
    return(score)


# df_head = df.iloc[14:22]
# iterate df_head
for index, row in df.iterrows():
    query = row['sentence1']
    doc = row['sentence2']
    if pd.notnull(query) and pd.notnull(doc):
        test_score = score(query, doc)
        df.at[index,'test_score'] = test_score
df.to_csv(outputfile_path)