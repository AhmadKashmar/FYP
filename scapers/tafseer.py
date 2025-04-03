import traceback
import argparse
import datetime
import json
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

MV_TV_PAIRS = {
    "1": ["1", "2", "4", "5", "7", "6", "8", "9"],
    "2": [
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "22",
        "23",
        "24",
        "25",
        "26",
        "28",
        "67",
        "75",
        "78",
        "79",
        "88",
        "91",
        "94",
        "96",
        "99",
        "100",
        "101",
        "102",
        "103",
        "104",
        "105",
        "111",
    ],
    "3": ["29", "30", "31", "32", "33", "36", "37", "92", "95", "97"],
    "10": ["50", "68", "65", "71", "85", "84", "83"],
    "4": ["3", "38", "39", "56", "41", "42", "40", "110"],
    "5": ["44", "45", "47", "89"],
    "6": ["48", "49", "51"],
    "7": ["52", "54", "55", "76", "57"],
    "8": ["60", "90", "106", "112"],
}

SOURA_AYA_COUNT = {
    1: 7,
    2: 286,
    3: 200,
    4: 176,
    5: 120,
    6: 165,
    7: 206,
    8: 75,
    9: 129,
    10: 109,
    11: 123,
    12: 111,
    13: 43,
    14: 52,
    15: 99,
    16: 128,
    17: 111,
    18: 110,
    19: 98,
    20: 135,
    21: 112,
    22: 78,
    23: 118,
    24: 64,
    25: 77,
    26: 227,
    27: 93,
    28: 88,
    29: 69,
    30: 60,
    31: 34,
    32: 30,
    33: 73,
    34: 54,
    35: 45,
    36: 83,
    37: 182,
    38: 88,
    39: 75,
    40: 85,
    41: 54,
    42: 53,
    43: 89,
    44: 59,
    45: 37,
    46: 35,
    47: 38,
    48: 29,
    49: 18,
    50: 45,
    51: 60,
    52: 49,
    53: 62,
    54: 55,
    55: 78,
    56: 96,
    57: 29,
    58: 22,
    59: 24,
    60: 13,
    61: 14,
    62: 11,
    63: 11,
    64: 18,
    65: 12,
    66: 12,
    67: 30,
    68: 52,
    69: 52,
    70: 44,
    71: 28,
    72: 28,
    73: 20,
    74: 56,
    75: 40,
    76: 31,
    77: 50,
    78: 40,
    79: 46,
    80: 42,
    81: 29,
    82: 19,
    83: 36,
    84: 25,
    85: 22,
    86: 17,
    87: 19,
    88: 26,
    89: 30,
    90: 20,
    91: 15,
    92: 21,
    93: 11,
    94: 8,
    95: 8,
    96: 19,
    97: 5,
    98: 8,
    99: 8,
    100: 11,
    101: 11,
    102: 8,
    103: 3,
    104: 9,
    105: 5,
    106: 4,
    107: 7,
    108: 3,
    109: 6,
    110: 3,
    111: 5,
    112: 4,
    113: 5,
    114: 6,
}

aya_tafsir_pairs = []  # not saved for now, can be inferred form the tafsir_id
all_tafsirs = []  # holds the tafsir text and its id
# the id is composed of the following main parts, separated by underscores:
# mv, tv, soura_index, aya_index, aya_window_size
# this tafsir is related to the ayas between aya_index and aya_index + aya_window_size - 1
# for example, if mv=1, tv=1, soura_index=2, aya_index=3, aya_window_size=5
# then the tafsir is related to the ayas 3, 4, 5, 6, and 7 of soura 2
# i replaced new lines by <> to preserve the paragraphs and not ruin the CSV file


def parse_args() -> tuple[str, str]:
    parser = argparse.ArgumentParser(
        description="Scrape Tafseer website using Selenium"
    )
    parser.add_argument(
        "--mv",
        type=str,
        help="Madares select value, inspect element to find",
    )
    parser.add_argument(
        "--tv",
        type=str,
        help="Tafsir select value, inspect element to find",
    )
    args = parser.parse_args()
    mv = str(args.mv)
    tv = str(args.tv)
    assert tv in MV_TV_PAIRS[mv], f"Invalid TV value {tv} for MV {mv}"
    return mv, tv


def load_progress(progress_file: str, key: str) -> dict[str, int]:
    print(f"Loading progress from {progress_file} with key {key}...")
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as pf:
            progress = json.load(pf)
        return progress.get(key, {"soura_index": 1, "aya_index": 1})
    return {"soura_index": 1, "aya_index": 1}


def save_progress(progress_file: str, key: str, soura_index: int, aya_index: int):
    print(
        f"Saving progress to {progress_file}: soura_index={soura_index}, aya_index={aya_index}"
    )
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as pf:
            progress = json.load(pf)
    else:
        progress = {}
    progress[key] = {"soura_index": soura_index, "aya_index": aya_index}
    with open(progress_file, "w", encoding="utf-8") as pf:
        json.dump(progress, pf, indent=2)


def save_df(rows: list[dict], mv: str, tv: str):
    dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not os.path.exists("tafseer"):
        os.makedirs("tafseer")
    csv_filename = f"tafseer/{dt_str}_mv{mv}_tv{tv}.csv"
    df = pd.DataFrame(rows)
    df.to_csv(csv_filename, index=False, encoding="utf-8")
    print(f"Data saved to {csv_filename}")


def get_page_count(text: str) -> int:
    pattern = r"""<td>\s*
                <a\s+href\s*=\s*"javascript:[^"]*"\s*>
                \s*<u>\s*         
                (\d+)             
                \s*</u>\s*        
                </a>\s*          
                </td>            
            """
    match = max(
        [1] + [int(i) for i in re.findall(pattern, text, flags=re.DOTALL | re.VERBOSE)]
    )
    return match


def get_aya_count(soup: BeautifulSoup) -> int:
    div = soup.find("h2", {"id": "ayahtext"})
    count = str(div).count("<b>{</b>")
    return count


def get_tafsir_text(soup: BeautifulSoup) -> str:
    for u_tag in soup.find_all("u"):
        parent = u_tag
        for _ in range(5):
            if parent.parent:
                parent = parent.parent
            else:
                break
        parent.decompose()

    div = soup.find("div", recursive=False)
    if div:
        div = div.find("div", recursive=False)
    # for this div, get its text content
    text = div.get_text(separator="<>", strip=True)
    return text.replace("{\n", "{ ").replace("}\n", "} ").replace("]\n", "] ")


def clean(text: str) -> str:
    text = text.lower()
    text = re.sub(
        r"<(style|script|head|link|title|meta)\b[^>]*>[\s\S]*?</\1>", "", text
    )
    text = re.sub(r"<meta\b[^>]*\/?>", "", text)
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    text = text.replace("center", "div")
    text = text.replace("font>", "span>")
    return text


def main():
    mv, tv = parse_args()
    progress_file = "progress.json"
    progress_key = f"{mv}_{tv}"
    progress_state = load_progress(progress_file, progress_key)
    resume_soura_index = progress_state.get("soura_index", 1)
    resume_aya_index = progress_state.get("aya_index", 1)
    print(
        f"Resuming from soura_index={resume_soura_index}, aya_index={resume_aya_index}"
    )
    try:
        soura_index = resume_soura_index
        while soura_index <= 114:
            print(f"Processing Soura {soura_index}...")
            aya_increment = 1
            aya_index = resume_aya_index if soura_index == resume_soura_index else 1
            while aya_index <= SOURA_AYA_COUNT[soura_index]:
                try:
                    print(f"Processing Aya {aya_index}...")
                    max_page_count = 1
                    tafsirs = []
                    page = 1
                    while page <= max_page_count:
                        req = requests.get(
                            f"https://www.altafsir.com/Tafasir.asp?tMadhNo={mv}&tTafsirNo={tv}&tSoraNo={soura_index}&tAyahNo={aya_index}&tDisplay=yes&Page={page}&Size=1&LanguageId=1"
                        )
                        text = clean(req.text)
                        soup = BeautifulSoup(text, "html.parser")
                        disp_frame = soup.find("div", {"id": "dispframe"})
                        soup = BeautifulSoup(
                            disp_frame.decode_contents(), "html.parser"
                        )
                        text = (
                            str(soup)
                            .replace("/font>", "/span>")
                            .replace("<font", "<span")
                            .replace("</td></td>", "</td>")
                        )
                        max_page_count = get_page_count(text)
                        tafsirs.append(get_tafsir_text(soup))
                        aya_increment = get_aya_count(soup)
                        page += 1
                    tafsir = "<>".join(tafsirs) if tafsirs else ""
                    tafsir_id = f"{mv}_{tv}_{soura_index}_{aya_index}_{aya_increment}"
                    for i in range(aya_increment):
                        aya_tafsir_pairs.append((soura_index, aya_index + i, tafsir_id))
                    all_tafsirs.append({"tafsir_id": tafsir_id, "text": tafsir})
                except Exception as e:
                    print(
                        f"No tafsir found for Soura {soura_index}, Aya {aya_index}: {e}"
                    )
                aya_index += aya_increment
            soura_index += 1
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Saving progress and exiting gracefully...")
        save_progress(progress_file, progress_key, soura_index, aya_index)
        save_df(all_tafsirs, mv, tv)
        return
    except Exception as e:
        print("\nAn error occurred:", str(e))
        traceback.print_stack()
        raise

    save_df(all_tafsirs, mv, tv)


if __name__ == "__main__":
    main()
