import google.generativeai as genai
from pyarabic import araby
from camel_tools.utils.normalize import normalize_unicode
import re

ZERO_SPACE_CHAR = "\u200c"


class TextCleaner:
    @staticmethod
    def deNoiseArabicText(text: str):
        """
        removes diactrics and tatweel and normalizes 'ى'
        """
        text = araby.strip_tashkeel(text)
        text = araby.strip_tatweel(text)
        text = araby.strip_diacritics(text)
        replacements = {
            "ى": "ي",
            "ؤ": "و",
            "إ": "ا",
            "أ": "ا",
            "آ": "ا",
            "ة": "ه",
            "ئ": "ي",
            "ء": "ا",
        }
        text = text.translate(str.maketrans(replacements))
        return text

    @staticmethod
    def replaceMultipleSpaces(inputString):
        """
        replaces consecutive white-spaces with a single space
        """
        cleanedString = re.sub(r"\s+", " ", inputString)
        return cleanedString

    @staticmethod
    def cleanText(text: str, strip=True):
        """
        removes diactrics, tatweel, shadda, new lines, zero-space characters, and leading and trailing whitespaces
        """
        text = TextCleaner.deNoiseArabicText(text)
        text = text.replace(ZERO_SPACE_CHAR, "")
        if strip:
            text = text.strip()
            text = TextCleaner.replaceMultipleSpaces(text)
        text = normalize_unicode(text)
        return text.strip()


class Gemini:

    def __init__(self, api_keys: list[str], model: str = "gemini-2.5-flash"):
        if not api_keys:
            raise ValueError("API key not found")
        self._api_keys = api_keys
        self._idx = 0
        self.model_name = model
        self._set_key(self._idx)

    def _set_key(self, idx: int):
        idx = idx % len(self._api_keys)
        self._idx = idx
        genai.configure(api_key=self._api_keys[idx])
        self.model = genai.GenerativeModel(self.model_name)

    def answer_and_rotate(self, prompt: str) -> str:
        n = len(self._api_keys)
        while n:
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception:
                print("Permutating Key...")
            n -= 1
            if n == 0:
                raise Exception("All API keys Exhausted.")
            self._set_key(self._idx + 1)

    def ask(self, user_query: str, json_data: str) -> str:

        prompt = f"""Given this JSON data:
<JSON data>
{json_data}
</JSON data>

Answer should include which quran ayat answer this query and how (according to each source), and mention evidence from these. You can exclude those you found not relevant out of them (do not mention excluding them). If all are to be excluded, only output the following "لم أجد أي معلومات ذات صلة للإجابة على هذا الاستفسار.". If some of them are to be excluded, exclude them without mentioning doing so.
Your output should be purely Arabic.
<user query>
{user_query}
</user query>

Some sample format for your output is as follows:
يذكر في القرآن الكريم الايت التالية (الاية if only one):
- <aya1, without any comments on it>
- <aya2, without any comments on it>
- ...
يُفسر <author> في تفسيره "<source_name>" على النحو التالي:
- <do not mention related_id or anything, just mention which sentence is explained by what
- <do the same for the next related_text mentioned as well>
- ...

يُفسر <author> في تفسيره "<source_name>" على النحو التالي:
- <do not mention related_id or anything, just mention which sentence is explained by what
- <do the same for the next related_text mentioned as well>
- ...
...

"""
        response = self.answer_and_rotate(prompt)
        return response

    def generate_question(self, text: str) -> str:

        prompt = f"""generate an arabic question answered by the following text
<text>
{text}
<text/>
Your output should only be the question to be asked. Do not provide anything else.


Sample input:
"Paris is the capital of France."
Sample output:
"ما هي عاصمة فرنسا؟"
"""

        response = self.answer_and_rotate(prompt)
        return response