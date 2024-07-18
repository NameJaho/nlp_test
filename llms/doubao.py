from openai import OpenAI


class DouBao:

    def __init__(self, llm_type):
        self.model = "ep-20240718071043-7h6bx" if llm_type =='moonshot' else "ep-20240718071014-2fjhp"

    def generate(self, messages, system_prompt):
        client = OpenAI(api_key='b8e0405b-dfed-4f44-8c0e-18af6c702484',
                        base_url="https://ark.cn-beijing.volces.com/api/v3")
        response = client.chat.completions.create(
            model=self.model,
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
