
"""
All Language Codes
IETF Language Tags

en - English
ru - Russian
uk - Ukrainian
be - Belarusian
ca - Catalan
hr - Croatian
nl - Dutch
fr - French
de - German
id - Indonesian
it - Italian
kk - Kazakh
ko - Korean
ms - Malay
pl - Polish
pt - Portuguese (Brazil)
sr - Serbian
es - Spanish
tr - Turkish
"""

DEFAULT_LANGUAGE = 'en'  # Ensure that all texts include the default language compatibility

FIRST_TEXT = {
	'en': "Hello!",
	'ru': "Привет!"
}  # Example of a text

def get_text(lang_code: str, text: dict[str, str]) -> str:
    if not lang_code in text.keys():
        lang_code = DEFAULT_LANGUAGE
    return text[lang_code]
