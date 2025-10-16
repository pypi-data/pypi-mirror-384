# web_scraper_to_memory.py
# Updated web scraper that saves structured person entries into memory.json
# - Attempts to save under data["info"]["persons"][<slug_name>] and data["persons"][<slug_name>] for compatibility
# - Makes a backup of memory.json before writing
# - Keeps existing keys intact
# Requirements: selenium, webdriver-manager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import re
import shutil
import unicodedata

MEMORY_FILE = "memory.json"
BACKUP_FILE = MEMORY_FILE + ".bak"

# ---------- Chrome Setup ----------
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0.0.0 Safari/537.36"
)

# ---------- Helpers for person detection & DOB extraction ----------
MONTHS_REGEX = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DOB_PATTERNS = [
    rf"\b\d{{1,2}}\s+{MONTHS_REGEX}\s+\d{{4}}\b",
    rf"\b{MONTHS_REGEX}\s+\d{{1,2}},?\s+\d{{4}}\b",
    r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",
    r"\b(?:born|b\.|b\.)\s+(?:in\s+)?\d{4}\b",
    r"\b(19|20)\d{2}\b",
]

QUESTION_WORDS = {"what", "who", "when", "where", "how", "why", "is", "are", "do", "did"}


def slugify_name(name: str) -> str:
    """Create a safe key for JSON: lowercase, ascii, spaces -> underscore."""
    n = name.strip().lower()
    # normalize unicode
    n = unicodedata.normalize('NFKD', n)
    n = n.encode('ascii', 'ignore').decode('ascii')
    n = re.sub(r"[^a-z0-9\s-]", "", n)
    n = re.sub(r"[\s-]+", "_", n).strip('_')
    return n or name


def looks_like_person_query(query: str) -> bool:
    if not query:
        return False
    q = query.strip()
    tokens = q.split()
    if len(tokens) < 1 or len(tokens) > 4:
        return False
    if tokens[0].lower() in QUESTION_WORDS:
        return False
    alpha_tokens = [t for t in tokens if re.match(r"^[A-Za-z\-']+$", t)]
    return len(alpha_tokens) == len(tokens) and len(tokens) >= 1


def extract_dob_from_paragraphs(paragraphs):
    joined = "\n".join(paragraphs)
    for pat in DOB_PATTERNS:
        matches = re.findall(pat, joined, flags=re.IGNORECASE)
        if matches:
            m = matches[0]
            if isinstance(m, tuple):
                m = " ".join([x for x in m if x])
            return m.strip()
    return None


def first_about_paragraph(paragraphs):
    if not paragraphs:
        return None
    for p in paragraphs:
        if len(p) > 80:
            return p
    return paragraphs[0]


def is_useful(text):
    text_lower = text.lower()
    return (
        len(text) > 50
        and not any(
            word in text_lower
            for word in [
                "login", "subscribe", "advertisement", "cookie",
                "policy", "terms", "copyright", "menu",
                "follow us", "newsletter", "advertising"
            ]
        )
        and not text.startswith("By ")
    )


# ---------- Memory file helpers ----------

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {MEMORY_FILE}: {e}")
        return {}


def backup_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            shutil.copy2(MEMORY_FILE, BACKUP_FILE)
            print(f"🔁 Backup created: {BACKUP_FILE}")
    except Exception as e:
        print(f"⚠️ Failed to create backup: {e}")


def save_person_to_memory(raw_name, dob, about, paragraphs):
    name_key = slugify_name(raw_name)
    entry = {
        "name": raw_name,
        "dob": dob,
        "about": about,
        "info": paragraphs
    }

    data = load_memory()
    backup_memory()

    # Ensure compatibility structures exist
    if 'info' not in data or not isinstance(data['info'], dict):
        data['info'] = {}
    if 'persons' not in data['info'] or not isinstance(data['info']['persons'], dict):
        data['info']['persons'] = {}
    if 'persons' not in data or not isinstance(data['persons'], dict):
        data['persons'] = {}

    # Save in both places for compatibility
    data['info']['persons'][name_key] = entry
    

    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Saved structured person entry for '{raw_name}' as key '{name_key}' in {MEMORY_FILE}")
    except Exception as e:
        print(f"❌ Failed to write memory file: {e}")


def save_info_to_memory(query, paragraphs):
    data = load_memory()
    backup_memory()
    if 'info' not in data or not isinstance(data['info'], dict):
        data['info'] = {}
    data['info'][query] = paragraphs
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Saved {len(paragraphs)} paragraphs for '{query}' in {MEMORY_FILE}")
    except Exception as e:
        print(f"❌ Failed to write memory file: {e}")


# ---------- Main Fetch Function ----------

def fetch_top_website_data(query):
    print(f"\n🔍 Searching Google for: {query}\n")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(f"https://www.google.com/search?q={query}")
    time.sleep(2)

    try:
        consent = driver.find_element(By.XPATH, "//button[contains(text(),'I agree') or contains(text(),'I Accept') or contains(text(),'Accept all')]")
        consent.click()
        time.sleep(1)
    except Exception:
        pass

    links = []
    try:
        results = driver.find_elements(By.CSS_SELECTOR, "div.tF2Cxc")
        for r in results[:4]:
            try:
                title_elem = r.find_element(By.TAG_NAME, "h3")
                link_elem = title_elem.find_element(By.XPATH, "..")
                link = link_elem.get_attribute("href")
                if link:
                    links.append(link)
            except Exception:
                continue
    except Exception:
        pass

    if not links:
        print("⚠️ No valid search results found.")
        driver.quit()
        return

    person_like = looks_like_person_query(query)
    if person_like:
        print("🔎 Query looks like a PERSON name (heuristic). Will try structured save (persons).")

    for idx, link in enumerate(links, start=1):
        try:
            print(f"🌐 Trying website #{idx}: {link}")
            driver.get(link)
            time.sleep(2)

            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            useful_paragraphs = [p.text.strip() for p in paragraphs if is_useful(p.text.strip())]

            if len(useful_paragraphs) < 3:
                headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
                for h in headings:
                    t = h.text.strip()
                    if t and len(t) > 30 and t not in useful_paragraphs:
                        useful_paragraphs.append(t)
                seen = set()
                useful_paragraphs = [x for x in useful_paragraphs if not (x in seen or seen.add(x))]

            if len(useful_paragraphs) >= 1:
                print(f"✅ Extracted {len(useful_paragraphs)} useful paragraphs from link #{idx}!")
                for i, para in enumerate(useful_paragraphs[:6], start=1):
                    print(f"{i}. {para[:200]}...\n")

                if person_like:
                    dob = extract_dob_from_paragraphs(useful_paragraphs)
                    about = first_about_paragraph(useful_paragraphs)
                    save_person_to_memory(query, dob, about, useful_paragraphs)
                else:
                    save_info_to_memory(query, useful_paragraphs)
                break
            else:
                print(f"⚠️ Link #{idx} didn't return enough useful data. Trying next...\n")

        except Exception as e:
            print(f"⚠️ Error on link #{idx}: {e}\nTrying next...\n")
            continue
    else:
        print("❌ All top websites failed to return valid data.")

    driver.quit()
    print("✅ Browser closed safely.\n")

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        fetch_top_website_data(query)
    else:
        print("Usage: python web_auto.py \"<search query>\"")

