import random
from http import HTTPStatus
import dashscope

dashscope.api_key = 'sk-1ab414c07a774b16b821c4b94a3226a4'


class Qwen2:

    def generate(self, messages, system_prompt):
        messages = [{"role": "user", "content": messages}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        response = dashscope.Generation.call(
            # 'qwen2-1.5b-instruct',
            'qwen2-0.5b-instruct',
            # 'qwen1.5-72b-chat',
            messages=messages,
            result_format='message',  # set the result to be "message" format.
            temperature=0.1
        )
        return response['output']['choices'][0]['message']['content'].replace('```json\n', '').replace('```',
                                                                                                       '').replace('\n',
                                                                                                                   '')
