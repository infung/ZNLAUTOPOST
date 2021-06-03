import json
import time

import selenium.webdriver as webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class WebDriver:
    @staticmethod
    def chrome():
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        # change windows size if too large
        options.add_argument("--window-size=1280,720")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        # to disable dumbass notification
        options.add_experimental_option("prefs",
                                        {"profile.default_content_setting_values.notifications": 2
                                         })

        # To unblock website that blocks headless chrome
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')

        driver = webdriver.Chrome('./chromedriver.exe', chrome_options=options)

        return driver


def wait_element_to_present(driver, delay, element):
    try:
        element = WebDriverWait(driver, delay).until(EC.presence_of_element_located(element))
        print('page ready')
    except TimeoutException:
        print('fked up here')


def main():
    driver = WebDriver.chrome()

    try:
        driver.get('https://weibo.com/login.php')

        wait_element_to_present(driver, 60, (By.ID, 'v6_pl_rightmod_myinfo'))

        inputs = driver.find_elements_by_class_name('W_input')
        post_input = inputs[1]

        buttons = driver.find_elements_by_class_name('W_btn_a')
        post_button = buttons[0]

        with open('./input.json') as f:
            data_list = json.load(f)
            for data in data_list:
                post_input.send_keys(data['text'])

                driver.find_element_by_xpath("//input[contains(@id, 'swf_upbtn')]").send_keys(data['image'])
                time.sleep(5)  # mandatory sleep, wait for file preview

                post_button.click()
                time.sleep(5)  # mandatory sleep, wait for upload
    except Exception as e:
        print(e)
        driver.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()