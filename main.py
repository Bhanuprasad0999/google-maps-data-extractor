import time
import re

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Google Maps Scraping API",
    version="1.0.0"
)


# ============================================================
# MODELS
# ============================================================

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


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    if not text:
        return None

    text = text.replace("", "")
    text = " ".join(text.split())

    return text.strip()


# ============================================================
# GET PLACE NAME
# ============================================================

def get_place_name(driver, search_name):

    try:

        element = WebDriverWait(
            driver, 15
        ).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1.DUwDvf")
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


# ============================================================
# GET ADDRESS
# ============================================================

def get_address(driver):

    selectors = [
        'button[data-item-id="address"]',
        'button[data-item-id*="address"]'
    ]

    for selector in selectors:

        try:

            element = driver.find_element(
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

    return None


# ============================================================
# GET RATING
# ============================================================

def get_rating(driver):

    try:

        element = driver.find_element(
            By.CSS_SELECTOR,
            'div.F7nice span[aria-hidden="true"]'
        )

        return clean_text(
            element.text
        )

    except Exception:

        return None


# ============================================================
# GET REVIEW COUNT
# ============================================================

def get_review_count(driver):

    # Method 1
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
                    r"([\d,]+)",
                    aria
                )

                if match:
                    return match.group(1)

    except Exception:
        pass


    # Method 2
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
                    r"[\d,]+",
                    text
                )

                if len(numbers) >= 2:
                    return numbers[-1]

    except Exception:
        pass


    return None


# ============================================================
# OPEN REVIEWS
# ============================================================

def open_reviews(driver):

    selectors = [

        'button[jsaction*="pane.reviewChart.moreReviews"]',

        'button[aria-label*="reviews"]',

        'button[aria-label*="Reviews"]',

        'div.F7nice button'

    ]


    for selector in selectors:

        try:

            buttons = driver.find_elements(
                By.CSS_SELECTOR,
                selector
            )

            for button in buttons:

                try:

                    driver.execute_script(
                        """
                        arguments[0].scrollIntoView({
                            block: 'center'
                        });
                        """,
                        button
                    )

                    time.sleep(1)


                    driver.execute_script(
                        "arguments[0].click();",
                        button
                    )

                    time.sleep(4)


                    reviews = driver.find_elements(
                        By.CSS_SELECTOR,
                        "div.jftiEf"
                    )

                    if reviews:

                        print(
                            "Reviews opened:",
                            len(reviews)
                        )

                        return True

                except Exception:
                    continue

        except Exception:
            continue


    print("Could not open reviews")

    return False


# ============================================================
# GET REVIEWER NAME
# ============================================================

def get_reviewer_name(review):

    selectors = [
        ".d4r55",
        ".WNxzHc"
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


# ============================================================
# GET REVIEW RATING
# ============================================================

def get_review_rating(review):

    # Method 1
    try:

        element = review.find_element(
            By.CSS_SELECTOR,
            "span.kvMYJc"
        )

        aria = element.get_attribute(
            "aria-label"
        )

        if aria:

            match = re.search(
                r"(\d+(?:\.\d+)?)",
                aria
            )

            if match:

                value = match.group(1)

                if value == "1":
                    return "1 star"

                return value + " stars"

    except Exception:
        pass


    # Method 2
    try:

        elements = review.find_elements(
            By.CSS_SELECTOR,
            '[role="img"]'
        )

        for element in elements:

            aria = element.get_attribute(
                "aria-label"
            )

            if aria and "star" in aria.lower():

                match = re.search(
                    r"(\d+(?:\.\d+)?)",
                    aria
                )

                if match:

                    value = match.group(1)

                    if value == "1":
                        return "1 star"

                    return value + " stars"

    except Exception:
        pass


    return None


# ============================================================
# GET REVIEW TEXT
# ============================================================

def get_review_text(review):

    selectors = [
        ".wiI7pd",
        ".MyEned"
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


# ============================================================
# EXTRACT REVIEWS
# ============================================================

def extract_reviews(driver, reviews, collected):

    review_elements = driver.find_elements(
        By.CSS_SELECTOR,
        "div.jftiEf"
    )


    print(
        "Reviews currently loaded:",
        len(review_elements)
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


            # Unique review

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


        except Exception as error:

            print(
                "Review error:",
                error
            )


# ============================================================
# FIND REVIEW SCROLL CONTAINER
# ============================================================

def find_scroll_container(driver):

    reviews = driver.find_elements(
        By.CSS_SELECTOR,
        "div.jftiEf"
    )


    if not reviews:
        return None


    first_review = reviews[0]


    try:

        container = driver.execute_script(

            """
            let element = arguments[0];

            while (element) {

                if (
                    element.scrollHeight >
                    element.clientHeight
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
            return container

    except Exception:
        pass


    return None


# ============================================================
# SCRAPE REVIEWS
# ============================================================

def scrape_reviews(driver):

    reviews = []
    collected = set()


    # --------------------------------------------------------
    # OPEN REVIEWS
    # --------------------------------------------------------

    if not open_reviews(driver):

        return reviews


    # --------------------------------------------------------
    # WAIT FOR REVIEWS
    # --------------------------------------------------------

    try:

        WebDriverWait(
            driver,
            15
        ).until(

            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "div.jftiEf"
                )
            )

        )

    except Exception:

        print(
            "No reviews found"
        )

        return reviews


    # --------------------------------------------------------
    # SCROLL CONTAINER
    # --------------------------------------------------------

    scrollable = find_scroll_container(
        driver
    )


    # --------------------------------------------------------
    # INITIAL REVIEWS
    # --------------------------------------------------------

    extract_reviews(
        driver,
        reviews,
        collected
    )


    # --------------------------------------------------------
    # SCROLL REVIEWS
    # --------------------------------------------------------

    if scrollable:

        for i in range(15):

            print(
                "Scroll:",
                i + 1
            )


            try:

                driver.execute_script(

                    """
                    arguments[0].scrollTop =
                    arguments[0].scrollHeight;
                    """,

                    scrollable

                )

                time.sleep(2)


                extract_reviews(
                    driver,
                    reviews,
                    collected
                )


            except Exception as error:

                print(
                    "Scroll error:",
                    error
                )

                break


    print(
        "TOTAL REVIEWS:",
        len(reviews)
    )


    return reviews


# ============================================================
# MAIN GOOGLE MAPS SCRAPER
# ============================================================

def get_place_from_google(place_name):

    # --------------------------------------------------------
    # CHROME
    # --------------------------------------------------------

    options = Options()

    # First test without headless
    # After working, uncomment this line

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


    driver = webdriver.Chrome(
        options=options
    )


    try:

        # ====================================================
        # SEARCH GOOGLE MAPS
        # ====================================================

        search_name = place_name.replace(
            " ",
            "+"
        )


        url = (
            "https://www.google.com/maps/search/"
            + search_name
        )


        print(
            "Opening:",
            url
        )


        driver.get(url)

        time.sleep(6)


        # ====================================================
        # CLICK FIRST RESULT
        # ====================================================

        try:

            results = driver.find_elements(

                By.CSS_SELECTOR,

                'div[role="feed"] '
                'a[href*="/maps/place/"]'

            )


            print(
                "Search results:",
                len(results)
            )


            if results:

                driver.execute_script(
                    "arguments[0].click();",
                    results[0]
                )

                time.sleep(5)


        except Exception as error:

            print(
                "Result error:",
                error
            )


        # ====================================================
        # PLACE NAME
        # ====================================================

        name = get_place_name(
            driver,
            place_name
        )


        # ====================================================
        # ADDRESS
        # ====================================================

        address = get_address(
            driver
        )


        # ====================================================
        # RATING
        # ====================================================

        rating_value = get_rating(
            driver
        )


        # ====================================================
        # REVIEW COUNT
        # ====================================================

        review_count = get_review_count(
            driver
        )


        # ====================================================
        # FINAL RATING
        # ====================================================

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


        # ====================================================
        # REVIEWS
        # ====================================================

        reviews = scrape_reviews(
            driver
        )


        # ====================================================
        # FINAL JSON
        # ====================================================

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

        driver.quit()


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def home():

    return {
        "message":
            "Google Maps Scraping API is running"
    }


# ============================================================
# PLACE API
# ============================================================

@app.get(
    "/place",
    response_model=PlaceResponse
)
async def get_place(
    name: str = Query(...)
):

    try:

        return get_place_from_google(
            name
        )

    except Exception as error:

        print(
            "ERROR:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )