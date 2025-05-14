#!/usr/bin/env python3
import os
import csv
import sys
import time
import json
import shutil
import random
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from .logger_setup import setup_logger

__VERSION__ = "0.0.4"


def init_driver(profile_dir: str, proxy: str = None, headless: bool = False):
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-features=IntentHandling")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("prefs", {
        "protocol_handler.external.whatsapp": False,  # Block WhatsApp protocol handler
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.popups": 0
    })

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1200,700")

    return uc.Chrome(options=options, headless=headless)


def wait_for_whatsapp_loaded(driver, timeout=90):
    print("[ * ] Waiting for WhatsApp Loading to finish...")
    wait = WebDriverWait(driver, timeout)

    def loading_still_visible(driver):
        try:
            app_div = driver.find_element(By.ID, "app")
            loading_texts = ["End-to-end encrypted", "Your messages are downloading"]
            return any(text in app_div.text for text in loading_texts)
        except:
            return True  # If #app is not found, assume still loading

    wait.until_not(loading_still_visible)
    print("[ + ] WhatsApp finished loading...")


def wait_for_login(driver, timeout: int = 180):
    print("[ * ] Waiting for WhatsApp Web Login...")

    driver.get("https://web.whatsapp.com")

    try:
        print("[ ! ] Checking login status")
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-js-navbar="true"]')),
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
            )
        )
        print("[ + ] Successfully logged into WhatsApp Web using saved session.")
        return True
    except TimeoutException:
        print("[ ! ] Checking if login page")
        try:
            # Wait until either QR login or phone number login prompt appears
            WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Log into WhatsApp Web")]')),
                    EC.presence_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]')),
                )
            )
            print(f"[ * ] Login screen detected. Waiting {timeout} seconds for user to log in...")

            WebDriverWait(driver, timeout).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-js-navbar="true"]')),
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
                )
            )

            print("[ + ] Successfully logged into WhatsApp Web.")
            return True
        except Exception as e:
            print(f"[ - ] Login failed or timed out. {e}")


def check_whatsapp_number(driver, number: str) -> bool | None:
    if '@' in number:
        number = number.split('@')[0]

    number = ''.join(_ for _ in number if _ in '0123456789')

    if len(number) == 10:
        number = f"1{number}"

    # url = f"https://wa.me/{number}"
    url = f"https://web.whatsapp.com/send/?phone={number}&text&type=phone_number"
    driver.get(url)
    wait_for_whatsapp_loaded(driver)
    try:
        time.sleep(1)
        driver.find_element(By.XPATH, "//div[contains(text(), 'Phone number shared via url is invalid')]")
        return False
    except NoSuchElementException:
        return True
    except Exception as e:
        print(f"[ x ] Unexpected error checking {number}: {e}")
        return None


def append_to_file(filename: str, number: str):
    with open(filename, "a+") as f:
        f.write(number + "\n")


def process_numbers(account_profile, numbers, proxy, args, thread_id):
    print(f"[Thread-{thread_id}] Starting with profile: {account_profile}")
    Path(account_profile).mkdir(parents=True, exist_ok=True)
    driver = init_driver(account_profile, proxy, headless=args.headless)

    driver.set_window_size(1200, 800)
    if args.headless: driver.maximize_window()

    login_success = wait_for_login(driver)
    if not login_success:
        print(f"[ ! ] Closing webdriver")
        driver.close()
        driver.quit()
        print(f"[ ! ] Removing Account Profile")
        shutil.rmtree(account_profile)
        return

    for number in numbers:
        print(f"[Thread-{thread_id}] Checking: {number}")
        result = check_whatsapp_number(driver, number)
        if result is True:
            print(f"[ ✓ ] ACTIVE: {number}")
            append_to_file(args.valid, number)
        elif result is False:
            print(f"[ ✗ ] INACTIVE: {number}")
            append_to_file(args.invalid, number)
        else:
            print(f"[ ! ] SKIPPED: {number}")
            append_to_file('skipped_numbers.txt', number)

        delay = args.delay + random.randint(0, 10)
        time.sleep(delay)

    driver.close()
    driver.quit()
    print(f"[Thread-{thread_id}] Done.")


def extract_contacts(account_profile, proxy, args, thread_id):
    print(f"[Thread-{thread_id}] Starting with profile: {account_profile}")
    Path(account_profile).mkdir(parents=True, exist_ok=True)
    driver = init_driver(account_profile, proxy, headless=args.headless)

    driver.set_window_size(1200, 800)
    if args.headless: driver.maximize_window()

    login_success = wait_for_login(driver)
    if not login_success:
        print(f"[ ! ] Closing webdriver")
        driver.close()
        driver.quit()
        print(f"[ ! ] Removing Account Profile")
        shutil.rmtree(account_profile)
        return

    wait = WebDriverWait(driver, 30)

    new_chat_btn = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, 'button[aria-label="New chat"][role="button"][title="New chat"]'
    )))
    new_chat_btn.click()
    print("[ ! ] Opened the contact list sidebar.")

    # contact list
    copyable_area = wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, 'div.copyable-area'
    )))
    contacts_container = copyable_area.find_element(By.CSS_SELECTOR, 'div[data-tab="4"]')
    scrollable_div = contacts_container.find_element(By.XPATH, './..')

    seen_items = set()
    contacts_data = []

    prev_item_count = 0
    same_count_retries = 0

    print("[ ! ] Scrolling and collecting contacts...")
    while True:
        list_items = contacts_container.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        for item in list_items:
            time.sleep(random.randint(2, 9) / 100)

            if item.text in seen_items:
                continue
            seen_items.add(item.text)

            try:
                contact_div = item.find_element(By.CSS_SELECTOR, 'div[role="button"]')
            except Exception as e:
                print(f"[###] {item.text.replace('\n', ' || ')}")
                continue
            else:
                contact_text = contact_div.text.replace('\n', ' || ')
                print(f"[ > ] {contact_text}")
                if 'Message yourself' in contact_text:
                    continue

                data = {}
                try:
                    avatar_span = contact_div.find_element(By.CSS_SELECTOR, 'span[data-icon="default-user"] svg')
                    data['user_avatar'] = ''
                except:
                    try:
                        avatar_img = contact_div.find_element(By.CSS_SELECTOR, 'img[draggable="false"]')
                        data['user_avatar'] = avatar_img.get_attribute('src')
                    except:
                        data['user_avatar'] = 'unknown'

                # Name and About
                try:
                    spans = contact_div.find_elements(By.CSS_SELECTOR, 'span[dir="auto"]')
                    if len(spans) >= 1:
                        data['name'] = spans[0].get_attribute('title')
                    if len(spans) >= 2:
                        data['about'] = spans[1].get_attribute('title')
                except:
                    data['name'] = data.get('name', '')
                    data['about'] = data.get('about', '')

                if data.get('name'):
                    contacts_data.append(data)
                    print(f"[{len(contacts_data)}] extracted: {data['name']}")

        current_count = len(seen_items)
        if current_count == prev_item_count:
            same_count_retries += 1
        else:
            same_count_retries = 0

        if same_count_retries >= 3:
            break

        prev_item_count = current_count
        driver.execute_script("arguments[0].scrollIntoView();", list_items[-1])
        time.sleep(random.randint(90, 200) / 100)

    filename = f"valid_whatsapp_contacts_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.csv"
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'about', 'user_avatar'])
        writer.writeheader()
        writer.writerows(contacts_data)

    driver.close()
    driver.quit()
    print(f"[Thread-{thread_id} Done] Extracted {len(contacts_data)} contacts and saved to {filename}")


def extract_chat_list_contacts(account_profile, proxy, args, thread_id):
    print(f"[Thread-{thread_id}] Starting with profile: {account_profile}")
    Path(account_profile).mkdir(parents=True, exist_ok=True)
    driver = init_driver(account_profile, proxy, headless=args.headless)

    driver.set_window_size(1200, 800)
    if args.headless: driver.maximize_window()

    login_success = wait_for_login(driver)
    if not login_success:
        print(f"[ ! ] Closing webdriver")
        driver.close()
        driver.quit()
        print(f"[ ! ] Removing Account Profile")
        shutil.rmtree(account_profile)
        return

    # chat list
    pane_side_div = driver.find_element(By.ID, 'pane-side')
    chat_list_div = pane_side_div.find_element(By.CSS_SELECTOR, 'div[role="grid"][aria-label="Chat list"]')

    seen_items = set()
    contacts_data = []

    prev_item_count = 0
    same_count_retries = 0

    print("[ ! ] Scrolling and collecting Chat list contacts...")
    while True:
        list_items = chat_list_div.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        for item in list_items:
            contact_text = item.text.replace('\n', ' || ')
            print(f"[ > ] {contact_text}")

            if contact_text in seen_items:
                continue

            seen_items.add(contact_text)

            data = {}
            # Avatar logic
            try:
                avatar_span = item.find_element(By.CSS_SELECTOR, 'span[data-icon="default-user"] svg')
                data['user_avatar'] = ''
            except:
                try:
                    avatar_img = item.find_element(By.CSS_SELECTOR, 'img[draggable="false"]')
                    data['user_avatar'] = avatar_img.get_attribute("src")
                except:
                    data['user_avatar'] = 'unknown'

            # Name and About
            try:
                spans = item.find_elements(By.CSS_SELECTOR, 'span[dir="auto"]')
                if len(spans) >= 1:
                    data['name'] = spans[0].get_attribute("title")
                if len(spans) >= 2:
                    data['about'] = spans[1].get_attribute("title")
            except:
                data['name'] = data.get('name', '')
                data['about'] = data.get('about', '')

            if data.get('name'):
                contacts_data.append(data)
                print(f"[{len(contacts_data)}] extracted: {data['name']}")


        current_count = len(seen_items)
        if current_count == prev_item_count:
            same_count_retries += 1
        else:
            same_count_retries = 0

        if same_count_retries >= 3:
            break  # We scrolled 3 times and saw no new content

        prev_item_count = current_count
        driver.execute_script("arguments[0].scrollIntoView();", list_items[-1])
        time.sleep(random.randint(150, 250) / 100)

    filename = f"whatsapp_chatlist_contacts_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.csv"
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'about', 'user_avatar'])
        writer.writeheader()
        writer.writerows(contacts_data)

    driver.close()
    driver.quit()
    print(f"[Thread-{thread_id} Done] Extracted {len(contacts_data)} chatlist contacts and saved to {filename}")


def chunkify(lst, n):
    """Split list `lst` into `n` roughly equal parts"""
    return [lst[i::n] for i in range(n)]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Concurrent WhatsApp number checker via WhatsApp Web"
    )
    parser.add_argument("--input", help="Input file with phone numbers (one per line)")
    parser.add_argument("--proxies", nargs="*", help="Optional list of proxies (one per account)")
    parser.add_argument("--valid", default=None, help="Output file for active numbers")
    parser.add_argument("--invalid", default=None, help="Output file for inactive numbers")
    parser.add_argument("--delay", type=int, default=5, help="Base delay between checks (in seconds)")
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode")
    parser.add_argument("--add-account", action="store_true", help="Add new WhatsApp account(s) via QR login before checking")

    args = parser.parse_args()

    # Load fallback config if needed
    config_path = Path("whatschecker.config.json")
    config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config = json.load(f)

    def get_config_or_prompt(key, prompt_text):
        return getattr(args, key) or config.get(key) or input(prompt_text).strip()

    args.input = get_config_or_prompt("input", "Enter path to input file: ")
    args.valid = args.valid or config.get("valid", "valid_numbers.txt")
    args.invalid = args.invalid or config.get("invalid", "invalid_numbers.txt")
    args.delay = args.delay or config.get("delay", 15)
    args.proxies = args.proxies or config.get("proxies", [])

    # Account profile loading/creation
    base_dir = Path.cwd() / "Profiles"
    base_dir.mkdir(exist_ok=True)

    def get_next_account_dir():
        i = 1
        while (base_dir / f"account{i}").exists():
            i += 1
        return base_dir / f"account{i}"

    if args.add_account:
        print("[ + ] Add new WhatsApp account(s) via QR")
        while True:
            new_profile = get_next_account_dir()
            print(f"[ + ] Launching session for: {new_profile.name}")
            driver = init_driver(str(new_profile), headless=False)  # Force visible for QR
            wait_for_login(driver)
            driver.quit()
            print(f"[ ✓ ] Saved profile: {new_profile.name}")
            choice = input("Add another account? (y/n): ").strip().lower()
            if choice != 'y':
                break

    existing_profiles = sorted(p.name for p in base_dir.iterdir() if p.is_dir() and p.name.startswith("account"))

    if not existing_profiles:
        print("[ ! ] No WhatsApp accounts found. Starting one now...")
        new_profile = get_next_account_dir()
        driver = init_driver(str(new_profile), headless=False)
        wait_for_login(driver)
        driver.quit()
        print(f"[ ✓ ] Saved profile: {new_profile.name}")
        existing_profiles = [new_profile.name]

    args.accounts = [str(base_dir / name) for name in existing_profiles]

    return args


def main():
    args = parse_args()

    # handle special input keywords
    special_keywords = ["contacts", "contact_list", "contacts_only", "saved_contacts", "device_contacts"]
    special_keywords_2 = ["chatlist", "chat-list", "chat_list", "chatlist_contacts", "chat-list-contacts", "chat_list_contacts"]

    if args.input.lower() in special_keywords+special_keywords_2:
        num_threads = len(args.accounts)
        proxy_list = args.proxies or [None] * num_threads

        print(f"[ + ] Launching {num_threads} threads for contacts extraction...")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i, account in enumerate(args.accounts):
                proxy = proxy_list[i] if i < len(proxy_list) else None
                if args.input.lower() in special_keywords_2:
                    executor.submit(extract_chat_list_contacts, account, proxy, args, i + 1)
                else:
                    executor.submit(extract_contacts, account, proxy, args, i + 1)

    else:
        with open(args.input, "r") as f:
            numbers = [line.strip() for line in f if line.strip()]

        num_threads = len(args.accounts)
        proxy_list = args.proxies or [None] * num_threads
        number_chunks = chunkify(numbers, num_threads)

        print(f"[ + ] Launching {num_threads} threads for checking {len(numbers)} numbers...")

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for i, (account, chunk) in enumerate(zip(args.accounts, number_chunks)):
                proxy = proxy_list[i] if i < len(proxy_list) else None
                executor.submit(process_numbers, account, chunk, proxy, args, i + 1)


if __name__ == "__main__":
    logger = setup_logger()

    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools"], stdout=subprocess.DEVNULL)

    try:
        import undetected_chromedriver as uc
    except ImportError:
        print(f"undetected_chromedriver not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "undetected-chromedriver"])
        import undetected_chromedriver as uc

    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        print(f"selenium not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
        from selenium.webdriver.common.by import By

    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    main()
