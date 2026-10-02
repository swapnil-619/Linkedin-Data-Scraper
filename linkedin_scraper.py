"""
LinkedIn Company People-Tab Scraper
------------------------------------
Reads a list of LinkedIn company "people" page URLs from a CSV file,
scrapes company name, headcount, a reconstructed company URL/ID, and
the "Where they live" country breakdown, then writes results to CSV.

INPUT:
  A CSV file with a single column named "url" (or just one URL per row),
  e.g. company_urls.csv:

      url
      https://www.linkedin.com/company/example-inc/people/
      https://www.linkedin.com/company/another-co/people/

OUTPUT:
  A CSV file with the scraped results.
"""

import os
import re
import csv
import time
import random
import traceback
from getpass import getpass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


# =========================================================
# CONFIG — edit these paths as needed
# =========================================================
INPUT_CSV = r"C:\Users\SwapnilPatel\OneDrive - TransForm Solutions (P) Limited\Desktop\linkedin HC-scraper\company_urls.csv"
OUTPUT_CSV = r"C:\Users\SwapnilPatel\OneDrive - TransForm Solutions (P) Limited\Desktop\linkedin HC-scraper\swapnil_TC_8_19_2026.csv"

USERNAME = os.environ.get("LINKEDIN_USERNAME")
PASSWORD = os.environ.get("LINKEDIN_PASSWORD")

MANUAL_LOGIN = True  # True = you log in by hand during the pause; False = script logs in for you

WORLD_COUNTRIES = {
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia",
    "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo, Democratic Republic of the", "Congo, Republic of the",
    "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador",
    "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
    "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, North", "Korea, South",
    "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein",
    "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania",
    "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
    "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway",
    "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland",
    "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey",
    "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
    "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe", "Türkiye",
}


# =========================================================
# HELPERS
# =========================================================
def load_company_urls(csv_path):
    """Read company URLs from a CSV file. Accepts a column named 'url',
    or falls back to the first column if no header match is found."""
    urls = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return urls

    header = [h.strip().lower() for h in rows[0]]
    start_idx = 0
    col_idx = 0
    if "url" in header:
        col_idx = header.index("url")
        start_idx = 1
    else:
        start_idx = 0

    for row in rows[start_idx:]:
        if row and row[col_idx].strip():
            urls.append(row[col_idx].strip())

    return urls


def build_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
    # Selenium 4.6+ has a built-in driver manager (Selenium Manager) that
    # auto-detects your installed Chrome version and fetches the matching
    # driver — no extra package or manual download needed.
    # No --user-data-dir is set, so each run starts a fresh, temporary
    # Chrome profile with no saved login — you'll need to log in each time.
    return webdriver.Chrome(options=options)


def login(driver, username, password, manual=True):
    driver.get("https://www.linkedin.com/login")
    time.sleep(random.uniform(3, 6))

    if manual or not username or not password:
        print("Please log in manually in the opened browser window.")
        print("You have 120 seconds...")
        time.sleep(120)
        return

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "username"))
    ).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(random.uniform(5, 8))


def extract_company_id(driver):
    employee_link = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[contains(@href, '/search/results/people/?currentCompany')]")
        )
    )
    employee_href = employee_link.get_attribute("href")
    u_id = employee_href.replace(
        "https://www.linkedin.com/search/results/people/?currentCompany=%5B%22",
        "https://www.linkedin.com/company/",
    )
    pos = u_id.find("%")
    return u_id[:pos] if pos != -1 else u_id


def extract_countries(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "org-people-bar-graph-module__geo-region"))
    )
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    first_li = soup.find("li", class_="artdeco-carousel__item")
    countries = []

    if first_li:
        buttons = first_li.find_all("button", class_="org-people-bar-graph-element")
        for btn in buttons:
            count_tag = btn.find("strong")
            location_tag = btn.find("span", class_="org-people-bar-graph-element__category")

            if not count_tag or not location_tag:
                continue

            count = count_tag.text.strip()
            location = location_tag.text.strip()

            if "," not in location and location in WORLD_COUNTRIES:
                countries.append(f"{location}:{count}")

    return "; ".join(countries)


def scrape_company(driver, url):
    driver.get(url)
    time.sleep(random.uniform(3, 5))

    company_name = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "org-top-card-summary__title"))
    ).text.strip()

    head_count_raw = driver.find_element(By.CLASS_NAME, "org-people__header-spacing-carousel").text.strip()
    head_count_digits = re.sub(r"[^\d]", "", head_count_raw)
    head_count = head_count_digits if head_count_digits else head_count_raw

    company_id = extract_company_id(driver)
    countries_str = extract_countries(driver)

    return company_name, head_count, company_id, countries_str


# =========================================================
# MAIN
# =========================================================
def main():
    company_urls = load_company_urls(INPUT_CSV)
    print(f"Loaded {len(company_urls)} company URLs from {INPUT_CSV}")

    if not company_urls:
        print("No URLs found — check INPUT_CSV path and format.")
        return

    driver = build_driver()
    all_data = []

    try:
        login(driver, USERNAME, PASSWORD, manual=MANUAL_LOGIN)

        for i, url in enumerate(company_urls, start=1):
            try:
                company_name, head_count, company_id, countries_str = scrape_company(driver, url)
                print(f"{i}. {url} => {company_name}, {head_count}, {company_id}")
                all_data.append([i, url, company_name, head_count, company_id, countries_str])
            except Exception as e:
                print(f"{i}. {url}: Failed with error: {type(e).__name__}: {e}")
                traceback.print_exc()
                all_data.append([i, url, "N/A", "N/A", "N/A", ""])

    finally:
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Serial Number", "Source", "LinkedIn Name", "LinkedIn HC", "LinkedIn U_id", "Countries"])
            writer.writerows(all_data)

        print(f"\n✅ CSV saved successfully at: {OUTPUT_CSV}")
        driver.quit()


if __name__ == "__main__":
    main()
