import json

from jarvis.executors import word_match
from jarvis.modules.audio import listener, speaker
from jarvis.modules.conditions import keywords
from jarvis.modules.database import database
from jarvis.modules.models import models
from jarvis.modules.utils import shared

tdb = database.Database(database=models.fileio.task_db)
tdb.create_table(table_name="tasks", columns=["category", "item"])


def todo(phrase: str) -> None:
    """Figure out the task to be executed on the DB and call the appropriate function.

    Args:
        phrase: Takes the phrase spoken as an argument.
    """
    if "plan" in phrase.lower():
        get_todo()
        return
    if shared.called_by_offline:
        speaker.speak(text="Todo actions are limited to live conversations.")
        return
    if "add" in phrase.lower():
        add_todo()
        return
    if word_match.word_match(phrase=phrase, match_list=("remove", "delete")):
        if "items" in phrase.lower():
            delete_todo_items()
        else:
            delete_todo()


def get_todo() -> None:
    """Says the item and category stored in the to-do list."""
    with tdb.connection as connection:
        cursor = connection.cursor()
        downloaded = cursor.execute("SELECT category, item FROM tasks").fetchall()
    result = {}
    for category, item in downloaded:
        # condition below makes sure one category can have multiple items without repeating category for each item
        if category not in result:
            # creates dict for category and item if category is not found in result
            result[category] = item
        else:
            # updates category if already found in result
            result[category] = result[category] + ", " + item
    if result:
        if shared.called_by_offline:
            speaker.speak(text=json.dumps(result))
            return
        speaker.speak(text="Your to-do items are")
        # browses dictionary and stores result in response and says it
        for (
            category,
            item,
        ) in result.items():
            response = f"{item}, in {category} category."
            speaker.speak(text=response)
    else:
        speaker.speak(
            text=f"You don't have any tasks in your to-do list {models.env.title}."
        )

    if shared.called["report"]:
        speaker.speak(run=True)


def add_todo() -> None:
    """Adds new items to the to-do list."""
    speaker.speak(text=f"What's your plan {models.env.title}?", run=True)
    if not (item := listener.listen()) or word_match.word_match(
        phrase=item, match_list=keywords.keywords["exit_"]
    ):
        speaker.speak(text=f"Your to-do list has been left intact {models.env.title}.")
        return
    speaker.speak(
        text=f"I heard {item}. Which category you want me to add it to?", run=True
    )
    if not (category := listener.listen()):
        category = "Unknown"
    if word_match.word_match(phrase=category, match_list=keywords.keywords["exit_"]):
        speaker.speak(text=f"Your to-do list has been left intact {models.env.title}.")
        return
    with tdb.connection as connection:
        cursor = connection.cursor()
        downloaded = cursor.execute("SELECT category, item FROM tasks").fetchall()
    if downloaded:
        for c, i in downloaded:  # browses through all categories and items
            # checks if already present and updates items in case of repeated category
            if i == item and c == category:
                speaker.speak(
                    text=f"Looks like you already have the item: {item} added in, {category} category"
                )
                return
    with tdb.connection as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT or REPLACE INTO tasks (category, item) VALUES (?,?)",
            (category, item),
        )
    speaker.speak(
        text=f"I've added the item: {item} to the category: {category}. "
        "Do you want to add anything else to your to-do list?",
        run=True,
    )
    if (category_continue := listener.listen()) and word_match.word_match(
        phrase=category_continue.lower(), match_list=keywords.keywords["ok"]
    ):
        add_todo()
    else:
        speaker.speak(text="Alright")


def delete_todo_items() -> None:
    """Deletes items from an existing to-do list."""
    speaker.speak(text=f"Which one should I remove {models.env.title}?", run=True)
    if not (word := listener.listen()) or word_match.word_match(
        phrase=word, match_list=keywords.keywords["exit_"]
    ):
        speaker.speak(text=f"Your to-do list has been left intact {models.env.title}.")
        return
    with tdb.connection as connection:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM tasks WHERE item=:item OR category=:category",
            {"item": word, "category": word},
        )
        cursor.connection.commit()
    speaker.speak(text=f"Done {models.env.title}!", run=True)


def delete_todo() -> None:
    """Deletes all the data from the table ``tasks`` in the database."""
    with tdb.connection as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tasks")
        cursor.connection.commit()
    speaker.speak(
        text=f"I've deleted all your tasks from the database {models.env.title}."
    )
