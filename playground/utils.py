from pyarabic import araby
from camel_tools.utils.normalize import normalize_unicode
import re
import wojood.utils as utils
import pandas as pd
from wojood.ner_shell import process_ner

ZERO_SPACE_CHAR = "\u200c"


class Wojood:
    wojood_tagger = utils.get_tagger()

    def find_entities(self, textList: str | list) -> list[tuple[str, str]]:
        """
        Returns a list of tuples of the form (entity, tag).
        """
        if isinstance(textList, str):
            textList = [textList]
        df = pd.DataFrame({"text": textList})
        entity_tag_list: list[tuple[str, str]] = process_ner(
            df,
            self.wojood_tagger,
            text_column_name="text",
            batch_size=1,
            id_column_name=None,
        )

        return entity_tag_list


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
        return text
