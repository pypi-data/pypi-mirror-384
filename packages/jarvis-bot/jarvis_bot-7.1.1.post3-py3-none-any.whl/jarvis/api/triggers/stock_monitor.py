"""Runs on a cron schedule every 15 minutes during weekdays."""

import collections
import logging
import math
import os
import time
from datetime import datetime
from typing import Any, Dict, Tuple

import gmailconnector
import jinja2
import matplotlib.dates
import matplotlib.pyplot as plt
from webull import webull


def generate_graph(logger: logging.Logger, ticker: str, bars: int = 300) -> str | None:
    """Generate historical graph for stock price.

    Args:
        logger: Takes the class ``logging.Logger`` as an argument.
        ticker: Stock ticker.
        bars: Number of bars to be fetched

    References:
        https://stackoverflow.com/a/49729752
    """
    logger.info("Generating price chart for '%s'", ticker)
    # ~ 1 month
    dataframe = webull().get_bars(
        stock=ticker, interval="m60", count=bars, extendTrading=1
    )
    refined = dataframe[["close"]]
    if len(refined) == 0:
        refined = dataframe[["open"]]
    x = util.matrix_to_flat_list(input_=refined.values.tolist())
    y = [i.to_pydatetime() for i in refined.iloc[:, 0].keys()]

    fig, ax = plt.subplots()
    ax.plot(y, x)

    plt.title(ticker)
    plt.xlabel("Timeseries")
    plt.ylabel(f"{bars} plots with 1 hour interval")

    if bars > 600:
        ax.xaxis.set_major_locator(matplotlib.dates.YearLocator())
        ax.xaxis.set_minor_locator(matplotlib.dates.MonthLocator((1, 4, 7, 10)))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("\n%Y"))
        ax.xaxis.set_minor_formatter(matplotlib.dates.DateFormatter("%b"))
    else:
        ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
        ax.xaxis.set_minor_locator(matplotlib.dates.DayLocator(tuple(range(2, 30, 3))))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("\n%B"))
        ax.xaxis.set_minor_formatter(matplotlib.dates.DateFormatter("%d"))

    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
    plt.grid()
    graph_file = ticker + ".png"
    fig.savefig(graph_file, format="png")
    if os.path.isfile(graph_file):
        return graph_file


class StockMonitor:
    """Initiates ``StockMonitor`` to check user entries in database and trigger notification if condition matches.

    >>> StockMonitor

    Args:
        logger: Takes the class ``logging.Logger`` as an argument.
    """

    def __init__(self, logger: logging.Logger):
        """Gathers user data in stock database, and groups user data by ``ticker`` and ``email``."""
        self.logger = logger
        self.email_grouped = collections.defaultdict(list)
        self.ticker_grouped = collections.defaultdict(list)
        self.data = stockmonitor_squire.get_stock_userdata()
        self.repeat_alerts = list(stockmonitor_squire.get_daily_alerts())
        if self.repeat_alerts == [{}]:
            self.repeat_alerts = []

    def at_exit(self):
        """Removes bin file created by webull client and updates the repeat alerts yaml mapping."""
        stockmonitor_squire.put_daily_alerts(params=self.repeat_alerts)
        os.remove("did.bin") if os.path.isfile("did.bin") else None

    def group_data(self) -> None:
        """Groups columns in the database by ticker to check the current prices and by email to send a notification.

        See Also:
            - For ticker grouping, first value in the list is the ticker, so key will be ticker and the rest are values.
            - For email grouping, first value among the rest is the email, so key is email and the rest are values.
        """
        self.logger.info("Grouping data extracted from database.")
        for k, *v in self.data:
            self.ticker_grouped[k].append(tuple(v))
            self.email_grouped[v[0]].append((k,) + tuple(v[1:]))

    def get_prices(self) -> Dict[str, Dict[str, float | str]]:
        """Get the price of each stock ticker along with the exchange code.

        Returns:
            dict:
            Returns a dictionary of prices for each ticker and their exchange code and key-value pairs.
        """
        prices = {}
        for ticker in self.ticker_grouped.keys():
            prices[ticker] = {}
            try:
                price_check = webull().get_quote(ticker)
                if current_price := round(
                    float(price_check.get("close") or price_check.get("open")), 2
                ):
                    prices[ticker]["price"] = float(current_price)
                else:
                    raise ValueError(price_check)
                if category := price_check.get("disExchangeCode"):
                    prices[ticker]["exchange_code"] = category
                else:
                    raise ValueError(price_check)
            except ValueError as error:
                self.logger.error(error)
                continue
        return prices

    @staticmethod
    def closest_maximum(
        stock_price: int | float, maximum: int | float, correction: int
    ) -> bool:
        """Determines if a stock price is close to the maximum value.

        Examples:
            - Current stock price: 96
            - Maximum price after which notification has to trigger: 100
            - Correction: 15%

            - Corrected: 100 (max) - 15 (15%) = 85 (this becomes the new maximum price)
            - Notifies since stock price is more than corrected amount, even though it is less than actual stock price.

        Args:
            stock_price: Current stock price.
            maximum: Maximum price set by user.
            correction: Correction percentage.

        Returns:
            bool:
            Boolean flag to indicate whether the current stock price is less than set maximum by correction percentage.
        """
        # Because math.floor will round it off to the previous whole number
        if correction < 1:
            return False
        max_corrected_amt = math.floor(maximum - (stock_price * correction / 100))
        return stock_price >= max_corrected_amt

    @staticmethod
    def closest_minimum(
        stock_price: int | float, minimum: int | float, correction: int
    ) -> bool:
        """Determines if a stock price is close to the minimum value.

        Examples:
            - Current stock price: 225
            - Minimum price below which notification has to trigger: 220
            - Correction: 10%

            - Corrected: 220 (min) + 22 (10%) = 242 (this becomes the new minimum price)
            - Notifies since stock price is less than corrected amount, even though it is more than actual stock price.

        Args:
            stock_price: Current stock price.
            minimum: Minimum price set by user.
            correction: Correction percentage.

        Returns:
            bool:
            Boolean flag to indicate whether the current stock price is more than set maximum by correction percentage.
        """
        # Because math.ceil will round it off to the next whole number
        if correction < 1:
            return False
        min_corrected_amt = math.ceil(minimum + (stock_price * correction / 100))
        return stock_price <= min_corrected_amt

    def skip_signal(
        self, condition_list: Tuple[Any, Any, Any, Any, Any, Any], hours: int = 12
    ) -> bool:
        """Generate a skip signal for a particular stock monitoring alert.

        Args:
            condition_list: Alert entry for which the validation should be done.
            hours: Number of hours of overlap to look for.

        Returns:
            bool:
            Returns a boolean flag indicating a repeat signal was generated.
        """
        for repeater in self.repeat_alerts:
            for alert_time, alert_entry in repeater.items():
                if alert_entry == condition_list:
                    # no notification should be triggered
                    if time.time() <= alert_time + hours * 60 * 60:
                        return True
                    else:
                        try:
                            self.repeat_alerts.remove({alert_time: alert_entry})
                        except ValueError as err:
                            self.logger.error(err)
                        return False  # notification should be triggered if condition matches

    def send_notification(self) -> None:
        """Sends notification to the user when the stock price matches the requested condition."""
        if self.data:
            self.group_data()
        else:
            self.logger.info("Database is empty!")
            return
        subject = f"Stock Price Alert - {datetime.now().strftime('%c')}"
        prices = self.get_prices()
        mail_obj = gmailconnector.SendEmail(
            gmail_user=models.env.open_gmail_user, gmail_pass=models.env.open_gmail_pass
        )

        for email_addr, corresponding_alerts in self.email_grouped.items():
            # unique datastore for each user
            datastore = {
                "text_gathered": [],
                "removals": [],
                "attachments": [],
            }
            for trigger in corresponding_alerts:
                ticker = trigger[0]
                maximum = trigger[1]
                minimum = trigger[2]
                correction = trigger[3]
                daily_alerts = trigger[4]
                if not prices[ticker]:
                    continue
                if daily_alerts == "on" and self.skip_signal(
                    condition_list=(
                        ticker,
                        email_addr,
                        maximum,
                        minimum,
                        correction,
                        daily_alerts,
                    ),
                ):
                    self.logger.info("Skipping validations due to daily alerts.")
                    continue
                ticker_hyperlinked = (
                    '<a href="https://www.webull.com/quote/'
                    f'{prices[ticker]["exchange_code"].lower()}-{ticker.lower()}">{ticker}</a>'
                )
                if not maximum and not minimum:
                    raise ValueError("Un-processable without both min and max")
                maximum = util.format_nos(maximum)
                minimum = util.format_nos(minimum)
                email_text = ""
                if maximum and prices[ticker]["price"] >= maximum:
                    email_text += f"{ticker_hyperlinked} has increased more than the set value: ${maximum:,}"
                elif maximum and self.closest_maximum(
                    prices[ticker]["price"], maximum, correction
                ):
                    email_text += (
                        f"{ticker_hyperlinked} is close (within {correction}% range) to the set "
                        f"maximum value: ${maximum:,}"
                    )
                elif minimum and prices[ticker]["price"] <= minimum:
                    email_text += f"{ticker_hyperlinked} has decreased less than the set value: ${minimum:,}"
                elif minimum and self.closest_minimum(
                    prices[ticker]["price"], minimum, correction
                ):
                    email_text += (
                        f"{ticker_hyperlinked} is close (within {correction}% range) to the set "
                        f"minimum value: ${minimum:,}"
                    )
                if email_text:
                    email_text += f"<br>Current price of {ticker_hyperlinked} is ${prices[ticker]['price']:,}"
                    datastore["text_gathered"].append(email_text)
                    datastore["removals"].append(
                        (
                            ticker,
                            email_addr,
                            float(maximum),
                            float(minimum),
                            correction,
                            daily_alerts,
                        )
                    )
                    datastore["attachments"].append(
                        generate_graph(ticker=ticker, logger=self.logger)
                    )
            if not datastore["text_gathered"]:
                self.logger.info("Nothing to report")
                return
            template = jinja2.Template(templates.email.stock_alert).render(
                CONVERTED="<br><br>".join(datastore["text_gathered"])
            )
            response = mail_obj.send_email(
                subject=subject,
                recipient=email_addr,
                html_body=template,
                sender="Jarvis",
                attachment=datastore["attachments"],
            )
            if response.ok:
                self.logger.info("Email has been sent to '%s'", email_addr)
                for entry in datastore["removals"]:
                    if entry[5] == "off":
                        self.logger.info("Removing '%s' from database.", entry)
                        stockmonitor_squire.delete_stock_userdata(data=entry)
                    else:
                        self.logger.info(
                            "Retaining '%s' as user subscribed for daily alerts.", entry
                        )
                        self.repeat_alerts.append({int(time.time()): entry})
            else:
                self.logger.error(response.json())
            [
                os.remove(stock_graph)
                for stock_graph in datastore["attachments"]
                if os.path.isfile(stock_graph)
            ]


if __name__ == "__main__":
    # imports within __main__ to avoid potential/future path error and circular import
    # override 'current_process().name' to avoid being set as 'MainProcess'
    # importing at top level requires setting current_process().name at top level which will in turn override any import
    from multiprocessing import current_process

    current_process().name = "StockMonitor"
    from jarvis.api.squire import stockmonitor_squire
    from jarvis.executors import crontab
    from jarvis.modules.logger import logger as main_logger
    from jarvis.modules.logger import multiprocessing_logger
    from jarvis.modules.models import models
    from jarvis.modules.templates import templates
    from jarvis.modules.utils import util

    multiprocessing_logger(filename=crontab.LOG_FILE)
    # Remove process name filter
    for log_filter in main_logger.filters:
        main_logger.removeFilter(filter=log_filter)
    stock_monitor = StockMonitor(logger=main_logger)
    stock_monitor.send_notification()
    stock_monitor.at_exit()
