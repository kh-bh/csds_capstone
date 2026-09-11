import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def setup_driver():
    """Configures Chrome with options to bypass basic automated browser detection."""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


def scrape_yelp_hospital_reviews(hospital_url, max_pages=1):
    """
    Navigates a Yelp business URL, handles pagination, and extracts review details.
    """
    driver = setup_driver()
    all_reviews = []

    try:
        for page in range(max_pages):
            # Yelp paginates using the 'start' query parameter in increments of 10
            pagination_url = f"{hospital_url}?start={page * 10}"
            print(f"Navigating to page {page + 1}: {pagination_url}")
            driver.get(pagination_url)

            # Wait for review section elements to load into the DOM
            time.sleep(3)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//p[contains(@class, 'comment')]"))
                )
            except Exception:
                print("Timeout waiting for reviews to load, or page has no reviews.")
                break

            # Find review blocks using resilient attribute substring matching
            review_blocks = driver.find_elements(
                By.XPATH, "//li[.//p[contains(@class, 'comment')]]"
            )

            if not review_blocks:
                print("No review blocks identified on this page.")
                break

            for block in review_blocks:
                # Author Name
                try:
                    author_elem = block.find_element(
                        By.XPATH, ".//a[contains(@href, '/user_details') or contains(@class, 'user-name')]"
                    )
                    author = author_elem.text
                except Exception:
                    author = "Anonymous"

                # Star Rating
                try:
                    rating_elem = block.find_element(
                        By.XPATH, ".//div[contains(@aria-label, 'star rating')]"
                    )
                    rating = rating_elem.get_attribute("aria-label")
                except Exception:
                    rating = "N/A"

                # Review Date
                try:
                    date_elem = block.find_element(
                        By.XPATH, ".//span[contains(@class, 'css-') and (contains(text(), '/') or contains(text(), '20'))]"
                    )
                    date = date_elem.text
                except Exception:
                    date = "N/A"

                # Review Text
                try:
                    text_elem = block.find_element(
                        By.XPATH, ".//p[contains(@class, 'comment')]//span"
                    )
                    text = text_elem.text.replace("\n", " ")
                except Exception:
                    text = ""

                if text:
                    all_reviews.append({
                        "author": author,
                        "rating": rating,
                        "date": date,
                        "text": text
                    })

            print(f"Extracted {len(review_blocks)} reviews from page {page + 1}.")

    finally:
        driver.quit()

    return all_reviews


def save_reviews_to_csv(reviews, output_filename="yelp_hospital_reviews.csv"):
    """Saves extracted review dictionaries to a local CSV file."""
    if not reviews:
        print("No reviews to save.")
        return

    fieldnames = ["author", "rating", "date", "text"]
    with open(output_filename, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reviews)

    print(f"\nSuccessfully saved {len(reviews)} reviews to {output_filename}")


if __name__ == "__main__":
    # Example Yelp URL for a hospital
    TARGET_YELP_URL = "https://www.yelp.com/biz/newyork-presbyterian-lower-manhattan-hospital-new-york"
    
    # Scrape 2 pages (20 reviews maximum)
    scraped_data = scrape_yelp_hospital_reviews(TARGET_YELP_URL, max_pages=2)
    save_reviews_to_csv(scraped_data)