import random
from datetime import datetime

from dateutil.relativedelta import relativedelta

from jarvis.modules.audio import speaker
from jarvis.modules.models import models
from jarvis.modules.utils import util


def form(*args) -> None:
    """Response for form."""
    speaker.speak(text="I am a program, I'm without form.")


def greeting(*args) -> None:
    """Response for greeting."""
    speaker.speak(
        text=random.choice(
            [
                "I am spectacular. I hope you are doing fine too.",
                "I am doing well. Thank you.",
                "I am great. Thank you.",
            ]
        )
    )


def capabilities(*args) -> None:
    """Response for capabilities."""
    speaker.speak(
        text="There is a lot I can do. For example: I can get you the weather at any location, news around "
        "you, meanings of words, launch applications, create a to-do list, check your emails, get your "
        "system configuration, tell your investment details, locate your phone, find distance between "
        "places, set an alarm, play music on smart devices around you, control your TV, tell a joke, "
        "send a message, set reminders, scan and clone your GitHub repositories, and much more. "
        "Time to ask,."
    )


def languages(*args) -> None:
    """Response for languages."""
    speaker.speak(
        text="Tricky question!. I'm configured in python, and I can speak English."
    )


def whats_up(*args) -> None:
    """Response for what's up."""
    speaker.speak(
        text="My listeners are up. There is nothing I cannot process. So ask me anything.."
    )


def what(*args) -> None:
    """Response for what."""
    speaker.speak(
        text="The name is Jarvis. I'm just a pre-programmed virtual assistant."
    )


def hi(*args) -> None:
    """Response for hi and hello."""
    speaker.speak(
        text="Hello there! My name is Jarvis"
        + random.choice(
            (
                f", good {util.part_of_day()}! How can I be of service today?",
                ", and I'm ready to assist you. How can I help you today?",
            )
        )
    )


def who(*args) -> None:
    """Response for whom."""
    speaker.speak(text="I am Jarvis. A virtual assistant designed by Mr.Raauv.")


def age(*args) -> None:
    """Response for age."""
    relative_date = relativedelta(
        dt1=datetime.strptime(
            datetime.strftime(datetime.now(), "%Y-%m-%d"), "%Y-%m-%d"
        ),
        dt2=datetime.strptime("2020-09-06", "%Y-%m-%d"),
    )
    statement = f"{relative_date.years} years, {relative_date.months} months and {relative_date.days} days"
    if not relative_date.years:
        statement = statement.replace(f"{relative_date.years} years, ", "")
    elif relative_date.years == 1:
        statement = statement.replace("years", "year")
    if not relative_date.months:
        statement = statement.replace(f"{relative_date.months} months", "")
    elif relative_date.months == 1:
        statement = statement.replace("months", "month")
    if not relative_date.days:
        statement = statement.replace(f"{relative_date.days} days", "")
    elif relative_date.days == 1:
        statement = statement.replace("days", "day")
    speaker.speak(text=f"I'm {statement} old.")


def about_me(*args) -> None:
    """Response for about me."""
    speaker.speak(
        text="I am Jarvis. I am a virtual assistant designed by Mr. Raauv. "
        "Given enough access I can be your home assistant. "
        "I can seamlessly take care of your daily tasks, and also help with most of your work!"
    )


def not_allowed_offline() -> None:
    """Response for tasks not supported via offline communicator."""
    speaker.speak(text="That's not supported via offline communicator.")


def un_processable() -> None:
    """Speaker response for un-processable requests."""
    speaker.speak(
        text=f"I'm sorry {models.env.title}! I wasn't able to process your request."
    )
