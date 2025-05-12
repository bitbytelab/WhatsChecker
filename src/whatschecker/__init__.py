#!/usr/bin/env python3
import os
import sys
import time
import random
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

__version__ = "0.0.1"

def init_driver(profile_dir: str, proxy: str = None, headless: bool = False):
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    return uc.Chrome(options=options, headless=headless)

def wait_for_login(delay: int = 20):
    print(f"[!] Waiting {delay} seconds for QR code scan...")
    time.sleep(delay)

def check_whatsapp_number(driver, number: str) -> bool | None:
    url = f"https://wa.me/{number.lstrip('+')}"
    driver.get(url)
    time.sleep(3)
    try:
        driver.find_element(By.ID, "action-button").click()
        time.sleep(3)
        driver.find_element(By.XPATH, "//div[contains(text(), 'Phone number shared via url is invalid')]")
        return False
    except NoSuchElementException:
        return True
    except Exception as e:
        print(f"[x] Unexpected error checking {number}: {e}")
        return None

def append_to_file(filename: str, number: str):
    with open(filename, "a+") as f:
        f.write(number + "\n")

def process_numbers(account_profile, numbers, proxy, args, thread_id):
    print(f"[Thread-{thread_id}] Starting with profile: {account_profile}")
    Path(account_profile).mkdir(parents=True, exist_ok=True)
    driver = init_driver(account_profile, proxy, headless=args.headless)

    wait_for_login()

    for number in numbers:
        print(f"[Thread-{thread_id}] Checking: {number}")
        result = check_whatsapp_number(driver, number)
        if result is True:
            print(f"[✓] ACTIVE: {number}")
            append_to_file(args.valid, number)
        elif result is False:
            print(f"[✗] INACTIVE: {number}")
            append_to_file(args.invalid, number)
        else:
            print(f"[!] SKIPPED: {number}")

        delay = args.delay + random.randint(0, 10)
        time.sleep(delay)

    driver.quit()
    print(f"[Thread-{thread_id}] Done.")

def chunkify(lst, n):
    """Split list `lst` into `n` roughly equal parts"""
    return [lst[i::n] for i in range(n)]

def parse_args():
    parser = argparse.ArgumentParser(description="Concurrent WhatsApp number checker via WhatsApp Web")
    parser.add_argument("--input", required=True, help="Input file with phone numbers (one per line)")
    parser.add_argument("--accounts", required=True, nargs="+", help="List of account profile folders")
    parser.add_argument("--proxies", nargs="*", help="Optional list of proxies (one per account)")
    parser.add_argument("--valid", default="valid_numbers.txt", help="Output file for active numbers")
    parser.add_argument("--invalid", default="invalid_numbers.txt", help="Output file for inactive numbers")
    parser.add_argument("--delay", type=int, default=15, help="Base delay between checks (in seconds)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    return parser.parse_args()

def main():
    args = parse_args()

    with open(args.input, "r") as f:
        numbers = [line.strip() for line in f if line.strip()]

    num_threads = len(args.accounts)
    proxy_list = args.proxies or [None] * num_threads
    number_chunks = chunkify(numbers, num_threads)

    print(f"[+] Launching {num_threads} threads for checking {len(numbers)} numbers...")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i, (account, chunk) in enumerate(zip(args.accounts, number_chunks)):
            proxy = proxy_list[i] if i < len(proxy_list) else None
            executor.submit(process_numbers, account, chunk, proxy, args, i + 1)

if __name__ == "__main__":
    try:
        import undetected_chromedriver as uc
    except ImportError:
        print(f"undetected_chromedriver not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "undetected-chromedriver"])

    try:
        from selenium.webdriver.common.by import By
    except ImportError:
        print(f"selenium not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])

    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException

    main()
