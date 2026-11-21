#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib.parse import urlencode
import json
import os
import sys
import re
import subprocess
import urllib.error
import urllib.request

import feedback

try:
    from spellcheck import check_spelling_and_get_suggestions
except ImportError:
    def check_spelling_and_get_suggestions(word, language_code):
        spellcheck_script = os.path.join(os.path.dirname(__file__), 'spellcheck.py')
        try:
            result = subprocess.run(
                ['/usr/bin/python3', spellcheck_script, word, language_code],
                capture_output=True,
                text=True,
                timeout=5,
                check=True)
            is_correct, suggestions = json.loads(result.stdout)
            return is_correct, suggestions
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            return True, []


def is_ascii(s):
    s = re.sub(r'\W+', '', s)
    return all(ord(c) < 128 for c in s)


def get_translation_direction(text):
    """Returns direction of translation."""
    lang = sys.argv[2]
    alt = sys.argv[3]
    return f'{lang}-{alt}' if is_ascii(text) else f'{alt}-{lang}'


def is_single_word_arg(text):
    return len(text.split()) == 1


def process_response_as_json(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=20) as response:
            resp = response.read()
        body = resp.decode('utf-8')
        print(f'DEBUG_TRANSLATE_RESPONSE: {body}', file=sys.stderr)
        return json.loads(body)
    except urllib.error.HTTPError as exc:
        print(f'DEBUG_TRANSLATE_HTTP_ERROR: {exc}', file=sys.stderr)
        return {}
    except Exception as exc:
        print(f'DEBUG_TRANSLATE_EXCEPTION: {exc}', file=sys.stderr)
        return {}

def get_output(input_string):
    """Main entry point"""
    fb = feedback.Feedback()
    input_string = input_string.strip()
    if not input_string:
        fb.add_item(title="Translation not found", valid="no")
        return fb

    # Building url
    source_language, target_language = get_translation_direction(input_string).split('-')

    if is_single_word_arg(input_string):
        is_correct, suggestions = check_spelling_and_get_suggestions(
            input_string, source_language)
        if not is_correct:
            for suggestion in suggestions[:5]:
                fb.add_item(
                    title=suggestion,
                    subtitle='Spelling suggestion',
                    arg=suggestion,
                    valid='no',
                    autocomplete=suggestion,
                    icon='spellcheck.png')

    """
    https://stackoverflow.com/questions/26714426/what-is-the-meaning-of-google-translate-query-params
    Using dictionary for single word or alternate translations for sentence
    """
    params = {
        'client': 'gtx',
        'dj': 1,
        'sl': source_language,
        'tl': target_language,
        'q': input_string,
        'dt': ['at', 'bd']
    }
    url = 'https://translate.googleapis.com/translate_a/single?' + urlencode(params, doseq=True)

    translation_response = process_response_as_json(url)
    if not isinstance(translation_response, dict):
        fb.add_item(title="Translation not found", valid="no")
        return fb

    if 'dict' in translation_response:
        """Check single word translation of dict type"""
        for item in translation_response['dict']:
            for entry in item.get('entry', []):
                fb.add_item(
                    title=entry['word'].capitalize(),
                    arg=entry['word'],
                    subtitle=', '.join(entry.get('reverse_translation', [])))
    elif 'alternative_translations' in translation_response:
        """Check sentence translation of alt type"""
        for alt_translations in translation_response['alternative_translations']:
            for alt in alt_translations.get('alternative', []):
                fb.add_item(
                    title=alt['word_postproc'].capitalize(),
                    arg=alt['word_postproc'],
                    subtitle=alt_translations['src_phrase'])
    else:
        fb.add_item(title="Translation not found", valid="no")
    return fb

if __name__ == '__main__':
    print(get_output(sys.argv[1]))