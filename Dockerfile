FROM python:3.11-slim

# ==================================================
# SYSTEM DEPENDENCIES
# ==================================================

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libu2f-udev \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*


# ==================================================
# INSTALL CHROME + MATCHING CHROMEDRIVER
# ==================================================

RUN python - <<'PY'
import json
import urllib.request
import zipfile
import io

url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

with urllib.request.urlopen(url) as response:
    data = json.load(response)

version = None
chrome_url = None
driver_url = None

for item in reversed(data["versions"]):

    chrome_downloads = (
        item.get("downloads", {})
        .get("chrome", [])
    )

    driver_downloads = (
        item.get("downloads", {})
        .get("chromedriver", [])
    )

    chrome_linux_url = None
    driver_linux_url = None

    for download in chrome_downloads:
        if download["platform"] == "linux64":
            chrome_linux_url = download["url"]
            break

    for download in driver_downloads:
        if download["platform"] == "linux64":
            driver_linux_url = download["url"]
            break

    if chrome_linux_url and driver_linux_url:
        version = item["version"]
        chrome_url = chrome_linux_url
        driver_url = driver_linux_url
        break

print("Chrome version:", version)
print("Chrome URL:", chrome_url)
print("ChromeDriver URL:", driver_url)

# Download Chrome
chrome_data = urllib.request.urlopen(chrome_url).read()

with zipfile.ZipFile(io.BytesIO(chrome_data)) as z:
    z.extractall("/opt")

# Download ChromeDriver
driver_data = urllib.request.urlopen(driver_url).read()

with zipfile.ZipFile(io.BytesIO(driver_data)) as z:
    z.extractall("/opt")

PY


# ==================================================
# CREATE COMMAND LINKS
# ==================================================

RUN ln -s /opt/chrome-linux64/chrome /usr/local/bin/google-chrome

RUN ln -s /opt/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver

RUN chmod +x /opt/chrome-linux64/chrome

RUN chmod +x /opt/chromedriver-linux64/chromedriver


# ==================================================
# VERIFY CHROME INSTALLATION
# ==================================================

RUN google-chrome --version && chromedriver --version


# ==================================================
# APPLICATION
# ==================================================

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


# ==================================================
# PORT
# ==================================================

EXPOSE 8000


# ==================================================
# START FASTAPI
# ==================================================

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]