import os
import string
from datetime import datetime

from jarvis.executors import communicator, weather
from jarvis.modules.logger import logger, multiprocessing_logger
from jarvis.modules.models import models


def monitor() -> None:
    """Weather monitoring system to trigger notifications for high, low weather and severe weather alert."""
    multiprocessing_logger(
        filename=os.path.join("logs", "background_tasks_%d-%m-%Y.log")
    )
    try:
        condition, high, low, temp_f, alert = weather.weather(monitor=True)
    except TypeError:
        logger.error("Failed to get weather alerts")
        return
    if not any(
        (
            high >= models.env.weather_alert_max,
            low <= models.env.weather_alert_min,
            alert,
        )
    ):
        logger.debug(
            dict(
                condition=condition, high=high, low=low, temperature=temp_f, alert=alert
            )
        )
        logger.info("No alerts to report")
        return
    title = "Weather Alert"
    sender = "Jarvis Weather Alert System"
    subject = title + " " + datetime.now().strftime("%c")
    body = (
        f"Highest Temperature: {high}\N{DEGREE SIGN}F\n"
        f"Lowest Temperature: {low}\N{DEGREE SIGN}F\n"
        f"Current Temperature: {temp_f}\N{DEGREE SIGN}F\n"
        f"Current Condition: {string.capwords(condition)}"
    )
    email_args = dict(
        body=body,
        recipient=models.env.recipient,
        subject=subject,
        sender=sender,
        title=title,
        gmail_user=models.env.open_gmail_user,
        gmail_pass=models.env.open_gmail_pass,
    )
    phone_args = dict(
        user=models.env.open_gmail_user,
        password=models.env.open_gmail_pass,
        body=body,
        number=models.env.phone_number,
        subject=subject,
    )
    # high will definitely be greater than or equal to current
    if high >= models.env.weather_alert_max:
        if alert:
            email_args["body"] = (
                f"High weather alert!\n{alert}\n\n" + email_args["body"]
            )
            phone_args["body"] = (
                f"High weather alert!\n{alert}\n\n" + phone_args["body"]
            )
        else:
            email_args["body"] = "High weather alert!\n" + email_args["body"]
            phone_args["body"] = "High weather alert!\n" + phone_args["body"]
        logger.info("high temperature alert")
        email_args["body"] = email_args["body"].replace("\n", "<br>")
        communicator.send_email(**email_args)
        communicator.send_sms(**phone_args)
        return
    # low will definitely be lesser than or equal to current
    if low <= models.env.weather_alert_min:
        if alert:
            email_args["body"] = f"Low weather alert!\n{alert}\n\n" + email_args["body"]
            phone_args["body"] = f"Low weather alert!\n{alert}\n\n" + phone_args["body"]
        else:
            email_args["body"] = "Low weather alert!\n" + email_args["body"]
            phone_args["body"] = "Low weather alert!\n" + phone_args["body"]
        logger.info("low temperature alert")
        email_args["body"] = email_args["body"].replace("\n", "<br>")
        communicator.send_email(**email_args)
        communicator.send_sms(**phone_args)
        return
    if alert:
        email_args["body"] = (
            f"Critical weather alert!\n{alert}\n\n" + email_args["body"]
        )
        phone_args["body"] = "Critical weather alert!\n" + phone_args["body"]
        logger.info("critical weather alert")
        email_args["body"] = email_args["body"].replace("\n", "<br>")
        communicator.send_email(**email_args)
        communicator.send_sms(**phone_args)
        return
