import openai
from loguru import logger
from openai import OpenAI


# from utils.wrapper import catch


class Azure:

    def __init__(self, api_version, api_key, api_base, engine):
        # openai.api_version = api_version
        # openai.api_type = "azure"
        # openai.api_key = api_key
        # openai.api_base = api_base
        self.api_version = api_version
        self.api_base = api_base
        self.api_key = api_key
        self.engine = engine
        self.client = openai.AzureOpenAI(
            azure_endpoint=self.api_base,
            api_key=self.api_key,
            api_version=self.api_version
        )

    def generate_pre(self, messages, system_prompt=None):
        """
            openai==0.28.0
        """

        messages = [{"role": "user", "content": messages}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        response = openai.ChatCompletion.create(
            engine=self.engine,
            messages=messages,
            temperature=0.0,
            top_p=0.0,
        )
        if response.choices[0].message.get("content", None) is None:
            logger.error(response)
        return response.choices[0].message.get("content", None)

    def generate(self, messages, system_prompt=None):
        """
            openai > 1.x
            https://learn.microsoft.com/en-us/azure/ai-services/openai/chatgpt-quickstart?tabs=command-line%2Cpython-new&pivots=programming-language-python
        """
        messages = [{"role": "user", "content": messages}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        response = self.client.chat.completions.create(

            model=self.engine,
            messages=messages,
            temperature=0.1,
            # top_p=0.1
        )
        return response.choices[0].message.content
