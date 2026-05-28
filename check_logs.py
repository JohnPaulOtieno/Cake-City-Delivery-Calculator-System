import sys
import os

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    import time

    options = Options()
    options.add_argument('--headless')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    driver = webdriver.Chrome(options=options)
    driver.get('http://127.0.0.1:8000/deliveries/new/')
    time.sleep(3) # Wait for maps to load and fail

    for entry in driver.get_log('browser'):
        print(f"[{entry['level']}] {entry['message']}")
    
    driver.quit()
except ImportError:
    print("Selenium not installed")
