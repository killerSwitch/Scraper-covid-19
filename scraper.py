import json
import logging
import smtplib
import argparse
import datetime

from os import getcwd
from selenium import webdriver
from bs4 import BeautifulSoup
from apscheduler.schedulers.blocking import BlockingScheduler


URL = "https://www.mohfw.gov.in/"
MSG_HEADINGS = ["Indian Cases", "Foreign Cases", "Cured", "Deaths"]

# Setting logger
logging.basicConfig(filename="file.log",
                    format='%(asctime)s %(levelname)s %(funcName)s %(lineno)d %(message)s ', filemode='w+')
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Setting Argparser
parser = argparse.ArgumentParser(
    description='Covid-19 Scraper',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--file', type=str, default="./config.json",
                    help='Path to Config file containing Gmail login Credentials')
args = parser.parse_args()


def get_page_source():
    try:
        option = webdriver.ChromeOptions()
        option.add_argument("—-incognito")
        driver = webdriver.Chrome(executable_path=f'{getcwd()}/chromedriver.exe',
                                  chrome_options=option)
        driver.get(URL)
        log.info("Got the webpage")
        button = driver.find_element_by_class_name('collapsible')
        button.click()
        log.info("Button clicked successfully")
        return driver.page_source

    except Exception as err:
        log.exception(err)
        raise


def extract_state_info_from_tds(tds):
    indian_cases = int(tds[2].text)
    foreign_cases = int(tds[3].text)
    cured_cases = int(tds[4].text)
    death_cases = int(tds[5].text)
    return [indian_cases, foreign_cases, cured_cases, death_cases]


def extract_country_info_from_tds(tds):
    total_cases_indian = int(tds[1].text.split()[0])
    total_cases_foreign = int(tds[2].text.split()[0])
    total_cases_cured = int(tds[3].text.split()[0])
    total_cases_death = int(tds[4].text.split()[0])
    return [total_cases_indian, total_cases_foreign,
            total_cases_cured, total_cases_death]


def extract_table(page_source):
    country_data = {}
    soup = BeautifulSoup(page_source, 'html.parser')

    try:
        tables = soup.findAll("div", {"class": "table-responsive"})
        table = tables[len(tables)-1]
        tbody = table.find("tbody")
        children = tbody.findChildren("tr", recursive=False)
        for index, child in enumerate(children):
            tds = child.findChildren("td", recursive=False)
            if index != len(children)-1:
                country_data[tds[1].text] = extract_state_info_from_tds(tds)
            else:
                country_data['Total'] = extract_country_info_from_tds(tds)

        return country_data

    except IndexError as err:
        log.exception("Index Error")
        raise

    except Exception as err:
        log.exception(err)
        raise


def check_difference(file_name, new_data):
    try:
        with open(file_name) as json_file:
            Messages = []
            TOTAL_KEY = "Total"
            old_data = json.load(json_file)
            log.info("Old Data Loaded")
            for (key, value) in new_data.items():
                if key == TOTAL_KEY:
                    continue
                elif not key in old_data.keys():
                    log.debug(f"NEW STATE\n {key}: {value}")
                    Messages.append(f"NEW STATE\n{key}: {value}")
                else:
                    old_values = old_data[key]
                    temp_str = ""
                    for i in range(len(old_values)):
                        if old_values[i] != value[i]:
                            temp_str += f"{MSG_HEADINGS[i]}: {value[i]-old_values[i]}\n"
                            log.debug(temp_str)
                    if temp_str != '':
                        Messages.append(f"{key}\n{temp_str}{value}")
            if Messages != []:
                log.info("Changes in the values")
                log.debug(Messages)
                Messages.append(f"Total:{new_data[TOTAL_KEY]}")
                with open(file_name, 'w') as json_file:
                    json.dump(new_data, json_file)
                log.info("New data dumped")
            else:
                log.info("No changes in values")
            return Messages

    except FileNotFoundError:
        log.info("No json file found. Dumping Latest Data")
        with open(file_name, 'w') as json_file:
            json.dump(new_data, json_file)

    except json.decoder.JSONDecodeError:
        log.info("Data File Present but is Empty. Dumping latest data")
        with open(file_name, 'w') as json_file:
            json.dump(new_data, json_file)

    except Exception as err:
        log.exception(err)
        raise


def send_email(subject, msg, login_creds):
    try:
        log.info("Sending Email...")
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(login_creds["EMAIL"], login_creds["PASSWORD"])
        message = f'Subject:{subject}\n\n{msg}'
        server.sendmail(login_creds["EMAIL"], login_creds["EMAIL"], message)
        server.quit()
        log.info("Success: Email Sent!")

    except Exception:
        log.exception("Email Failed to send")
        raise


def convert_msgs_to_str(msgs):
    msg_str = ""
    for msg in msgs:
        msg_str = msg_str + msg + "\n###############\n"
    log.debug("Message String is as follows")
    log.debug(msg_str)
    return msg_str


def main():
    page_source = get_page_source()
    data = extract_table(page_source)
    messages = check_difference("data.json", data)
    if messages != []:
        try:
            with open(args.file) as json_file:
                login_creds = json.load(json_file)
                msg_str = convert_msgs_to_str(messages)
                send_email("Covid-19", msg_str, login_creds)

        except FileNotFoundError as err:
            log.exception("Config File not Found")
            raise
        except Exception as err:
            log.exception(err)
            raise


if __name__ == "__main__":
    main()
    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'interval', hours=1,
                      start_date=datetime.datetime.now())
    scheduler.start()
