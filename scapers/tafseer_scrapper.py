import traceback
import argparse
import datetime
import json
import os
import time
import pandas as pd
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.webdriver import WebDriver as EdgeDriver
from selenium.webdriver.edge.options import Options


def load_progress(progress_file: str, key: str) -> dict[str, int]:
    print(f"Loading progress from {progress_file} with key {key}...")
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as pf:
            progress = json.load(pf)
        return progress.get(key, {"soura_index": 0, "aya_index": 0})
    return {"soura_index": 0, "aya_index": 0}


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


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Tafseer website using Selenium"
    )
    parser.add_argument(
        "--mv", type=str, help="Madares select value, inspect element to find"
    )
    parser.add_argument(
        "--tv", type=str, help="Tafsir select value, inspect element to find"
    )
    args = parser.parse_args()

    mv = str(args.mv)
    tv = str(args.tv)
    print(f"Starting scraper with mv={mv}, tv={tv}")

    progress_file = "progress.json"
    progress_key = f"{mv}_{tv}"
    progress_state = load_progress(progress_file, progress_key)
    resume_soura_index = progress_state.get("soura_index", 0)
    resume_aya_index = progress_state.get("aya_index", 0)
    print(
        f"Resuming from soura_index={resume_soura_index}, aya_index={resume_aya_index}"
    )

    edge_options = Options()
    edge_options.use_chromium = True
    edge_options.add_argument("headless")
    edge_options.add_argument("disable-gpu")
    edge_service = EdgeService("./msedgedriver.exe")
    driver = EdgeDriver(service=edge_service, options=edge_options)
    print("Opening Altafsir website...")
    driver.get("https://www.altafsir.com/Tafasir.asp?LanguageID=1")
    time.sleep(2)  # wait for page to load

    madares_dropdown = Select(driver.find_element(By.ID, "Madhab"))
    tafseer_dropdown = Select(driver.find_element(By.ID, "Tafsir"))
    tafseer_dropdown.select_by_value(tv)
    madares_dropdown.select_by_value(mv)

    rows = []
    current_id = 1

    try:
        soura_dropdown_element = driver.find_element(By.ID, "SoraName")
        soura_dropdown = Select(soura_dropdown_element)
        soura_elements = [
            option.get_attribute("value") for option in soura_dropdown.options
        ]
        print(f"Found {len(soura_elements)} soura options.")

        for soura_index, soura_value in enumerate(soura_elements):
            if soura_index < resume_soura_index:
                continue
            print(f"Processing soura_index={soura_index}, soura_value={soura_value}")

            soura_dropdown = Select(driver.find_element(By.ID, "SoraName"))
            soura_dropdown.select_by_value(soura_value)
            time.sleep(0.1)

            ayat_dropdown_element = driver.find_element(By.ID, "Ayat")
            ayat_dropdown = Select(ayat_dropdown_element)
            ayat_elements = [
                option.get_attribute("value") for option in ayat_dropdown.options
            ]

            start_aya_index = (
                resume_aya_index if soura_index == resume_soura_index else 0
            )

            for aya_index in range(start_aya_index, len(ayat_elements)):
                aya_value = ayat_elements[aya_index]
                print(f"  Processing aya_index={aya_index}")

                ayat_dropdown = Select(driver.find_element(By.ID, "Ayat"))
                ayat_dropdown.select_by_value(aya_value)
                time.sleep(0.1)

                show_button = driver.find_element(By.ID, "Display")
                show_button.click()
                time.sleep(0.25)

                text = ""
                elements = driver.find_elements(By.CLASS_NAME, "TextResultArabic")
                next_links = driver.find_elements(
                    By.XPATH,
                    "//a[starts-with(@href, 'Javascript:InnerLink_onchange') and .//img[(@alt='التالي' or @alt='Next')]]",
                )
                for el in elements:
                    text += " " + el.text

                while next_links:
                    next_links[0].click()
                    time.sleep(0.5)
                    elements = driver.find_elements(By.CLASS_NAME, "TextResultArabic")
                    next_links = driver.find_elements(
                        By.XPATH,
                        "//a[starts-with(@href, 'Javascript:InnerLink_onchange') and .//img[(@alt='التالي' or @alt='Next')]]",
                    )
                    for el in elements:
                        text += el.text

                rows.append(
                    {
                        "id": current_id,
                        "source": f"{mv}_{tv}",
                        "sentence": aya_value,
                        "chapter": soura_value,
                        "text": text.strip(),
                    }
                )
                print(f"    Added row id={current_id}")
                current_id += 1

                save_progress(progress_file, progress_key, soura_index, aya_index + 1)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected. Saving progress and exiting gracefully...")
        save_progress(progress_file, progress_key, soura_index, aya_index)
        save_df(rows, mv, tv)
        driver.quit()
        return
    except Exception as e:
        print("\nAn error occurred:", str(e))
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        screenshot = (
            f"screenshots/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        driver.save_screenshot(screenshot)
        print(
            f"---------------------Screenshot saved to {screenshot}----------------------"
        )
        traceback.print_stack()
        driver.quit()
        raise

    save_df(rows, mv, tv)
    driver.quit()
    print("Scraping completed.")


def save_df(rows, mv, tv):
    dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not os.path.exists("tafseer"):
        os.makedirs("tafseer")
    csv_filename = f"tafseer/{dt_str}_mv{mv}_tv{tv}.csv"
    df = pd.DataFrame(rows)
    df.to_csv(csv_filename, index=False, encoding="utf-8")
    print(f"Data saved to {csv_filename}")


if __name__ == "__main__":
    main()
