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
                    format='%(asctime)s %(name)s - %(levelname)s: %(message)s',
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
        driver.save_screenshot(str(time.time()) + '.png')
        driver.close()
        sys.exit(1)


def get_os_path():
    if platform.system() == 'Windows':
        return '\\'

    return '/'


def read_file_with_encoding(filename, encoding):
    with open(filename, encoding=encoding) as file:
        try:
            data = json.load(file)
            logging.info(filename + ' ingested')
            return data
        except ValueError:
            logging.exception('Failed to parse ' + filename +
                              ' in ' + encoding + ' encoding scheme')

    return None


def read_file(filename):
    data = read_file_with_encoding(filename, 'utf-8')
    if data is None:
        logging.info('Trying to parse file as UTF-8 BOM')
        data = read_file_with_encoding(filename, 'utf-8-sig')
        if data is None:
            sys.exit(1)

    return data


def generate_znl_text(content):
    znl_text = ''
    try:
        random_num = str(random.randint(0, 888888)
                         ) if content['withRandNum'] else ''
        znl_text = (content['tags1'] + ' ' +
                    random.choice(content['emoji']) + ' ' +
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
            'strange overlay element found, exiting')
        driver.save_screenshot(str(time.time()) + '.png')
        driver.close()
        sys.exit(1)


def set_text(data_content, driver, post_input):
    # set post text
    wb_text = generate_znl_text(data_content)
    actions = ActionChains(driver)
    actions.move_to_element(post_input).double_click()
    post_input.clear()
    post_input.send_keys(wb_text)


def handle_pop_up(driver, post_button):
    try:
        # handle popup
        pop_up = driver.find_element_by_xpath(
            '//div[contains(@id, "layer_")]')
        if pop_up:
            logging.info('Overlay found, will try to dismiss it')

            titles = driver.find_elements_by_class_name('S_txt1')
            popup_title = titles[len(titles) - 1]
            if popup_title.text == '需要验证码' or popup_title.text == '发布内容过于频繁' or popup_title.text == 'Cannot do this operation':
                logging.error('Account locked')
                driver.close()
                sys.exit(1)

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


def main():
    # test config parsing and get config before starting chromedriver
    data_content = read_file('content.json')
    data_info = read_file('input.json')
    num_of_posts = data_info['numOfPosts']
    image_folder_path = data_info['imageFolderPath']
    image_upload_enabled = image_folder_path.strip() != ''
    super_topic = data_info['superTopic']
    if not image_upload_enabled:
        logging.info('Fast mode enabled')
    else:
        logging.info('Normal mode enabled')

    start_time = time.time()
    driver = WebDriver.chrome()

    try:
        login_start_time = time.time()
        driver.get('https://weibo.com/login.php')  # login
        wait_element_to_present(driver, 300, (By.ID, 'v6_pl_rightmod_myinfo'))
        logging.info('--- %s seconds used on login ---' %
                     (time.time() - login_start_time))

        navigate_start_time = time.time()
        driver.get(super_topic)
        wait_element_to_present(driver, 30, (By.ID, 'Pl_Third_Inline__260'))
        logging.info('--- %s seconds used on navigating to super page ---' %
                     (time.time() - navigate_start_time))
        time.sleep(3)  # avoid flakiness on page load

        inputs = driver.find_elements_by_class_name('W_input')
        post_input = inputs[1]

        buttons = driver.find_elements_by_class_name('W_btn_a')
        post_button = buttons[0]

        # send n posts loop
        for i in range(num_of_posts):
            logging.info('Posting No.' + str(i + 1) + ' blog')

            set_text(data_content, driver, post_input)

            try:
                post_input.click()
            except ElementClickInterceptedException:
                # in case any overlay found, dismiss and reset text
                handle_pop_up(driver, post_button)
                set_text(data_content, driver, post_input)
                post_input.click()

            logging.info('Finished setting text')
            time.sleep(1)  # wait element to be inserted to DOM

            # upload image to the post
            if image_upload_enabled:
                files = os.listdir(image_folder_path)
                filtered_img_files = [
                    img for img in files if '.png' in img or '.jpg' in img or '.jpeg' in img]
                image_path = image_folder_path + get_os_path() + random.choice(filtered_img_files)
                logging.info('Sending ' + image_path)

                driver.find_element_by_xpath(
                    '//a[@action-type="multiimage"]').click()
                logging.info('Image upload button toggled')
                time.sleep(1)

                driver.find_element_by_xpath(
                    '//input[contains(@id, "swf_upbtn")]').send_keys(image_path)
                logging.info('Image uploaded')
                time.sleep(3)  # mandatory sleep, wait for file preview

            post(post_button, driver)  # first attempt
            handle_pop_up(driver, post_button)
    except Exception:
        try:
            logging.exception('Unknown exception')
            driver.save_screenshot(str(time.time()) + '.png')
        except Exception:
            pass

        driver.close()
    finally:
        logging.info('--- %s seconds used ---' % (time.time() - start_time))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
