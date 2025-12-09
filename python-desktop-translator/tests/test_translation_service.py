import unittest
from src.services.translation_service import TranslationService

class TestTranslationService(unittest.TestCase):

    def setUp(self):
        self.translation_service = TranslationService()

    def test_translate_text(self):
        result = self.translation_service.translate("Hello, world!", "zh_CN")
        self.assertEqual(result, "你好，世界！")  # Assuming this is the expected translation

    def test_translate_empty_text(self):
        result = self.translation_service.translate("", "zh_CN")
        self.assertEqual(result, "")  # Expecting empty string for empty input

    def test_translate_invalid_language(self):
        with self.assertRaises(ValueError):
            self.translation_service.translate("Hello", "invalid_lang")

    def test_translate_with_special_characters(self):
        result = self.translation_service.translate("Hello @#$%^&*()", "zh_CN")
        self.assertEqual(result, "你好 @#$%^&*()")  # Assuming this is the expected translation

if __name__ == '__main__':
    unittest.main()