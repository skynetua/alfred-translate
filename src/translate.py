#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib.parse import urlencode
import asyncio
import aiohttp
import json
import feedback
import sys
import re


def is_ascii(s):
    s = re.sub(r'\W+', '', s)
    return all(ord(c) < 128 for c in s)

def get_translation_direction(text):
    """Returns direction of translation."""
    lang = sys.argv[2]
    alt = sys.argv[3]
    return f'{lang}-{alt}' if is_ascii(text) else f'{alt}-{lang}'

async def process_requests(urls):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[process_response_as_json(url, session) for url in urls])

async def process_response_as_json(url, session):
    try:
        async with session.get(url=url) as response:
            resp = await response.read()
            return json.loads(resp)
        
    except Exception as e:
        print("Failed to get url {} due to {}.".format(url, e.__class__))

def get_output(input_string):
    """Main entry point"""
    fb = feedback.Feedback()
    input_string = input_string.strip()
    if not input_string:
        fb.add_item(title="Translation not found", valid="no")
        return fb

    # Building url
    source_language, target_language = get_translation_direction(input_string).split('-')

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

    # Making requests in parallel
    responses = asyncio.run(process_requests([url]))

    translation_response = responses[0]
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