import re
import unittest

import sys
from textwrap import dedent

import pandas as pd
from loguru import logger

from entity.entity_extractor import EntityExtractor

sys.path.append('..')

entity = EntityExtractor()
# 测试数据
df = pd.read_csv('test/data/query_validation_label_v1.csv')


# df = df[:10]


class EntityRecognitionError(Exception):
    """Exception for errors in entity recognition."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class EntityExtractorTestCase(unittest.TestCase):
    def setUp(self):
        self.df = df

    def test_entity_extractor(self):
        # for text, expected_output in test_data:
        for index, value in self.df.iterrows():
            id_, text, expected_output = value['t'], str(value['搜索词']), eval(value['intent_who'])
            o_expected = expected_output
            with self.subTest(text=text):
                result = entity.extract(text)
                result = entity.format(result)  # strict
                o_result = result
                if mode == 'strict':
                    pass
                else:
                    result = entity.cut_entity(result)
                    expected_output = entity.cut_entity(expected_output)

                msg = {
                    # "error": "intent who error",
                    "text": text,
                    "result": o_result,
                    "expected_output": o_expected,
                    "id_": id_
                }
                try:
                    self.assertEqual(sorted(result), sorted(expected_output))
                except AssertionError:
                    raise EntityRecognitionError(msg)


class CustomTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self.entity_recognition_errors = {'EntityRecognitionError': 0}
        self.error_entity = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1

        print(f"Test passed: {test.id()}")

    def parse_errors(self):
        for index, error in self.errors:
            # print(f'\n' + '* ' * 20)
            # print(index)
            # print(error)
            for error_type in self.entity_recognition_errors.keys():
                if error_type in str(error):
                    self.entity_recognition_errors[error_type] += 1
            entity_error_msg = re.findall('EntityRecognitionError: (.*?\n)', error)[0]
            # print(entity_error_msg)
            self.error_entity.append(entity_error_msg)
            # print(f'\n' + '* ' * 20)

    def print_final_result(self):
        total = len(df)
        self.parse_errors()
        successes = total - sum(self.entity_recognition_errors.values())
        msg = dedent(f"""
        Total tests: {total}
        Success: {successes} 
        Strict Precision Rate: {(successes / total) * 100:.2f}%
        Error Items:
        """)
        # Entity Recognition Errors: {self.entity_recognition_errors}
        msg += ''.join([i for i in self.error_entity])
        # print(msg)
        logger.info(msg)


class CustomTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resultclass = CustomTestResult  # Ensure we are using CustomTestResult

    def run(self, test):
        result = super().run(test)
        result.print_final_result()
        return result


if __name__ == '__main__':
    # mode = 'loose'
    mode = 'strict'
    suite = unittest.TestLoader().loadTestsFromTestCase(EntityExtractorTestCase)
    runner = CustomTestRunner(verbosity=2)
    runner.run(suite)
