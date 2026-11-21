import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import translate

class TranslateTests(unittest.TestCase):
    def test_get_output_returns_translation(self):
        original_argv = sys.argv[:]
        try:
            sys.argv = ['workflow.py', 'hello', 'en', 'fr']
            feedback = translate.get_output('hello')
            titles = [item.find('title').text for item in feedback.feedback.findall('item')]
            self.assertTrue(any('Bonjour' in title for title in titles))
        finally:
            sys.argv = original_argv

    def test_http_error_is_silent(self):
        with patch('urllib.request.urlopen', side_effect=urllib.error.HTTPError('https://example.com', 403, 'Forbidden', hdrs=None, fp=None)):
            with patch('sys.stdout', new_callable=io.StringIO) as stdout:
                result = translate.process_response_as_json('https://example.com')
                self.assertEqual(result, {})
                self.assertEqual(stdout.getvalue(), '')

    def test_get_output_adds_spelling_suggestions(self):
        original_argv = sys.argv[:]
        try:
            sys.argv = ['workflow.py', 'helo', 'en', 'fr']
            with patch.object(
                    translate,
                    'check_spelling_and_get_suggestions',
                    return_value=(False, ['hello', 'help'])):
                feedback = translate.get_output('helo')

            items = feedback.feedback.findall('item')
            suggestions = [
                item.find('title').text
                for item in items
                if item.find('title').text in ('hello', 'help')
            ]
            self.assertEqual(suggestions, ['hello', 'help'])
        finally:
            sys.argv = original_argv

    def test_get_output_skips_spellcheck_for_sentence(self):
        original_argv = sys.argv[:]
        try:
            sys.argv = ['workflow.py', 'hello world', 'en', 'fr']
            with patch.object(
                    translate,
                    'check_spelling_and_get_suggestions') as spellcheck:
                translate.get_output('hello world')

            spellcheck.assert_not_called()
        finally:
            sys.argv = original_argv


if __name__ == '__main__':
    unittest.main()
