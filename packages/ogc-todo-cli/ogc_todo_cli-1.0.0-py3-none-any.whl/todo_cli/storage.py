import json
import os.path

FILE_NAME = "todo_log.json"


def load():
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, "r") as f:
        file = json.load(f)
        return file

def update_tasks(tasks):
    with open(FILE_NAME, "w") as f:
        json.dump(tasks, f, indent=4, ensure_ascii=False)

