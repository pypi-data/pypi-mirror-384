import random
from datetime import datetime
from .storage import load, update_tasks

class Task:
    def __init__(self, text, category = "general", status = "Pending"):
        self.task_id = str(random.randint(1000, 9999))
        self.text = text
        self.category = category
        self.status = status
        self.created_at = datetime.now().strftime("Date: %d-%m-%Y Time: %H:%M:%S")



    def __repr__(self):
        return f"[{self.status}] {self.text} ({self.category})"


class Design:
    def __init__(self, log_line= "="*48):
        self.log_line = Design.color(36, log_line)

    @staticmethod
    def color(color_code: int, text: str):
        return f"\033[{color_code}m{text}\033[0m"

    @staticmethod
    def clean_word(text):
        txt = text.strip().replace(" ","").lower()
        return txt


    def show_log_message(self, message):
        print(f"{self.log_line}\n {message}\n{self.log_line}")


class ManageTask(Design):
    def __init__(self):
        self.tasks = []
        super().__init__()


    def add_task(self,text, category):
        task = Task(text, category if category else "general")
        self.tasks.append({"Task": task.text,
                           "Category":  task.category,
                           "Created at": task.created_at,
                           "Status": task.status
                                   if task.status == "Pending"
                                   else task.status
                           })
        update_tasks(self.tasks)


    def show_tasks(self, iterable, message = "All added tasks"):
        tasks = load()
        tasks_dicts = [t for t in tasks]
        self.show_log_message(f"{message}")
        for index, task in enumerate(iterable, start=1):
            for each_dict in tasks_dicts:
                if task == each_dict["Task"]:
                    print(f"""{index}. Task - {self.color(34, task)} - Status: {self.color(31,each_dict['Status'])
                           if each_dict['Status'] == 'Pending'
                            else self.color(32,each_dict['Status'])
                    }
                    \n """)


class Error(ManageTask):
    def error_message(self, message = "No tasks yet!..."):
        print(self.color(31, message))

    def warning_message(self,message_prompt, value = "App"):
        print(self.color(31, f"If you proceed you won't be able to Undo"
                                            f" {message_prompt}!\n{self.color(34,'-'*55)} "))

        print(self.color(31, f"Are you sure you want to "
                                             f"{message_prompt} {value} permanently?\n"
                                             "1. yes\n"
                                             "2. no"))
        print(self.log_line)

    def warning_response(self, choice, update, prompt = "delete"):
        if self.clean_word(choice) in ["1", "yes"] and prompt == "delete":
            update_tasks(update)
            self.show_log_message(self.color(32,"Updated Successfully!"))
        elif self.clean_word(choice) in ["1", "yes"] and prompt == "clear":
            self.tasks.clear()
            update_tasks(self.tasks)
            self.show_log_message(self.color(32, "Tasks cleared successfully!.."))
        elif self.clean_word(choice) in ["2", "no"]:
            self.show_log_message(self.color(32,"Aborted  Successfully!"))

        else:
            print(self.color(31, f"Error... Expected '1,2....yes,no' got '{choice}' instead."))


class TaskManager(Error):
    pass

