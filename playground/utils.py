from pyarabic import araby
from camel_tools.utils.normalize import normalize_unicode
import re

ZERO_SPACE_CHAR = '\u200c'

class TextCleaner:
    @staticmethod
    def deNoiseArabicText(text: str):
        """
        removes diactrics and tatweel and normalizes 'ى' 
        """
        # arabic normalization (hamze, ta, ى)
        text = araby.strip_tashkeel(text)
        text = araby.strip_tatweel(text)
        text = araby.strip_diacritics(text)
        # text = araby.normalize_hamza(text)
        replacements = {
            'ى': 'ي',
            'ؤ': 'و',
            'إ': 'ا',
            'أ': 'ا',
            'آ': 'ا',
            'ة': 'ه',
            'ئ': 'ي',
            'ء': 'ا'
        }
        text = text.translate(str.maketrans(replacements))
        return text
    

    @staticmethod
    def replaceMultipleSpaces(inputString):
        """
        replaces consecutive white-spaces with a single space
        """
        cleanedString = re.sub(r'\s+', ' ', inputString)
        return cleanedString


    @staticmethod
    def cleanText(text: str, strip=True):
        """
        removes diactrics, tatweel, shadda, new lines, zero-space characters, and leading and trailing whitespaces
        """
        # text = GetArabicPart(text)
        text = TextCleaner.deNoiseArabicText(text)
        # text = text.replace('\n',' ')
        text = text.replace(ZERO_SPACE_CHAR, '')
        if strip:
            text = text.strip()
            text = TextCleaner.replaceMultipleSpaces(text)
        text = normalize_unicode(text)
        return text
    
    
print(TextCleaner.cleanText("""قال: وفيها وجه آخر في التفسير، وهو أنهم كانوا يَرَوْنَ من ملوكهم ما لا يصبرون عليه، فاتخذوا أسراباً وصوامع وابتدعوا ذلك، فلما ألزموا أنفسهم ذلك التطوع ودخلوا عليه، لزمهم تمامه، كما أن الإنسان إذا جعل على نفسه صوماً لم يُفْرَض عليه لزمه أن يتم."""
))