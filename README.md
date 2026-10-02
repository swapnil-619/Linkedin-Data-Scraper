# LinkedIn Company People-Tab Scraper

A Python + Selenium script that reads a list of LinkedIn company "People" page URLs from a CSV and extracts each company's name, headcount, LinkedIn company ID URL, and the "Where they live" country breakdown. Results are saved to a CSV file.

## Features

- Batch processing of company URLs from a CSV file
- Extracts:
  - **Company name**
  - **Headcount** (LinkedIn employee count)
  - **Company ID URL** (reconstructed from the "See all employees" link)
  - **Country breakdown** of employees (e.g. `India:120; United States:45`)
- Manual login (default) or automated login via environment variables
- Randomized delays between actions
- Failed URLs are logged and written as `N/A` so one error doesn't stop the run
- Results are saved even if the script is interrupted

## Requirements

- Python 3.8+
- Google Chrome installed
- Python packages:

```bash
pip install selenium beautifulsoup4
```

Selenium 4.6+ includes Selenium Manager, which automatically downloads the matching ChromeDriver, so no manual driver setup is needed.

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
   ```

2. **Create the input CSV** (e.g. `company_urls.csv`) with a `url` column:

   ```csv
   url
   https://www.linkedin.com/company/example-inc/people/
   https://www.linkedin.com/company/another-co/people/
   ```

   If there is no `url` header, the first column is used.

3. **Edit the config section** at the top of `linkedin_scraper.py`:

   ```python
   INPUT_CSV = r"path/to/company_urls.csv"
   OUTPUT_CSV = r"path/to/output.csv"
   MANUAL_LOGIN = True   # False = script logs in using env variables
   ```

4. *(Optional)* For automated login, set environment variables:

   ```bash
   # macOS / Linux
   export LINKEDIN_USERNAME="your_email"
   export LINKEDIN_PASSWORD="your_password"

   # Windows (PowerShell)
   $env:LINKEDIN_USERNAME="your_email"
   $env:LINKEDIN_PASSWORD="your_password"
   ```

   Then set `MANUAL_LOGIN = False`.

## Usage

```bash
python linkedin_scraper.py
```

With `MANUAL_LOGIN = True`, a Chrome window opens on the LinkedIn login page. Log in within the **120-second** pause (complete any CAPTCHA or 2FA), and the script will start scraping automatically.

## Output

A CSV with the following columns:

| Column | Description |
|---|---|
| Serial Number | Row index |
| Source | Input URL |
| LinkedIn Name | Company name |
| LinkedIn HC | Headcount (digits only) |
| LinkedIn U_id | Company URL containing the numeric ID |
| Countries | `Country:Count` pairs separated by `;` |

Example row:

```
1, https://www.linkedin.com/company/example-inc/people/, Example Inc, 1250, https://www.linkedin.com/company/12345, India:600; United States:300; United Kingdom:80
```

## How It Works

1. Loads URLs from the input CSV
2. Launches Chrome and logs in (manual or automated)
3. For each URL, loads the People page and parses the company name and headcount with Selenium
4. Extracts the company ID from the employee search link
5. Parses the country bar graph with BeautifulSoup, keeping only entries that match a country list (cities and regions are filtered out)
6. Writes all results to the output CSV

## Troubleshooting

- **Elements not found / timeouts:** LinkedIn changes its HTML class names often. If extraction fails, inspect the page and update the class names in `scrape_company()` and `extract_countries()`.
- **Login issues / CAPTCHA:** Use `MANUAL_LOGIN = True` and complete verification by hand.
- **Missing countries:** A location is only included if it exactly matches a name in `WORLD_COUNTRIES`. Add alternate spellings to that set if needed.
- **Rate limiting:** Keep batches small and avoid reducing the built-in delays.

## Disclaimer

This project is for educational and personal use. Scraping LinkedIn may violate [LinkedIn's User Agreement](https://www.linkedin.com/legal/user-agreement), and your account could be restricted or banned. Use it at your own risk, scrape responsibly and at low volume, and never commit credentials to version control.

## License

Add a license of your choice (e.g. MIT) in a `LICENSE` file.
