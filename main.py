import json
import logging
import os
import platform
import random
import sys
import time

import selenium.webdriver as webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='runtime.log',
                    filemode='w')


class WebDriver:
    @staticmethod
    def resource_path(relative_path: str) -> str:
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(__file__)

        return os.path.join(base_path, relative_path)

    @staticmethod
    def chrome():
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        # change windows size if too large
        options.add_argument('--window-size=1280,720')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        # to disable dumbass notification
        options.add_experimental_option('prefs',
                                        {'profile.default_content_setting_values.notifications': 2
                                         })

        # To unblock website that blocks headless chrome
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')

        if platform.system() == 'Windows':
            logging.info('Running on Windows')
            return webdriver.Chrome(WebDriver.resource_path('chromedriver.exe'), chrome_options=options)

        logging.info('Running on Mac / *nix')
        return webdriver.Chrome(WebDriver.resource_path('chromedriver'), chrome_options=options)


def wait_element_to_present(driver, delay, element):
    try:
        WebDriverWait(driver, delay).until(
            EC.presence_of_element_located(element))
    except TimeoutException:
        logging.exception('Failed to wait element within ' + str(delay) + 's')


def get_os_path():
    if platform.system() == 'Windows':
        return '\\'

    return '/'


def generate_znl_text(content):
    znl_text = ''
    try:
        random_num = str(random.randint(0, 888888)
                         ) if content['withRandNum'] else ''
        znl_text = (content['tags1'] +
                    random.choice(content['emoji']) +
                    content['tags2'] + '\n' +
                    random.choice(content['znlText']) +
                    random.choice(content['emoji']) +
                    random.choice(content['emoji']) + '\n' +
                    random.choice(content['exText']) + ' 伯远' +
                    random.choice(content['emoji']) +
                    random.choice(content['emoji']) + ' ' +
                    random_num + '\n@INTO1-伯远 \n')
    except Exception:
        logging.exception('Failed to generate znl text')
    finally:
        return znl_text


def post(post_button, driver):
    try:
        post_button.click()  # send post
        logging.info('Post uploaded')
        time.sleep(5)  # mandatory sleep, wait for upload
    except ElementClickInterceptedException:
        logging.exception(
            'strange overlay element found, refreshing page to resume')
        driver.refresh()


def main():
    start_time = time.time()
    driver = WebDriver.chrome()

    try:
        login_start_time = time.time()
        driver.get('https://weibo.com/login.php')  # login
        wait_element_to_present(driver, 300, (By.ID, 'v6_pl_rightmod_myinfo'))
        logging.info('User logged in')
        logging.info('--- %s seconds used on login ---' % (time.time() - login_start_time))

        navigate_start_time = time.time()
        driver.get(
            'https://weibo.com/p/100808c58cd9e27740c6aae77baa96d6538cab/super_index')
        wait_element_to_present(driver, 30, (By.ID, 'Pl_Third_Inline__260'))
        logging.info('Navigated to super page')
        logging.info('--- %s seconds used on navigating to super page ---' % (time.time() - navigate_start_time))
        time.sleep(3)  # avoid flakiness on page load

        inputs = driver.find_elements_by_class_name('W_input')
        post_input = inputs[1]

        buttons = driver.find_elements_by_class_name('W_btn_a')
        post_button = buttons[0]

        with open('input.json', encoding='utf8') as info:
            data_info = json.load(info)
            logging.info('Input config ingested')

            num_of_posts = data_info['numOfPosts']
            image_folder_path = data_info['imageFolderPath']
            image_upload_enabled = image_folder_path.strip() != ''
            if not image_upload_enabled:
                logging.info('Fast mode enabled')
            else:
                logging.info('Normal mode enabled')

        with open('content.json', encoding='utf8') as content:
            data_content = json.load(content)
            logging.info('Content ingested, start posting ' + str(num_of_posts) + ' blog')

            # send n posts loop
            for i in range(num_of_posts):
                logging.info('Posting No.' + str(i + 1) + ' blog')

                # set post text
                wb_text = generate_znl_text(data_content)
                actions = ActionChains(driver)
                actions.move_to_element(post_input).double_click()
                post_input.send_keys(wb_text)
                post_input.click()

                logging.info('Finished setting text')
                time.sleep(2)  # wait element to be inserted to DOM

                # upload image to the post
                if image_upload_enabled:
                    randint = random.randint(1, 10)
                    image_path = image_folder_path + get_os_path() + str(randint) + '.jpg'
                    logging.info('Sending image' + str(randint) + '.jpg')

                    driver.find_element_by_xpath(
                        '//a[@action-type="multiimage"]').click()
                    logging.info('Image upload button toggled')
                    time.sleep(1)

                    driver.find_element_by_xpath(
                        '//input[contains(@id, "swf_upbtn")]').send_keys(image_path)
                    logging.info('Image uploaded')
                    time.sleep(3)  # mandatory sleep, wait for file preview

                post(post_button, driver)  # first attempt

                try:
                    # handle popup
                    pop_up = driver.find_element_by_xpath(
                        '//div[contains(@id, "layer_")]')
                    if pop_up:
                        logging.info('Overlay found, will try to dismiss it')
                        button = driver.find_element_by_xpath(
                            '//a[@action-type="ok"]')
                        if button:
                            logging.info(
                                'Dismiss button found, will try click it')
                            button.click()  # wait for animation fade out
                            logging.info(
                                'Dismiss button clicked, waiting animation')
                            time.sleep(2)

                            post(post_button, driver)  # second attempt after pop up gone
                except NoSuchElementException:
                    logging.debug('Overlay element cannot be found')
                    pass
    except Exception:
        try:
            logging.exception('Unknown exception')
        except Exception:
            pass

        time.sleep(10000)  # TODO:  change it to driver.close() later
    finally:
        logging.info('--- %s seconds used ---' % (time.time() - start_time))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
