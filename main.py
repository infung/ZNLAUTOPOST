import json
import platform
import time
import random
import traceback

import selenium.webdriver as webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
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

        if platform.system() == 'Windows':
            return webdriver.Chrome('./chromedriver.exe', chrome_options=options)

        return webdriver.Chrome('./chromedriver', chrome_options=options)

def wait_element_to_present(driver, delay, element):
    try:
        element = WebDriverWait(driver, delay).until(EC.presence_of_element_located(element))
        print('page ready')
    except TimeoutException:
        print('login failed!')

def generateZNLText(content):
    try:
        randomNum = str(random.randint(0,888888)) if content['withRandNum'] else ''
        znlText = content['tags1'] + random.choice(content['emoji']) + content['tags2'] + "\n" + random.choice(content['znlText']) + random.choice(content['emoji']) + random.choice(content['emoji']) + "\n" + random.choice(content['exText']) + ' 伯远' + random.choice(content['emoji']) + random.choice(content['emoji']) + ' ' + randomNum + "\n@INTO1-伯远 \n"
        return znlText
    except Exception as e:
        print(e)

def main():
    driver = WebDriver.chrome()

    try:
        driver.get('https://weibo.com/login.php')  # login
        wait_element_to_present(driver, 300, (By.ID, 'v6_pl_rightmod_myinfo'))

        driver.get('https://weibo.com/p/100808c58cd9e27740c6aae77baa96d6538cab/super_index')
        wait_element_to_present(driver, 30, (By.ID, 'Pl_Third_Inline__260'))
        time.sleep(3)  # avoid flakiness on page load

        inputs = driver.find_elements_by_class_name('W_input')
        post_input = inputs[1]

        buttons = driver.find_elements_by_class_name('W_btn_a')
        post_button = buttons[0]

        #default var
        numOfPosts = 20
        imageFolderPath = ''

        with open('./input.json') as info:
            data_info = json.load(info)
            numOfPosts = data_info['numOfPosts']
            imageFolderPath = data_info['imageFolderPath']

        with open('./content.json') as content:
            data_content = json.load(content)
            #send n posts loop
            for i in range(numOfPosts):
                #set post text
                wb_text = generateZNLText(data_content)

                actions = ActionChains(driver)
                actions.move_to_element(post_input).double_click() 
                post_input.send_keys(wb_text)
                post_input.click()

                time.sleep(3)  # wait element to be inserted to DOM

                #upload image to the post
                if imageFolderPath.strip() != '':
                    randint = random.randint(1,10) 
                    imagePath = imageFolderPath + '/' + str(randint) + '.jpg'

                    driver.find_element_by_xpath('//a[@action-type="multiimage"]').click()
                    time.sleep(1)

                    driver.find_element_by_xpath("//input[contains(@id, 'swf_upbtn')]").send_keys(imagePath)
                    time.sleep(5)  # mandatory sleep, wait for file preview
                #send post
                post_button.click()
                time.sleep(5)  # mandatory sleep, wait for upload
    except Exception as e:
        print(e)
        traceback.print_exc()
        driver.close()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
