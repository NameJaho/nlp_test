from dashscope import Application


class Qwen:

    def generate(self, messages):
        # 目前是max 如果需要改模型 需要线上改
        response = Application.call(app_id='5fc245471197441484693ea2eb51cd40',
                                    api_key='sk-1ab414c07a774b16b821c4b94a3226a4',
                                    prompt=messages,
                                    )
        return response.output['text'].replace('```json\n', '').replace('```', '').replace('\n', '')
