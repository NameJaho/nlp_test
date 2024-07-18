# -*- coding: utf-8 -*-
import configparser
import json
import os
import time
from json import JSONDecodeError

from loguru import logger

from llms.deepseek import DeepSeek
from llms.doubao import DouBao

from llms.qwen_v2 import Qwen2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ChatLlm:
    def __init__(self, llm, ini=os.path.join(BASE_DIR, '../config/config.ini')):
        self.config = configparser.ConfigParser()
        self.config.read(ini, encoding="utf-8")
        self.llm = self.init_llm(llm)

    @staticmethod
    def init_llm(llm_type):
        if llm_type.startswith("qwen2"):
            llm = Qwen2()
        # elif llm_type.startswith("qwen"):
        #     key = self.config.get(llm_type, "appid")
        #     llm = Qwen(key)
        elif llm_type.startswith("ds"):
            llm = DeepSeek()
        elif llm_type.startswith("doubao"):
            llm = DouBao("doubao")
        elif llm_type.startswith("moonshot"):
            llm = DouBao("moonshot")
        else:
            raise Exception("llms type error")
        return llm

    def generate(self, messages, system_prompt=None):
        """
        :param llm_type: gpt3.5 or gpt4 or azure
        :param messages: [{"role": "user", "content": "写一个hello world程序"}]
        :return:
        """
        analysis_response = ""

        try:
            analysis_response = self.llm.generate(messages, system_prompt)
            if isinstance(analysis_response, str):
                json_response = json.loads(analysis_response)
            else:
                json_response = analysis_response
        except JSONDecodeError:
            json_response = analysis_response.replace('```json\n', '').replace('```', '')

        except Exception as e:
            import traceback
            logger.info(traceback.print_exc())
            return None
        return json_response


if __name__ == '__main__':
    obj = ChatLlm('doubao')

    system_prompt = """
Use Semantic Ontology & Knowledge Graph. Think Step by Step. Step 1: Create Tagline {T} and Précis {P} from {Content} Relevant to {Query}. Step 2: Derive [FOUR] Aspect {X} Relevant to {Query} from {Content}. Be Categorical & Succinct. Step 3: Derive COMPLETE Knowledge Graph {KG} for Each {X}. Annotate {Subject}, Sentiment {S} on Syntax-Coherent Sententces of Verbatim {V}, and Extract Signifier_Term {K} from Verbatim {V} ONLY IF Available & Applicable. Step 4: Extract All Proper Name {PRN} from {Content}. Annotate Geographical_Name {GN}, Person_Name {PN}, Company_Name {CN}, Brand & Product_Name {BN}. Be Specific & Meticulous.\r\nOutput in JSON Syntax:\r\n{\r\n    \"T\": \"\",\r\n    \"P\": \"\",\r\n    \"X\": [\"\"],\r\n    \"KG\": [\r\n        {\r\n            \"X\": \"\",\r\n            \"Subject\": \"\",\r\n            \"V\": [\"\"],\r\n            \"S\": [\"\"],\r\n            \"K\": [\"\"]\r\n        },\r\n    ]\r\n    \"PRN\": {\r\n        \"GN\": [\"\"],\r\n        \"PN\": [\"\"],\r\n        \"CN\": [\"\"],\r\n        \"BN\": [\"\"],\r\n        \"Other\": [\"\"]\r\n    }\r\n}.\r\nOutput Language = 简体中文. Be Thoughtful & Exhaustive.
    """
    user_prompt = """
    {Content} = 以下为2023/10/29的研报中部分内容：
Q3收入稳步增长，期待Q4表现。
华泰研究2023年10月29日中国内地。
Q3营收同增6.03%， 维持“增持”评级公司发布三季报， 23Q1-Q3实现营收60.69亿元（yoy+5.71%）， 归母净利3.90亿元（yoy+0.33%）， 扣非净利3.80（yoy+4.19%)。 其中Q3实现营收22.64亿元（yoy+6.03%)， 归母净利1.68亿元（yoy-0.79%)。 在行业需求仍面临压力的背景下， 公司推动品类及渠道开拓， 营收仍实现稳步增长。 考虑到需求尚处恢复期， 我们下调各项业务收入预测， 预计23-25年归母净利润分别为5.27/6.16/7.13亿元（前值5.31/7.00/9.17亿元）。 对应EPS分别为1.36/1.59/1.84元。 参考可比公司23年Wind一致预期PE均值为16倍， 考虑公司渠道扩张节奏领先同业， 给予公司23年20倍PE， 目标价27.20元（前值31.51元)， 维持“增持”评级。
23Q1-3喜临门品牌线下零售收入同增4%， 线上收入同增18%分业务看， 23Q1-3自主品牌零售业务营收同增4%至40.1亿元， 其中线下渠道建设稳步推进， 截止23Q3喜临门/喜眠/M&D（含夏图） 门店分别达3496/1585/556家， 合计较年初净增364家， 23Q1-3线下零售收入28.4亿元， 同比略降1%（其中喜临门品牌线下零售同增4%至25.5亿元）； 同时，公司推动线上多渠道+多品类运营， 23Q1-3线上收入同增18%至11.7亿元。 此外，23Q1-3自主品牌工程收入同增11%至2.8亿元， 代加工业务收入同增8%至17.7亿元， 均保持稳步增长。
前三季度销售毛利率同比提升0.78pct， 经营性净现金流同比明显改善23Q1-3销售毛利率同增0.78pct至34.2%， 我们判断主要系供应链管理水平提升及原料成本下行所致； 23Q1-3期间费用率同增1.84pct至26.6%， 其中销售费用率同增1.95pct至19.1%， 主要系广告宣传费、网销费用及销售渠道费等费用增加所致； 管理+研发费用率同增0.19pct至7.4%； 财务费用率同降0.30pct至0.18%， 主要系汇兑收益及利息收入增加所致。 此外，23Q1-3公司经营性净现金流为1.55亿元， 去年同期为0.17亿元， 经营性净现金流同比大幅改善， 主要系本期回款增加、支付采购材料款减少所致。.\n{Query} = 24年线上零售市场的变化.
    """

    result = obj.generate(user_prompt, system_prompt=system_prompt)
    print(f"{result}")

