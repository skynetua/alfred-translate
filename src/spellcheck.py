from Foundation import NSNotFound
from AppKit import NSSpellChecker, NSString
import json
import sys


def _normalize_language(language_code):
    return language_code.lower().replace('_', '-')


def _find_supported_language(language_code, available_languages):
    normalized = _normalize_language(language_code)

    for available in available_languages:
        if _normalize_language(str(available)) == normalized:
            return str(available)

    base_language = normalized.split('-', 1)[0]
    for available in available_languages:
        available_text = str(available)
        if _normalize_language(available_text).split('-', 1)[0] == base_language:
            return available_text

    return None


def check_spelling_and_get_suggestions(word, language_code):
    if not word or not language_code:
        return True, []

    spell_checker = NSSpellChecker.sharedSpellChecker()
    available_languages = spell_checker.availableLanguages()
    supported_language = _find_supported_language(language_code, available_languages)
    if supported_language is None:
        return True, []

    word_nsstring = NSString.stringWithString_(word)
    misspelled_range = spell_checker.checkSpellingOfString_startingAt_(
        word_nsstring, 0)

    if misspelled_range.location == NSNotFound:
        return True, []

    suggestions = spell_checker.guessesForWordRange_inString_language_inSpellDocumentWithTag_(
        misspelled_range, word_nsstring, supported_language, 0)
    return False, [str(suggestion) for suggestion in suggestions]


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(json.dumps([True, []]))
        raise SystemExit(0)

    print(json.dumps(check_spelling_and_get_suggestions(
        sys.argv[1], sys.argv[2])))