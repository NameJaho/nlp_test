import os
from tqdm import tqdm
import pandas as pd
from tools.utils import get_root_path
from llms.llm import ChatLlm

INPUT_FILE="llm_prompt_evaluator_test.csv"
OUTPUT_FILE="llm_prompt_evaluator_output.csv"
SYSTEM_PROMPT_DEEPSEEK = """
     你是DeepSeek V2 Chat，一个乐于助人且注重安全的语言模型。你会尽可能的提供详细、符合事实、格式美观的回答。
     请作为一位专业的数据分析员，根据以下标准对给定的Query和Summary进行相关性评估，同样的问题多次回答必须保持一致，不要随意修改答案。
    """

SYSTEM_PROMPT_QWEN = """
     你是QWEN2 Chat，一个乐于助人且注重安全的语言模型。你会尽可能的提供详细、符合事实、格式美观的回答。
     请作为一位专业的数据分析员，根据以下标准对给定的Query和Summary进行相关性评估，同样的问题多次回答必须保持一致，不要随意修改答案。
    """

class Label_evaluator:
    def __init__(self):
        self.input_file_path = os.path.join(get_root_path(), 'embedding/input', INPUT_FILE)
        self.output_file_path = os.path.join(get_root_path(), 'embedding/output', OUTPUT_FILE)

    @staticmethod
    def build_user_prompt(template, query, doc):
        return template.format(query=query, doc=doc)

    def score(self, query, doc, prompt_path, llm_name):
        llm=ChatLlm(llm_name) 
        with open(prompt_path, 'r',encoding='utf-8') as file:
            prompt_template = file.read()
        user_prompt = self.build_user_prompt(prompt_template, query, doc)

        if llm_name == 'ds':
            response = str(llm.generate(user_prompt, system_prompt=SYSTEM_PROMPT_DEEPSEEK))
        else:
            response = str(llm.generate(user_prompt, system_prompt=SYSTEM_PROMPT_QWEN))
        score = int(response.split(": ")[1].split(",")[0])
        return(score)

    def process(self, model_list, prompt_list):
        accuracy=[]
        df = pd.read_csv(self.input_file_path)
        for i in range(len(model_list)):
            for j in range(len(prompt_list)):
                accuracy_count=0
                for index, row in df.iterrows():
                    query = row['query']
                    doc = row['doc']
                    label = row['custom_label']
                    if pd.notnull(query) and pd.notnull(doc):
                        test_score = self.score(query, doc, prompt_list[j], model_list[i])
                        llm_prompt_name = str(model_list[i]) +'+prompt' + str(j+1)
                        if test_score == label:
                            accuracy_count+=1
                        df.at[index, llm_prompt_name] = test_score
                accuracy.append(llm_prompt_name+':'+ str((accuracy_count/len(df['custom_label']))*100) +'%')
        print(accuracy)
        df.to_csv(self.output_file_path)

if __name__ == '__main__':
    model_list=['ds','qwen2']
    prompt_list=['F:\\inter\\nlp_test\\llms\\prompt\\similar_judge_deepseek.txt']
    le=Label_evaluator()
    le.process(model_list, prompt_list)
    print('处理完成')
