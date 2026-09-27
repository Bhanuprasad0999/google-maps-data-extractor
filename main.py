import time
import re
import os

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==================================================
# FASTAPI APP
# ==================================================

app = FastAPI(
    title="Google Maps Scraping API",
    version="1.0.0"
)


# ==================================================
# RESPONSE MODELS
# ==================================================

class Review(BaseModel):
    reviewer_name: str
    rating: Optional[str] = None
    review_text: str


class PlaceData(BaseModel):
    name: str
    address: Optional[str] = None
    rating: Optional[str] = None
    reviews: List[Review] = Field(default_factory=list)


class PlaceResponse(BaseModel):
    place: PlaceData


# ==================================================
# CLEAN TEXT
# ==================================================

def clean_text(text):

    if not text:
        return None

    text = text.replace("", "")
    text = " ".join(text.split())

    return text.strip()


# ==================================================
# PLACE NAME
# ==================================================

def get_place_name(driver, search_name):

    try:

        element = WebDriverWait(
            driver,
            15
        ).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "h1.DUwDvf"
                )
            )
        )

        return clean_text(element.text)

    except Exception:

        try:

            element = driver.find_element(
                By.TAG_NAME,
                "h1"
            )

            return clean_text(element.text)

        except Exception:

            return search_name


# ==================================================
# ADDRESS
# ==================================================

def get_address(driver):

    selectors = [
        'button[data-item-id="address"]',
        'button[data-item-id*="address"]',
        '[data-item-id="address"]'
    ]

    for selector in selectors:

        try:

            element = driver.find_element(
                By.CSS_SELECTOR,
                selector
            )

            text = clean_text(element.text)

            if text:
                return text

        except Exception:
            continue

    return None


# ==================================================
# RATING
# ==================================================

def get_rating(driver):

    selectors = [
        'div.F7nice span[aria-hidden="true"]',
        'div.F7nice span',
        '[role="img"][aria-label*="star" i]'
    ]

    for selector in selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            for element in elements:

                text = clean_text(
                    element.text
                )

                if text:

                    match = re.search(
                        r"(\d+(?:\.\d+)?)",
                        text
                    )

                    if match:
                        return match.group(1)

                aria = element.get_attribute(
                    "aria-label"
                )

                if aria:

                    match = re.search(
                        r"(\d+(?:\.\d+)?)",
                        aria
                    )

                    if match:
                        return match.group(1)

        except Exception:
            continue

    return None


# ==================================================
# REVIEW COUNT
# ==================================================

def get_review_count(driver):

    try:

        buttons = driver.find_elements(
            By.XPATH,
            "//button[contains("
            "translate(@aria-label,"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),"
            "'review')]"
        )

        for button in buttons:

            aria = button.get_attribute(
                "aria-label"
            )

            if aria:

                match = re.search(
                    r"(\d[\d,]*)",
                    aria
                )

                if match:

                    value = match.group(1)
                    value = value.replace(",", "")

                    if value.isdigit():
                        return value

    except Exception:
        pass


    try:

        elements = driver.find_elements(
            By.CSS_SELECTOR,
            "div.F7nice"
        )

        for element in elements:

            text = clean_text(
                element.text
            )

            if text:

                numbers = re.findall(
                    r"\d[\d,]*",
                    text
                )

                if len(numbers) >= 2:

                    value = numbers[-1]
                    value = value.replace(",", "")

                    if value.isdigit():
                        return value

    except Exception:
        pass

    return None


# ==================================================
# OPEN REVIEWS
# ==================================================

def open_reviews(driver):

    print(
        "Trying to open reviews...",
        flush=True
    )

    selectors = [

        'button[jsaction*="pane.reviewChart.moreReviews"]',

        'button[aria-label*="reviews" i]',

        'button[aria-label*="review" i]',

        'div[role="button"][aria-label*="reviews" i]',

        'div[role="button"][aria-label*="review" i]',

        'a[href*="/reviews"]',

        'a[href*="reviews"]'
    ]


    for selector in selectors:

        try:

            elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            print(
                "Selector:",
                selector,
                "Found:",
                len(elements),
                flush=True
            )


            for element in elements:

                try:

                    if not element.is_displayed():
                        continue


                    aria = element.get_attribute(
                        "aria-label"
                    )

                    text = clean_text(
                        element.text
                    )

                    print(
                        "Review element:",
                        "aria=",
                        aria,
                        "text=",
                        text,
                        flush=True
                    )


                    driver.execute_script(
                        """
                        arguments[0].scrollIntoView({
                            block: 'center'
                        });
                        """,
                        element
                    )

                    time.sleep(1)


                    driver.execute_script(
                        "arguments[0].click();",
                        element
                    )

                    print(
                        "Review button clicked",
                        flush=True
                    )

                    time.sleep(4)


                    review_elements = driver.find_elements(
                        By.CSS_SELECTOR,
                        'div[data-review-id], div.jftiEf'
                    )


                    print(
                        "Review elements after click:",
                        len(review_elements),
                        flush=True
                    )


                    if review_elements:
                        return True


                except Exception as error:

                    print(
                        "Click error:",
                        error,
                        flush=True
                    )


        except Exception as error:

            print(
                "Selector error:",
                error,
                flush=True
            )


    print(
        "Could not open reviews",
        flush=True
    )

    return False


# ==================================================
# REVIEWER NAME
# ==================================================

def get_reviewer_name(review):

    selectors = [
        ".d4r55",
        ".WNxzHc",
        '[class*="d4r55"]',
        '[class*="WNxzHc"]'
    ]


    for selector in selectors:

        try:

            element = review.find_element(
                By.CSS_SELECTOR,
                selector
            )

            name = clean_text(
                element.text
            )

            if name:
                return name

        except Exception:
            continue


    return "Anonymous"


# ==================================================
# REVIEW RATING
# ==================================================

def get_review_rating(review):

    selectors = [
        "span.kvMYJc",
        '[role="img"]',
        '[aria-label*="star" i]',
        'span[aria-label*="star" i]'
    ]


    for selector in selectors:

        try:

            elements = review.find_elements(
                By.CSS_SELECTOR,
                selector
            )


            for element in elements:

                aria = element.get_attribute(
                    "aria-label"
                )

                if not aria:
                    continue


                if "star" not in aria.lower():
                    continue


                match = re.search(
                    r"(\d+(?:\.\d+)?)",
                    aria
                )


                if match:

                    return (
                        match.group(1)
                        + " stars"
                    )


        except Exception:
            continue


    return None


# ==================================================
# REVIEW TEXT
# ==================================================

def get_review_text(review):

    selectors = [
        ".wiI7pd",
        ".MyEned",
        '[class*="wiI7pd"]',
        '[class*="MyEned"]'
    ]


    for selector in selectors:

        try:

            element = review.find_element(
                By.CSS_SELECTOR,
                selector
            )

            text = clean_text(
                element.text
            )

            if text:
                return text

        except Exception:
            continue


    return ""


# ==================================================
# EXTRACT REVIEWS
# ==================================================

def extract_reviews(
    driver,
    reviews,
    collected
):

    selectors = [
        "div[data-review-id]",
        "div.jftiEf"
    ]


    review_elements = []


    for selector in selectors:

        try:

            review_elements = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            if review_elements:
                break

        except Exception:
            continue


    print(
        "Reviews currently loaded:",
        len(review_elements),
        flush=True
    )


    for review in review_elements:

        try:

            reviewer_name = get_reviewer_name(
                review
            )

            rating = get_review_rating(
                review
            )

            review_text = get_review_text(
                review
            )


            if not review_text:
                continue


            key = (
                reviewer_name
                + "|"
                + review_text
            )


            if key in collected:
                continue


            collected.add(key)


            reviews.append({

                "reviewer_name":
                    reviewer_name,

                "rating":
                    rating,

                "review_text":
                    review_text
            })


            print(
                "Review collected:",
                reviewer_name,
                flush=True
            )


        except Exception as error:

            print(
                "Review extraction error:",
                error,
                flush=True
            )


# ==================================================
# FIND SCROLL CONTAINER
# ==================================================

def find_scroll_container(driver):

    selectors = [
        "div[data-review-id]",
        "div.jftiEf"
    ]


    reviews = []


    for selector in selectors:

        try:

            reviews = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            if reviews:
                break

        except Exception:
            continue


    if not reviews:

        print(
            "No review elements for scroll container",
            flush=True
        )

        return None


    first_review = reviews[0]


    try:

        container = driver.execute_script(
            """
            let element = arguments[0];

            while (element) {

                if (
                    element.scrollHeight >
                    element.clientHeight + 100
                ) {
                    return element;
                }

                element = element.parentElement;
            }

            return null;
            """,
            first_review
        )


        if container:

            print(
                "Review scroll container found",
                flush=True
            )

            return container


    except Exception as error:

        print(
            "Scroll container error:",
            error,
            flush=True
        )


    return None


# ==================================================
# SCRAPE REVIEWS
# ==================================================

def scrape_reviews(driver):

    reviews = []
    collected = set()


    print(
        "Starting review scraping...",
        flush=True
    )


    if not open_reviews(driver):

        print(
            "Review section could not be opened",
            flush=True
        )

        return reviews


    try:

        WebDriverWait(
            driver,
            15
        ).until(

            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'div[data-review-id], div.jftiEf'
                )
            )
        )


    except Exception:

        print(
            "No reviews found after opening review section",
            flush=True
        )

        return reviews


    scrollable = find_scroll_container(
        driver
    )


    extract_reviews(
        driver,
        reviews,
        collected
    )


    # ==================================================
    # FIVE SCROLLS
    # ==================================================

    if scrollable:

        for i in range(5):

            print(
                "Scroll:",
                i + 1,
                flush=True
            )


            try:

                old_count = len(
                    reviews
                )


                driver.execute_script(
                    """
                    arguments[0].scrollTop =
                    arguments[0].scrollTop +
                    arguments[0].clientHeight;
                    """,
                    scrollable
                )


                time.sleep(2)


                extract_reviews(
                    driver,
                    reviews,
                    collected
                )


                print(
                    "Total collected:",
                    len(reviews),
                    flush=True
                )


                if len(reviews) == old_count:

                    time.sleep(1)


            except Exception as error:

                print(
                    "Scroll error:",
                    error,
                    flush=True
                )

                break


    print(
        "TOTAL REVIEWS:",
        len(reviews),
        flush=True
    )


    return reviews


# ==================================================
# GOOGLE MAPS SCRAPER
# ==================================================

def get_place_from_google(place_name):

    print(
        "Starting Google Maps scraper...",
        flush=True
    )


    options = Options()


    # ==================================================
    # CHROME SETTINGS
    # ==================================================

    # Render / Docker uses Chrome installed at this path.
    # Windows uses the normal installed Chrome automatically.
    if os.name != "nt":

        options.binary_location = (
            "/usr/local/bin/google-chrome"
        )


    options.add_argument(
        "--headless=new"
    )

    options.add_argument(
        "--disable-gpu"
    )

    options.add_argument(
        "--no-sandbox"
    )

    options.add_argument(
        "--disable-dev-shm-usage"
    )

    options.add_argument(
        "--window-size=1920,1080"
    )

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    options.add_argument(
        "--disable-extensions"
    )

    options.add_argument(
        "--disable-software-rasterizer"
    )


    # ==================================================
    # START CHROME
    # ==================================================

    print(
        "Starting Chrome...",
        flush=True
    )


    try:

        # Windows local
        if os.name == "nt":

            driver = webdriver.Chrome(
                options=options
            )

        # Render / Docker Linux
        else:

            driver = webdriver.Chrome(

                service=Service(
                    "/usr/local/bin/chromedriver"
                ),

                options=options
            )


        print(
            "Chrome started successfully",
            flush=True
        )


    except Exception as error:

        print(
            "Chrome startup failed:",
            error,
            flush=True
        )

        raise


    try:

        # ==================================================
        # GOOGLE MAPS URL
        # ==================================================

        search_name = place_name.replace(
            " ",
            "+"
        )


        url = (
            "https://www.google.com/maps/search/"
            + search_name
        )


        print(
            "Opening Google Maps:",
            url,
            flush=True
        )


        driver.get(url)


        print(
            "Google Maps page opened",
            flush=True
        )


        time.sleep(6)


        # ==================================================
        # SELECT FIRST SEARCH RESULT
        # ==================================================

        try:

            results = driver.find_elements(
                By.CSS_SELECTOR,
                'div[role="feed"] '
                'a[href*="/maps/place/"]'
            )


            print(
                "Search results:",
                len(results),
                flush=True
            )


            if results:

                driver.execute_script(
                    "arguments[0].click();",
                    results[0]
                )


                print(
                    "First search result clicked",
                    flush=True
                )


                time.sleep(5)


        except Exception as error:

            print(
                "Result selection error:",
                error,
                flush=True
            )


        # ==================================================
        # PLACE INFORMATION
        # ==================================================

        print(
            "Getting place information...",
            flush=True
        )


        name = get_place_name(
            driver,
            place_name
        )


        address = get_address(
            driver
        )


        rating_value = get_rating(
            driver
        )


        review_count = get_review_count(
            driver
        )


        print(
            "Place name:",
            name,
            flush=True
        )


        print(
            "Address:",
            address,
            flush=True
        )


        print(
            "Rating:",
            rating_value,
            flush=True
        )


        print(
            "Review count:",
            review_count,
            flush=True
        )


        # ==================================================
        # BUILD RATING
        # ==================================================

        rating = None


        if rating_value:

            if review_count:

                rating = (
                    rating_value
                    + "("
                    + review_count
                    + ")"
                )

            else:

                rating = rating_value


        # ==================================================
        # REVIEWS
        # ==================================================

        reviews = scrape_reviews(
            driver
        )


        print(
            "Final review count:",
            len(reviews),
            flush=True
        )


        return {

            "place": {

                "name":
                    name,

                "address":
                    address,

                "rating":
                    rating,

                "reviews":
                    reviews
            }
        }


    finally:

        print(
            "Closing Chrome...",
            flush=True
        )

        driver.quit()


# ==================================================
# HOME API
# ==================================================

@app.get("/")
async def home():

    return {
        "message":
            "Google Maps Scraping API is running"
    }


# ==================================================
# PLACE API
# ==================================================

@app.get(
    "/place",
    response_model=PlaceResponse
)
async def get_place(
    name: str = Query(...)
):

    print(
        "Received place request:",
        name,
        flush=True
    )


    try:

        result = get_place_from_google(
            name
        )


        print(
            "Request completed successfully",
            flush=True
        )


        return result


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


# ==================================================
# LOCAL RUN
# ==================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )