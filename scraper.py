import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
from twilio.rest import Client


# Constants
BUTTON_CLASS = "important-information-modal__button bb-button bb-button--rounded bb-button--primary bb-button--md"
STANDING_LOCATION = "3239946%2C3239944%2C3239945"
FRONT_LOCATION = "3234163%2C3234191%2C3234225%2C3234244"
MAX_PRICE_STAND = 1100
MAX_PRICE_FRONT = 750
STAND_COOLDOWN = 3600
FRONT_COOLDOWN = 3600

# Twilio setup
load_dotenv()
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)
from_number = os.getenv("FROM_NUMBER")
to_number = os.getenv("TO_NUMBER")


def init_driver():
    options = webdriver.EdgeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Edge(options=options)
    driver.wait = WebDriverWait(driver, 5)
    return driver


def lookup(driver, location):
    # Get page and click button
    driver.get(
        f"https://www.stubhub.co.uk/taylor-swift-tickets-london-wembley-stadium-15-8-2024/event/105966002/?sort=price%20asc&sid={location}"
    )
    # try:
    #     button = driver.wait.until(EC.element_to_be_clickable((By.NAME, BUTTON_CLASS)))
    #     button.click()
    # except TimeoutException:
    #     print("Button not found")
    # # Scrolling to 5 * i th elements for every 1 second -- to display them all
    # for ticketBoxIndex in range(0, 200, 5):
    #     try:
    #         print("ticketBoxIndex %d" % ticketBoxIndex)
    #         driver.execute_script(
    #             "$('.rowcell')[" + str(ticketBoxIndex) + "].scrollIntoView(true);"
    #         )
    #         time.sleep(1)
    #     except Exception as e:
    #         print(e)
    #         break
    # Get all statistics
    prices = driver.find_elements(By.CLASS_NAME, "AdvisoryPriceDisplay__content")[:5]
    prices = [
        int("".join(e for e in p.text if e.isdigit() or e == ".")) for p in prices
    ]
    num_tickets = driver.find_elements(
        By.CLASS_NAME, "RoyalTicketListPanel__SecondaryInfo"
    )[:5]
    num_tickets = [
        int(ticket.text.split(" ")[-2].split("\n")[-1]) for ticket in num_tickets
    ]
    return prices, num_tickets


def alert_by_price(prices, tickets, is_stand):
    if min(prices) < MAX_PRICE_STAND and is_stand:
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body=f"Front Standing tickets available for £{min(prices)}",
        )
        time.sleep(STAND_COOLDOWN)
    if min(prices) < MAX_PRICE_FRONT and not is_stand:
        message = client.messages.create(
            from_=from_number,
            to=to_number,
            body=f"Front Seated tickets available for £{min(prices)}",
        )
        time.sleep(FRONT_COOLDOWN)


if __name__ == "__main__":
    driver = init_driver()
    while True:
        try:
            standing_prices, standing_tickets = lookup(driver, STANDING_LOCATION)
            alert_by_price(standing_prices, standing_tickets, True)
        except Exception as e:
            print(e)
        time.sleep(30)
        try:
            front_prices, standing_prices = lookup(driver, FRONT_LOCATION)
            alert_by_price(front_prices, standing_prices, False)
        except Exception as e:
            print(e)
        time.sleep(30)
    driver.quit()
