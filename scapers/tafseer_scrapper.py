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


def load_progress(progress_file: str, key: str) -> dict[str, int]:
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as pf:
            progress = json.load(pf)
        return progress.get(key, {"soura_index": 0, "aya_index": 0})
    return {"soura_index": 0, "aya_index": 0}


def save_progress(progress_file: str, key: str, soura_index: int, aya_index: int):
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as pf:
            progress = json.load(pf)
    else:
        progress = {}
    progress[key] = {"soura_index": soura_index, "aya_index": aya_index}
    with open(progress_file, "w", encoding="utf-8") as pf:
        json.dump(progress, pf, indent=2)


def remove_progress_entry(progress_file: str, key: str):
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as pf:
            progress = json.load(pf)
        if key in progress:
            del progress[key]
        with open(progress_file, "w", encoding="utf-8") as pf:
            json.dump(progress, pf, indent=2)


def main():
    # Parse command line arguments for mv and tv values.
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

    # Set up progress file and key for resuming work.
    progress_file = "progress.json"
    progress_key = f"{mv}_{tv}"
    progress_state = load_progress(progress_file, progress_key)
    resume_soura_index = progress_state.get("soura_index", 0)
    resume_aya_index = progress_state.get("aya_index", 0)

    # Change this to chrome if you want to use Chrome instead of Edge.
    edge_service = EdgeService("./msedgedriver.exe")
    driver = EdgeDriver(service=edge_service)
    driver.get("https://www.altafsir.com/Tafasir.asp?LanguageID=1")
    time.sleep(2)  # wait for page to load

    # Set the madares and tafsir dropdown values to the ones we want to scrape
    madares_dropdown = Select(driver.find_element(By.ID, "Madhab"))
    tafseer_dropdown = Select(driver.find_element(By.ID, "Tafsir"))
    tafseer_dropdown.select_by_value(tv)
    madares_dropdown.select_by_value(mv)

    rows = []
    current_id = 1

    try:
        # Get soura dropdown options.
        soura_dropdown_element = driver.find_element(By.ID, "SoraName")
        soura_dropdown = Select(soura_dropdown_element)
        soura_elements = [
            option.get_attribute("value") for option in soura_dropdown.options
        ]

        # Iterate over soura values starting from the saved index.
        for soura_index, soura_value in enumerate(soura_elements):
            if soura_index < resume_soura_index:
                continue

            # select the current soura
            soura_dropdown = Select(driver.find_element(By.ID, "SoraName"))
            soura_dropdown.select_by_value(soura_value)
            time.sleep(0.1)

            # Get ayat dropdown options for the current soura.
            ayat_dropdown_element = driver.find_element(By.ID, "Ayat")
            ayat_dropdown = Select(ayat_dropdown_element)
            ayat_elements = [
                option.get_attribute("value") for option in ayat_dropdown.options
            ]

            # Determine from which aya to resume (if we are on the saved soura).
            start_aya_index = (
                resume_aya_index if soura_index == resume_soura_index else 0
            )

            for aya_index in range(start_aya_index, len(ayat_elements)):
                aya_value = ayat_elements[aya_index]

                # select the current aya
                ayat_dropdown = Select(driver.find_element(By.ID, "Ayat"))
                ayat_dropdown.select_by_value(aya_value)
                time.sleep(0.1)

                # load the tafseer text.
                show_button = driver.find_element(By.ID, "Display")
                show_button.click()
                time.sleep(0.5)

                # Extract the text for the current aya.
                text = ""
                elements = driver.find_elements(By.CLASS_NAME, "TextResultArabic")
                next_links = driver.find_elements(
                    By.XPATH,
                    "//a[starts-with(@href, 'Javascript:InnerLink_onchange') and .//img[(@alt='التالي' or @alt='Next')]]",
                )
                for el in elements:
                    text += " " + el.text

                # Continue clicking "Next" if available and accumulate text.
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

                # Append the scraped data as a new row.
                rows.append(
                    {
                        "id": current_id,
                        "source": f"{mv}_{tv}",
                        "sentence": aya_value,
                        "chapter": soura_value,
                        "text": text.strip(),
                    }
                )
                current_id += 1

                # Update progress after each aya so that we can resume here if interrupted.
                save_progress(progress_file, progress_key, soura_index, aya_index + 1)

    except KeyboardInterrupt:
        # Save the current progress state and data
        print("\nKeyboardInterrupt detected. Saving progress and exiting gracefully...")
        save_progress(progress_file, progress_key, soura_index, aya_index)
        save_df(rows, mv, tv)
        driver.quit()
        return
    except Exception as e:
        print("\nAn error occurred:", str(e))
        traceback.print_stack()
        remove_progress_entry(progress_file, progress_key)
        driver.quit()
        raise

    remove_progress_entry(progress_file, progress_key)
    save_df(rows, mv, tv)
    driver.quit()
    print("Scraping completed.")


def save_df(rows, mv, tv):
    dt_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"tafseer_{dt_str}_mv{mv}_tv{tv}.csv"
    df = pd.DataFrame(rows)
    df.to_csv(csv_filename, index=False, encoding="utf-8")
    print(f"Data saved to {csv_filename}")


if __name__ == "__main__":
    main()
