import random

import openai
from loguru import logger
from openai import OpenAI


# from utils.wrapper import catch


class DeepSeek:

    def __init__(self):
        self.api_key = 'sk-a03389979dc14f7bb714ecdb49a55a47,sk-450ced789d334effb70368f69ab531dd, sk-7238d8c95772437d9a99ebc65186c5be, sk-07c7d4f888d04084a5d5af4c80c0ef8f, sk-c65200fe06c04cfc87139969ccbf3953'.split(
            ',')

    def generate(self, messages, system_prompt):
        client = OpenAI(api_key='sk-da27af325d294d8087c31fc0907b5322', base_url="https://api.deepseek.com")
        response = client.chat.completions.create(

            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": messages},
            ],
            # messages=[
            #     {"role": "system",
            #      "content": system_prompt},
            #     {"role": "user", "content": user_prompt},
            # ],
            # stream=False,
            temperature=0.1,
            # top_p=0.1
        )
        return response.choices[0].message.content
