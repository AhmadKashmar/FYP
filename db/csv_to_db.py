import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from tqdm import tqdm
# from playground.utils import TextCleaner # no need to clean text here
import re


tv_mapping = {
    "1_1": {
        "title": "جامع البيان في تفسير القرآن",
        "author": "الطبري",
        "date_info": "ت 310 هـ",
        "concept": "بالمأثور",
        "source_type": "أمهات التفاسير",
    },
    "1_2": {
        "title": "الكشاف",
        "author": "الزمخشري",
        "date_info": "ت 538 هـ",
        "concept": "بياني",
        "source_type": "أمهات التفاسير",
    },
    "1_4": {
        "title": "مفاتيح الغيب ، التفسير الكبير",
        "author": "الرازي",
        "date_info": "ت 606 هـ",
        "concept": "اجتهادي",
        "source_type": "أمهات التفاسير",
    },
    "1_5": {
        "title": "الجامع لاحكام القرآن",
        "author": "القرطبي",
        "date_info": "ت 671 هـ",
        "concept": "فقهي",
        "source_type": "أمهات التفاسير",
    },
    "1_7": {
        "title": "تفسير القرآن العظيم",
        "author": "ابن كثير",
        "date_info": "ت 774 هـ",
        "concept": "بالمأثور",
        "source_type": "أمهات التفاسير",
    },
    "1_6": {
        "title": "انوار التنزيل واسرار التأويل",
        "author": "البيضاوي",
        "date_info": "ت 685 هـ",
        "concept": "اجتهادي",
        "source_type": "أمهات التفاسير",
    },
    "1_8": {
        "title": "تفسير الجلالين",
        "author": "المحلي و السيوطي",
        "date_info": "ت المحلي 864 هـ",
        "concept": "ميسر",
        "source_type": "أمهات التفاسير",
    },
    "1_9": {
        "title": "فتح القدير",
        "author": "الشوكاني",
        "date_info": "ت 1250 هـ",
        "concept": "اجتهادي",
        "source_type": "أمهات التفاسير",
    },
    "2_10": {
        "title": "تفسير القرآن",
        "author": "الفيروز آبادي",
        "date_info": "ت817 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_11": {
        "title": "بحر العلوم",
        "author": "السمرقندي",
        "date_info": "ت 375 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_12": {
        "title": "النكت والعيون",
        "author": "الماوردي",
        "date_info": "ت 450 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_13": {
        "title": "معالم التنزيل",
        "author": "البغوي",
        "date_info": "ت 516 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_14": {
        "title": "المحرر الوجيز في تفسير الكتاب العزيز",
        "author": "ابن عطية",
        "date_info": "ت 546 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_15": {
        "title": "زاد المسير في علم التفسير",
        "author": "ابن الجوزي",
        "date_info": "ت 597 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_16": {
        "title": "تفسير القرآن",
        "author": "ابن عبد السلام",
        "date_info": "ت 660 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_17": {
        "title": "مدارك التنزيل وحقائق التأويل",
        "author": "النسفي",
        "date_info": "ت 710 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_18": {
        "title": "لباب التأويل في معاني التنزيل",
        "author": "الخازن",
        "date_info": "ت 725 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_19": {
        "title": "البحر المحيط",
        "author": "ابو حيان",
        "date_info": "ت 754 هـ",
        "concept": "لغوي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_20": {
        "title": "التفسير",
        "author": "ابن عرفة",
        "date_info": "ت 803 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_22": {
        "title": "غرائب القرآن و رغائب الفرقان",
        "author": "القمي النيسابوري",
        "date_info": "ت 728 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_23": {
        "title": "الجواهر الحسان في تفسير القرآن",
        "author": "الثعالبي",
        "date_info": "ت 875 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_24": {
        "title": "اللباب في علوم الكتاب",
        "author": "ابن عادل",
        "date_info": "ت 880 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_25": {
        "title": "نظم الدرر في تناسب الآيات والسور",
        "author": "البقاعي",
        "date_info": "ت 885 هـ",
        "concept": "بياني",
        "source_type": "تفاسير أهل السنة",
    },
    "2_26": {
        "title": "الدر المنثور في التفسير بالمأثور",
        "author": "السيوطي",
        "date_info": "ت 911 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_28": {
        "title": "إرشاد العقل السليم إلى مزايا الكتاب الكريم",
        "author": "ابو السعود",
        "date_info": "ت 951 هـ",
        "concept": "بياني",
        "source_type": "تفاسير أهل السنة",
    },
    "2_67": {
        "title": "مقاتل بن سليمان",
        "author": "مقاتل بن سليمان",
        "date_info": "ت 150 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_75": {
        "title": "الكشف والبيان",
        "author": "الثعلبي",
        "date_info": "ت 427 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_78": {
        "title": "تفسير مجاهد",
        "author": "مجاهد بن جبر المخزومي",
        "date_info": "ت 104 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_79": {
        "title": "الدر المصون",
        "author": "السمين الحلبي",
        "date_info": "ت 756 هـ",
        "concept": "لغوي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_88": {
        "title": "التسهيل لعلوم التنزيل",
        "author": "ابن جزي الغرناطي",
        "date_info": "ت 741 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_91": {
        "title": "التفسير الكبير",
        "author": "الإمام الطبراني",
        "date_info": "ت 360 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_94": {
        "title": "تأويلات أهل السنة",
        "author": "الماتريدي",
        "date_info": "ت 333هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_96": {
        "title": "حاشية الصاوي",
        "author": "تفسير الجلالين",
        "date_info": "ت1241هـ",
        "concept": "ميسر",
        "source_type": "تفاسير أهل السنة",
    },
    "2_99": {
        "title": "تفسير سفيان الثوري",
        "author": "عبد الله سفيان بن سعيد بن مسروق الثوري الكوفي",
        "date_info": "ت161هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_100": {
        "title": "تفسير النسائي",
        "author": "النسائي",
        "date_info": "ت 303 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_101": {
        "title": "تفسير عبد الرزاق الصنعاني مصور",
        "author": "همام الصنعاني",
        "date_info": "ت 211 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_102": {
        "title": "محاسن التأويل",
        "author": "محمد جمال الدين القاسمي",
        "date_info": "ت 1332هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_103": {
        "title": "تفسير المنار",
        "author": "محمد رشيد بن علي رضا",
        "date_info": "ت 1354هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_104": {
        "title": "تفسير القرآن العزيز",
        "author": "ابن أبي زمنين",
        "date_info": "ت  399هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير أهل السنة",
    },
    "2_105": {
        "title": "كتاب نزهة القلوب",
        "author": "أبى بكر السجستاني",
        "date_info": "ت 330هـ",
        "concept": "لغوي",
        "source_type": "تفاسير أهل السنة",
    },
    "2_111": {
        "title": "رموز الكنوز في تفسير الكتاب العزيز",
        "author": "عز الدين عبد الرازق الرسعني الحنبلي",
        "date_info": "ت 661هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة",
    },
    "3_29": {
        "title": "تفسير القرآن",
        "author": "التستري",
        "date_info": "ت 283 هـ",
        "concept": "صوفي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_30": {
        "title": "حقائق التفسير",
        "author": "السلمي",
        "date_info": "ت 412 هـ",
        "concept": "صوفي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_31": {
        "title": "لطائف الإشارات",
        "author": "القشيري",
        "date_info": "ت 465 هـ",
        "concept": "إشاري",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_32": {
        "title": "عرائس البيان في حقائق القرآن",
        "author": "البقلي",
        "date_info": "ت 606 هـ",
        "concept": "صوفي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_33": {
        "title": "تفسير القرآن",
        "author": "ابن عربي",
        "date_info": "ت 638 هـ",
        "concept": "صوفي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_36": {
        "title": "روح البيان في تفسير القرآن",
        "author": "اسماعيل حقي",
        "date_info": "ت 1127 هـ",
        "concept": "صوفي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_37": {
        "title": "البحر المديد في تفسير القرآن المجيد",
        "author": "ابن عجيبة",
        "date_info": "ت 1224 هـ",
        "concept": "صوفي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_92": {
        "title": "تفسير الهدايه إلى بلوغ النهايه",
        "author": "مكي بن أبي طالب",
        "date_info": "ت 437 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_95": {
        "title": "تفسير الجيلاني",
        "author": "الجيلاني",
        "date_info": "ت713هـ",
        "concept": "صوفي",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "3_97": {
        "title": "التأويلات النجمية في التفسير الإشاري الصوفي",
        "author": "الإمام أحمد بن عمر",
        "date_info": "ت618 هـ",
        "concept": "إشاري",
        "source_type": "تفاسير أهل السنة الصوفية",
    },
    "9_50": {
        "title": "تيسير التفسير",
        "author": "اطفيش",
        "date_info": "ت 1332 هـ",
        "concept": "ميسر",
        "source_type": "تفاسير ميسرة",
    },
    "9_68": {
        "title": "تيسير التفسير",
        "author": "القطان",
        "date_info": "ت 1404 هـ",
        "concept": "ميسر",
        "source_type": "تفاسير ميسرة",
    },
    "9_65": {
        "title": "المنتخب في تفسير القرآن الكريم",
        "author": "لجنة القرآن و السنة",
        "date_info": None,
        "concept": "ميسر",
        "source_type": "تفاسير ميسرة",
    },
    "9_71": {
        "title": "أيسر التفاسير",
        "author": "د. أسعد حومد",
        "date_info": "ت 2011م",
        "concept": "ميسر",
        "source_type": "تفاسير ميسرة",
    },
    "9_85": {
        "title": "تفسير آيات الأحكام",
        "author": "الصابوني",
        "date_info": "مـ 1930م -",
        "concept": "فقهي",
        "source_type": "تفاسير ميسرة",
    },
    "9_84": {
        "title": "مختصر تفسير ابن كثير",
        "author": "الصابوني",
        "date_info": "مـ 1930م -",
        "concept": "بالمأثور",
        "source_type": "تفاسير ميسرة",
    },
    "9_83": {
        "title": "صفوة التفاسير",
        "author": "الصابوني",
        "date_info": "مـ 1930م -",
        "concept": "ميسر",
        "source_type": "تفاسير ميسرة",
    },
    "4_3": {
        "title": "مجمع البيان في تفسير القرآن",
        "author": "الطبرسي",
        "date_info": "ت 548 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "4_38": {
        "title": "تفسير القرآن",
        "author": "علي بن ابراهيم القمي",
        "date_info": "ت القرن 4 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "4_39": {
        "title": "التبيان الجامع لعلوم القرآن",
        "author": "الطوسي",
        "date_info": "ت 460 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "4_56": {
        "title": "الميزان في تفسير القرآن",
        "author": "الطبطبائي",
        "date_info": "ت 1401 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "4_41": {
        "title": "الصافي في تفسير كلام الله الوافي",
        "author": "الفيض الكاشاني",
        "date_info": "ت 1090 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "4_42": {
        "title": "تفسير بيان السعادة في مقامات العبادة",
        "author": "الجنابذي",
        "date_info": "ت القرن 14  هـ",
        "concept": "صوفي",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "4_40": {
        "title": "تفسير صدر المتألهين",
        "author": "صدر المتألهين الشيرازي",
        "date_info": "ت 1059 هـ",
        "concept": "صوفي",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "4_110": {
        "title": "البرهان في تفسير القرآن",
        "author": "هاشم الحسيني البحراني",
        "date_info": "ت 1107هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسير الشيعة الإثنى عشرية",
    },
    "5_44": {
        "title": "تفسير الحبري",
        "author": "الحبري",
        "date_info": "ت 286 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسيرالزيدية",
    },
    "5_45": {
        "title": "تفسير فرات الكوفي",
        "author": "فرات الكوفي",
        "date_info": "ت القرن 3 هـ",
        "concept": "بالمأثور",
        "source_type": "تفاسيرالزيدية",
    },
    "5_47": {
        "title": "تفسير الأعقم",
        "author": "الأعقم",
        "date_info": "ت القرن 9 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسيرالزيدية",
    },
    "5_89": {
        "title": "غريب القرآن",
        "author": "زيد بن علي",
        "date_info": "ت 120 هـ",
        "concept": "لغوي",
        "source_type": "تفاسيرالزيدية",
    },
    "6_48": {
        "title": "تفسير كتاب الله العزيز",
        "author": "الهواري",
        "date_info": "ت القرن 3 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسيرالاباضية",
    },
    "6_49": {
        "title": "هميان الزاد إلى دار المعاد",
        "author": "اطفيش",
        "date_info": "ت 1332 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسيرالاباضية",
    },
    "6_51": {
        "title": "جواهر التفسير",
        "author": "الخليلي",
        "date_info": "مـ 1942م- ",
        "concept": "اجتهادي",
        "source_type": "تفاسيرالاباضية",
    },
    "7_52": {
        "title": "روح المعاني",
        "author": "الالوسي",
        "date_info": "ت 1270 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير حديثة",
    },
    "7_54": {
        "title": "التحرير والتنوير",
        "author": "ابن عاشور",
        "date_info": "ت 1393 هـ",
        "concept": "بياني",
        "source_type": "تفاسير حديثة",
    },
    "7_55": {
        "title": "أضواء البيان في تفسير القرآن",
        "author": "الشنقيطي",
        "date_info": "ت 1393 هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير حديثة",
    },
    "7_76": {
        "title": "خواطر محمد متولي الشعراوي",
        "author": "محمد متولي الشعراوي",
        "date_info": "ت 1419 هـ",
        "concept": "ميسر",
        "source_type": "تفاسير حديثة",
    },
    "7_57": {
        "title": "الوسيط في تفسير القرآن الكريم",
        "author": "طنطاوي",
        "date_info": "ت 1431 هـ",
        "concept": "ميسر",
        "source_type": "تفاسير حديثة",
    },
    "8_60": {
        "title": "الوجيز",
        "author": "الواحدي",
        "date_info": "ت 468 هـ",
        "concept": "ميسر",
        "source_type": "تفاسير مختصرة",
    },
    "8_90": {
        "title": "النهر الماد",
        "author": "الأندلسي",
        "date_info": "ت 754 هـ",
        "concept": "لغوي",
        "source_type": "تفاسير مختصرة",
    },
    "8_106": {
        "title": "تذكرة الاريب في تفسير الغريب",
        "author": "الامام ابي الفرج ابن الجوزي",
        "date_info": "ت 597 هـ",
        "concept": "لغوي",
        "source_type": "تفاسير مختصرة",
    },
    "8_112": {
        "title": "الصراط المستقيم في تبيان القرآن الكريم",
        "author": "تفسير الكازروني",
        "date_info": "ت 923هـ",
        "concept": "اجتهادي",
        "source_type": "تفاسير مختصرة",
    },
}

# cleaner = TextCleaner()

SENTENCE_BREAK = re.compile(
    r"""(?<=[.!؟!?…:؛])(?![^()\[\]{}]*[)\]\}])\s+""", re.VERBOSE
)


def enforce_lower_bound(texts: list[str], min_token_cnt: int):
    """
    Makes sure the minimum number of tokens per list item is >= min_token_cnt
    """
    clean_texts: list[str] = []
    for text in texts:
        if not clean_texts:
            clean_texts.append(text)
            continue
        word_count = len(clean_texts[-1].split())
        if word_count < min_token_cnt:
            clean_texts[-1] += " " + text
        else:
            clean_texts.append(text)
    if len(clean_texts) > 1 and len(clean_texts[-1].split()) < min_token_cnt:
        last = clean_texts.pop()
        clean_texts[-1] += " " + last
    return clean_texts


def enforce_upper_bound(texts: list[str], max_token_cnt: int):
    i = 0
    clean_texts: list[str] = []
    while i < len(texts):
        text = texts[i]
        length = len(text.split())
        if length < 2 * max_token_cnt:
            clean_texts.append(text)
        else:
            for j in range(0, length, max_token_cnt):
                clean_texts.append(" ".join(text.split()[j : j + max_token_cnt]))
        i += 1
    return clean_texts


def to_sentences(text: str) -> list[str]:
    """
    Splits a piece of text to sentences with min/max token count. min token count is given more priority over max token count
    Generally, the real max token count is min + max - 1
    """
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\{\s*(?:<>\s*)?", "{", text)
    text = re.sub(r"(?:(?:\s*<>\s*)|\s+)\}", "}", text)
    text = re.sub(r"\(\s*(?:<>\s*)?", "(", text)
    text = re.sub(r"(?:(?:\s*<>\s*)|\s+)\)", ")", text)
    text = re.sub(r"\[\s*(?:<>\s*)?", "[", text)
    text = re.sub(r"(?:(?:\s*<>\s*)|\s+)\]", "]", text)
    text = re.sub(r"\s+\.", ".", text)
    # text = cleaner.cleanText(text)

    min_paragraph_tokens = 100
    min_sentence_tokens = 20
    max_sentence_tokens = 30

    paragraphs = text.split("<>")
    paragraphs = enforce_lower_bound(paragraphs, min_paragraph_tokens)

    result: list[str] = []
    for paragraph in paragraphs:
        sentences = SENTENCE_BREAK.split(paragraph)
        sentences = enforce_lower_bound(sentences, min_sentence_tokens)
        sentences = enforce_upper_bound(sentences, max_sentence_tokens)
        result.extend([s for s in sentences if s])
        # result[-1][-1] += "\n"  this line caused an error because result[-1] is the string while result[-1][-1] is the last character of that string
        result[-1] += "\n"  # add a newline to the end of the paragraph

    result = enforce_lower_bound(result, min_sentence_tokens)

    return [s for s in result if s]


def create_tables(cursor: psycopg2.extensions.cursor):
    # execute SQL in db/tables.sql to create the database and tables if not created
    with open("db/tables.sql", "r") as f:
        sql = f.read()
    cursor.execute(sql)


def add_sentences(cursor: psycopg2.extensions.cursor):
    df = pd.read_csv("data/quran.csv")
    query = """
    INSERT INTO Sentence (sentence_id, section_id, paragraph_id, text)
    VALUES %s
    ON CONFLICT (sentence_id, section_id)
    DO NOTHING;
    """
    values: list[tuple[int, int, int, str]] = []
    for i, row in df.iterrows():
        row["aya"] = int(row["aya"])
        row["sura"] = int(row["sura"])
        values.append(
            (
                row["aya"],
                row["sura"],
                None,
                # cleaner.cleanText(row["text"]),
                row["text"],
            )
        )
    execute_values(cursor, query, values)


def add_sources(cursor: psycopg2.extensions.cursor):
    query = """
    INSERT INTO Related_text_source (source_id, source_type, author, date_info, concept, title)
    VALUES %s
    ON CONFLICT (source_id) DO NOTHING;
    """
    values: list[tuple[str, str, str, str, str]] = []
    for source_id, value in tv_mapping.items():
        values.append(
            (
                source_id,
                value["source_type"],
                value["author"],
                value["date_info"],
                value["concept"],
                value["title"],
            ),
        )

    execute_values(cursor, query, values)


def process_df(
    df: pd.DataFrame,
    file: str,
    cursor: psycopg2.extensions.cursor,
    page_size: int = 1000,
):
    # infer the mv, tv, soura, aya, and number of ayas this tafsir covers from the tafsir_id column
    df[["mv", "tv", "soura", "aya", "size"]] = df["tafsir_id"].str.split(
        "_", expand=True
    )
    # convert to integers
    df[["soura", "aya", "size"]] = df[["soura", "aya", "size"]].astype(int)
    # get the source ID from the mv and tv values
    df["source_id"] = df["mv"].astype(str) + "_" + df["tv"].astype(str)
    # divide the tafsir on the sentence level
    df["sentences"] = df["text"].map(to_sentences)
    # explode the sentences column to have one sentence per row
    sentences = df.explode("sentences", ignore_index=True)
    # the ID is the <tafsir_id>_<index>
    sentences["related_text_id"] = (
        sentences["tafsir_id"]
        + "_"
        + sentences.groupby("tafsir_id").cumcount().astype(str)
    )
    sentences.rename(columns={"sentences": "details"}, inplace=True)

    related_rows = sentences[
        ["related_text_id", "details", "source_id"]
    ].values.tolist()

    execute_values(
        cursor,
        """
        INSERT INTO related_text (related_id, details, source_id)
        VALUES %s
        ON CONFLICT (related_id) DO NOTHING
        """,
        related_rows,
        page_size=page_size,
    )

    relationship_rows = []
    for row in tqdm(sentences.itertuples()):
        # iterate over the sentences and create the relationship rows
        aya: int = row.aya
        soura: int = row.soura
        related_text_id: str = row.related_text_id
        size: int = row.size
        relationship_rows.extend(
            [(aya + j, soura, related_text_id) for j in range(size)]
        )

    execute_values(
        cursor,
        """
        INSERT INTO relationship (sentence_id, section_id, related_text_id)
        VALUES %s
        ON CONFLICT (sentence_id, section_id, related_text_id) DO NOTHING
        """,
        relationship_rows,
        page_size=page_size,
    )

    cursor.connection.commit()
    print("File processed:", file)
    os.makedirs("data/done", exist_ok=True)
    os.rename(file, os.path.join("data/done", os.path.basename(file)))


def main():
    load_dotenv()
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    DATA_DIR = os.getenv("DATA_DIR")
    # connect to the database
    connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
    )
    cursor = connection.cursor()
    create_tables(cursor)
    add_sentences(cursor)
    add_sources(cursor)
    connection.commit()

    for i, file in enumerate(os.listdir(DATA_DIR)):
        file = os.path.join(DATA_DIR, file)
        process_df(pd.read_csv(file), file, cursor)
        connection.commit()
        # if i == 3:
        #     input()


if __name__ == "__main__":
    main()
