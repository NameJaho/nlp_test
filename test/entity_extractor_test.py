import unittest

import sys
from textwrap import dedent

import pandas as pd
from loguru import logger

from entity.entity_extractor import EntityExtractor

sys.path.append('..')
# from metadata.entity_extractor import EntityExtractor

entity = EntityExtractor()
# 测试数据
test_data = [
    # ("阿里巴巴在大模型领域占据领先地位", {'公司': {'阿里巴巴': 1}, '技术': {'大模k型': 1}}),
    # ("喜茶快要上市了", {'公司': {'喜茶': 1}}),

    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎d牙': 1}, '行业': {'手d游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎d牙': 1}, '行业': {'手游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎牙': 1}, '行业': {'手d游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎牙': 1}, '行业': {'手游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎牙': 1}, '行业': {'手游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎牙': 1}, '行业': {'手游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎牙': 1}, '行业': {'手游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎牙': 1}, '行业': {'手游': 1}}),
    ("手游市场增长，虎牙财报亮眼", {'公司': {'虎牙': 1}, '行业': {'手游': 1}}),
]


class EntityRecognitionError(Exception):
    """Exception for errors in entity recognition."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class EntityExtractorTestCase(unittest.TestCase):

    def test_entity_extractor(self):
        for text, expected_output in test_data:
            with self.subTest(text=text):
                result = entity.extract(text)
                industry_correct = expected_output.get('行业', {}) == result.get('行业', {})
                company_correct = expected_output.get('公司', {}) == result.get('公司', {})
                msg = {
                    "error": "",
                    "text": text,
                    "result": result,
                    "expected_output": expected_output
                }
                try:
                    self.assertEqual(result, expected_output)
                except AssertionError:
                    if not industry_correct and not company_correct:
                        msg['error'] = 'BothError'
                    elif not industry_correct:
                        msg['error'] = 'IndustryError'
                    elif not company_correct:
                        msg['error'] = 'CompanyError'
                    else:
                        msg['error'] = 'UnKnownError'
                    raise EntityRecognitionError(msg)


class CustomTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self.entity_recognition_errors = {i: 0 for i in ['IndustryError', 'CompanyError', 'BothError', 'UnKnownError']}

    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1

        print(f"Test passed: {test.id()}")

    def parse_errors(self):
        for index, error in self.errors:
            print(f'\n' + '* ' * 20)
            print(index)
            print(error)
            for error_type in self.entity_recognition_errors.keys():
                if error_type in str(error):
                    self.entity_recognition_errors[error_type] += 1
            print(f'\n' + '* ' * 20)

    def print_final_result(self):
        total = len(test_data)
        self.parse_errors()

        successes = total - sum(self.entity_recognition_errors.values())
        print(f"Total tests: {total}")
        print(f"Success: {successes}")
        print(f"Entity Recognition Errors: {self.entity_recognition_errors}")  # Print new error type
        print(f"Success rate: {(successes / total) * 100:.2f}%")
        msg = dedent(f"""
        Total tests: {total}
        Success: {successes}
        Entity Recognition Errors: {self.entity_recognition_errors}
        Success rate: {(successes / total) * 100:.2f}%
        """)
        logger.info(msg)


class CustomTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resultclass = CustomTestResult  # Ensure we are using CustomTestResult

    def run(self, test):
        result = super().run(test)
        result.print_final_result()
        return result


def init_dataset():
    df = pd.read_csv('')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(EntityExtractorTestCase)
    runner = CustomTestRunner(verbosity=2)
    runner.run(suite)
