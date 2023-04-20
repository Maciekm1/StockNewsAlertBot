import requests
import datetime as dt
import smtplib
from twilio.rest import Client
import sys

# Settings
SIGNIFICANCE_VALUE = 0
SEND_SMS = True

STOCK = "AAPL"
COMPANY_NAME = "Tesla Inc"
ALPHA_VANTAGE_API_KEY = "-"

# Twilio settings
TWILIO_SID = "-"
TWILIO_AUTH = "-"

TO_PHONE = "-"
TWILIO_PHONE = "-"

# Email settings
TO_EMAIL = "-"
FROM_EMAIL = "-"
MY_PASSWORD = "-"


def return_stock_prices_diff(stock: str) -> tuple:
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": stock,
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    response = requests.get("https://www.alphavantage.co/query", params=parameters)
    response.raise_for_status()

    # print(response.json()["Time Series (Daily)"])

    today = dt.datetime.today().date()
    yesterday = today - dt.timedelta(days=1)
    day_before_yesterday = today - dt.timedelta(days=2)
    try:
        stock_open_yesterday = response.json()["Time Series (Daily)"][str(yesterday)]["1. open"]
        stock_close_yesterday = response.json()["Time Series (Daily)"][str(yesterday)]["4. close"]

        stock_open_bfr_yesterday = response.json()["Time Series (Daily)"][str(day_before_yesterday)]["1. open"]
        stock_close_bfr_yesterday = response.json()["Time Series (Daily)"][str(day_before_yesterday)]["4. close"]

        percent_diff_yesterday_open = (float(stock_open_yesterday) / float(stock_open_bfr_yesterday) * 100) - 100
        percent_diff_yesterday_close = (float(stock_close_yesterday) / float(stock_close_bfr_yesterday) * 100) - 100

        # returns a tuple of percent difference between stock prices at (open , close, current_price, price before)
        # times
        return percent_diff_yesterday_open, percent_diff_yesterday_close, stock_close_yesterday, stock_close_bfr_yesterday
    except KeyError:
        print(f"{STOCK} stock data has not been updated yet. Please try again later.")
        sys.exit()


def return_news_articles():
    # Find datetime 2 days before
    days_before_2 = dt.datetime.now() - dt.timedelta(days=2)
    date_split_list = str(days_before_2.date()).split("-")
    formatted_date = f"{date_split_list[0]}{date_split_list[1]}{date_split_list[2]}T0000"

    parameters = {
        "function": "NEWS_SENTIMENT",
        "tickers": STOCK,
        "time_from": formatted_date,
        "sort": "RELEVANCE",
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    response = requests.get("https://www.alphavantage.co/query", params=parameters)
    response.raise_for_status()

    article_1_title = response.json()["feed"][0]["title"]
    article_1_summary = response.json()["feed"][0]["summary"]
    article_1_url = response.json()["feed"][0]["url"]

    article_2_title = response.json()["feed"][1]["title"]
    article_2_summary = response.json()["feed"][1]["summary"]
    article_2_url = response.json()["feed"][1]["url"]

    article_3_title = response.json()["feed"][2]["title"]
    article_3_summary = response.json()["feed"][2]["summary"]
    article_3_url = response.json()["feed"][2]["url"]

    return f"A1: {article_1_title}\n Summary: {article_1_summary}\n  url:{article_1_url}\n\n" \
           f"A2: {article_2_title}\n Summary: {article_2_summary}\n  url:{article_2_url}\n\n" \
           f"A3: {article_3_title}\n Summary: {article_3_summary}\n  url:{article_3_url}"


def send_message(to_phone, from_phone):
    client = Client(TWILIO_SID, TWILIO_AUTH)

    message = client.messages.create(
        from_=from_phone,
        to=to_phone,
        body=stock_info + news_articles
    )

    print(message.status)


def send_email():
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(user=FROM_EMAIL, password=MY_PASSWORD)
        connection.sendmail(from_addr=FROM_EMAIL,
                            to_addrs=TO_EMAIL,
                            msg=f"Subject:{stock_info}\n\n{news_articles}")
        print("email sent successfully!")


# in the format (open percent diff, close percent diff, price at close yesterday, price at close before yesterday)
stock_data = return_stock_prices_diff(STOCK)

if abs(stock_data[1]) > SIGNIFICANCE_VALUE:

    stock_fluctuation_text = ""
    if stock_data[1] > 0:
        if SEND_SMS:
            stock_fluctuation_text = '🔺'
        else:
            stock_fluctuation_text = " | INCREASED BY"

    else:
        if SEND_SMS:
            stock_fluctuation_text = '🔻'
        else:
            stock_fluctuation_text = " | DECREASED BY"

    # 🔺 🔻 replace with INCREASE / DECREASE when sending EMAIL
    # f"{STOCK} {'🔺' if stock_data[1] > 0 else '🔻'}"

    stock_info = (f"{STOCK} {stock_fluctuation_text}"
                  f" {round(abs(stock_data[1]), 4)}%  |  "
                  f"{stock_data[3]}$ -> {stock_data[2]}$  |  "
                  f" Price at close yesterday: {stock_data[2]}$  |  price at close before yesterday: {stock_data[3]}"
                  "$\n\n")
    # print(stock_info)

    news_articles = return_news_articles()
    # print(news_articles)

    if SEND_SMS:
        send_message(to_phone=TO_PHONE, from_phone=TWILIO_PHONE)
    else:
        send_email()
