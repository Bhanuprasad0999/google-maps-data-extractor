import time
from urllib.parse import quote_plus

from fastapi import FastAPI, HTTPException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


app = FastAPI(
    title="Google Maps Data Extractor",
    version="1.0.0"
)


def scrape_google_maps(place_name: str):

    driver = None

    try:

        print("Starting Google Maps scraper...", flush=True)

        options = Options()

        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--window-size=1920,1080")

        print("Starting Chrome...", flush=True)

        driver = webdriver.Chrome(
            options=options
        )

        print(
            "Chrome started successfully",
            flush=True
        )

        url = (
            "https://www.google.com/maps/search/"
            + quote_plus(place_name)
        )

        print(
            "Opening:",
            url,
            flush=True
        )

        driver.get(url)

        time.sleep(6)

        try:

            first_result = WebDriverWait(
                driver,
                15
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'a[href*="/maps/place/"]'
                    )
                )
            )

            driver.execute_script(
                "arguments[0].click();",
                first_result
            )

            time.sleep(5)

        except Exception as error:

            print(
                "First result click failed:",
                error,
                flush=True
            )

        result_place_name = place_name

        for selector in [
            "h1.DUwDvf",
            "h1.fontHeadlineLarge",
            "h1"
        ]:

            try:

                element = driver.find_element(
                    By.CSS_SELECTOR,
                    selector
                )

                if element.text.strip():

                    result_place_name = (
                        element.text.strip()
                    )

                    break

            except Exception:
                continue

        address = ""

        for selector in [
            'button[data-item-id="address"]',
            'button[aria-label*="Address"]',
            'div[data-item-id="address"]'
        ]:

            try:

                element = driver.find_element(
                    By.CSS_SELECTOR,
                    selector
                )

                address = element.text.strip()

                if address:
                    break

            except Exception:
                continue

        rating = ""

        for selector in [
            'div.F7nice span[aria-hidden="true"]',
            'span.ceNzKf',
            'div[role="img"][aria-label*="star"]'
        ]:

            try:

                element = driver.find_element(
                    By.CSS_SELECTOR,
                    selector
                )

                rating = element.text.strip()

                if not rating:

                    rating = (
                        element.get_attribute(
                            "aria-label"
                        ) or ""
                    )

                if rating:
                    break

            except Exception:
                continue

        review_selectors = [
            'button[jsaction*="pane.reviewChart.moreReviews"]',
            'button[aria-label*="reviews" i]',
            'button[aria-label*="review" i]',
            'div[role="button"][aria-label*="reviews" i]',
            'div[role="button"][aria-label*="review" i]',
            'a[href*="/reviews"]',
            'a[href*="reviews"]'
        ]

        review_count = ""

        for selector in review_selectors:

            try:

                element = driver.find_element(
                    By.CSS_SELECTOR,
                    selector
                )

                text = element.text.strip()

                if text:
                    review_count = text

                driver.execute_script(
                    "arguments[0].click();",
                    element
                )

                time.sleep(4)

                break

            except Exception:
                continue

        print(
            "Scrolling reviews...",
            flush=True
        )

        for _ in range(5):

            try:

                driver.execute_script(
                    """
                    const feeds =
                        document.querySelectorAll(
                            'div[role="feed"]'
                        );

                    feeds.forEach(feed => {
                        feed.scrollTop = feed.scrollHeight;
                    });
                    """
                )

                time.sleep(2)

            except Exception:
                pass

        review_elements = driver.find_elements(
            By.CSS_SELECTOR,
            'div[data-review-id], div.jftiEf'
        )

        print(
            "Reviews found:",
            len(review_elements),
            flush=True
        )

        reviews = []
        seen = set()

        for review in review_elements:

            try:

                reviewer = ""

                for selector in [
                    ".d4r55",
                    ".WNxzHc",
                    '[class*="d4r55"]',
                    '[class*="WNxzHc"]'
                ]:

                    try:

                        element = review.find_element(
                            By.CSS_SELECTOR,
                            selector
                        )

                        reviewer = (
                            element.text.strip()
                        )

                        if reviewer:
                            break

                    except Exception:
                        continue

                review_rating = ""

                for selector in [
                    "span.kvMYJc",
                    '[role="img"]',
                    '[aria-label*="star" i]',
                    'span[aria-label*="star" i]'
                ]:

                    try:

                        element = review.find_element(
                            By.CSS_SELECTOR,
                            selector
                        )

                        review_rating = (
                            element.get_attribute(
                                "aria-label"
                            )
                            or element.text.strip()
                        )

                        if review_rating:
                            break

                    except Exception:
                        continue

                review_text = ""

                for selector in [
                    ".wiI7pd",
                    ".MyEned",
                    '[class*="wiI7pd"]',
                    '[class*="MyEned"]'
                ]:

                    try:

                        element = review.find_element(
                            By.CSS_SELECTOR,
                            selector
                        )

                        review_text = (
                            element.text.strip()
                        )

                        if review_text:
                            break

                    except Exception:
                        continue

                unique_key = (
                    reviewer
                    + "|"
                    + review_text
                )

                if (
                    not review_text
                    or unique_key in seen
                ):
                    continue

                seen.add(unique_key)

                reviews.append(
                    {
                        "reviewer": reviewer,
                        "rating": review_rating,
                        "review": review_text
                    }
                )

            except Exception:
                continue

        return {
            "place": result_place_name,
            "address": address,
            "rating": rating,
            "review_count": review_count,
            "reviews": reviews
        }

    except Exception as error:

        print(
            "Scraper error:",
            error,
            flush=True
        )

        raise

    finally:

        if driver:

            try:

                driver.quit()

                print(
                    "Chrome closed",
                    flush=True
                )

            except Exception:
                pass


@app.get("/")
def home():

    return {
        "message": "Google Maps Scraping API is running"
    }


@app.get("/place")
def get_place(name: str):

    print(
        f"Received place request: {name}",
        flush=True
    )

    try:

        return scrape_google_maps(name)

    except Exception as error:

        print(
            "ERROR:",
            error,
            flush=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )