import unittest
import html
import re
from telegram_handlers import _format_telegram_message


class TestTelegramFormatting(unittest.TestCase):

    def test_bold_conversion(self):
        """Test that **text** is converted to <b>text</b>."""
        input_text = "This is **bold** text."
        expected = "This is <b>bold</b> text."
        result = _format_telegram_message(input_text)
        self.assertEqual(result, expected)

    def test_multiple_bold(self):
        """Test multiple bold sections."""
        input_text = "**First** and **second** bold."
        expected = "<b>First</b> and <b>second</b> bold."
        result = _format_telegram_message(input_text)
        self.assertEqual(result, expected)

    def test_html_escaping(self):
        """Test that HTML characters are escaped."""
        input_text = "Text with <script> and **bold**."
        expected = "Text with &lt;script&gt; and <b>bold</b>."
        result = _format_telegram_message(input_text)
        self.assertEqual(result, expected)

    def test_no_bold(self):
        """Test text without bold markers."""
        input_text = "Plain text without formatting."
        expected = "Plain text without formatting."
        result = _format_telegram_message(input_text)
        self.assertEqual(result, expected)

    def test_empty_string(self):
        """Test empty string."""
        input_text = ""
        expected = ""
        result = _format_telegram_message(input_text)
        self.assertEqual(result, expected)

    def test_nested_asterisks(self):
        """Test that single * are not converted."""
        input_text = "Italic *text* but **bold**."
        expected = "Italic *text* but <b>bold</b>."
        result = _format_telegram_message(input_text)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()