import json
from .storage import load, update_tasks
from .models import TaskManager, Design

def task_menu():
    manager = TaskManager()
    while True:
        menu = {
            "1": "New task 📝",
            "2": "View all task 👁",
            "3": "Mark task as done ✅",
            "4": "Delete a task 🗑",
            "5": "View task by category 🔎",
            "6": "Search task by keyword 🔑",
            "7": "Clear all task 🚮",
            "8": "Exit app 🚪📲"
        }
        print(json.dumps(menu, indent=4, ensure_ascii=False))
        choice = manager.clean_word(input("Enter a prompt\n"
                                          "-> "))

        if  choice in ["1", "newtask"]:
            text = input("Enter a task: ").strip().capitalize()
            if text:
                category = input("Enter a category: ").strip().capitalize()
                manager.add_task(text, category)
            else:
                manager.show_log_message(manager.color(31,"Error.. Task was not entered!"))

        elif choice in ["2", "viewalltask"]:
            tasks = load()
            if tasks:
                filtered_tasks = [t["Task"] for t in tasks]
                manager.show_tasks(filtered_tasks)
            else:
                manager.error_message()


        elif choice in ["3", "marktaskasdone"]:
            tasks = load()
            if tasks:
                filtered_tasks =[t["Task"] for t in tasks]
                manager.show_tasks(filtered_tasks)

                print(manager.log_line)
                print(manager.color(34, "Enter the number of task completed."))
                try:
                    choice = int(manager.clean_word(input("-> ")))
                    if 1 <= choice <= len(filtered_tasks):
                        selected_task = filtered_tasks[choice-1]
                        for t in tasks:
                                if t["Task"] == selected_task:
                                    if t["Status"] != manager.color(32, "Completed"):
                                        t["Status"]=manager.color(32, "Completed")
                                        update_tasks(tasks)
                                        manager.show_log_message(manager.color(32,"Updated Successfully!"))
                                    else:
                                        manager.show_log_message(manager.color(32, "Already Updated!"))
                    else:
                        manager.show_log_message(manager.color(31,"Error... No number match found in tasks\n"
                                                                  "please select a valid number!."))
                except ValueError as e:
                    print(manager.color(31, f"Error... {e}."))
            else:
                manager.error_message()


        elif choice in ["4", "deleteatask"]:
                stop_code = False
                tasks = load()
                if tasks:
                    try:
                        filter_tasks = [t["Task"] for t in tasks]
                        manager.show_tasks(filter_tasks)
                        print(manager.log_line)
                        print(manager.color(34, "Enter the number of task you want to delete!"))
                        option = int(input("-> "))
                        if option:
                            if 1 <= option <= len(filter_tasks):
                                manager.warning_message("delete", "Tasks")
                            else:
                                print(manager.color(31, f"Error...Invalid response expected "
                                                        f"'1...{len(filter_tasks)}'/'yes,no' got {option} instead!."))
                                stop_code = True
                        else:
                            print(manager.color(31, "Invalid response!.. Expected "))
                        if not stop_code:
                            answer = input("-> ")
                            for index, task in enumerate(filter_tasks, start=1):
                                if option == index:
                                    del filter_tasks[index-1]
                            updated_task = [
                                t for t in tasks
                                if t["Task"] in filter_tasks
                            ]
                            manager.warning_response(answer,updated_task)
                        else:
                            pass

                    except ValueError as e:
                        print(manager.color(31, f"Error... {e}."))
                else:
                    manager.error_message()


        elif choice in ["5", "viewtaskbycategory"]:
            category = manager.clean_word(input("Enter a category\n"
                                                "-> "))
            if category:
                tasks = load()
                tasks_in_category = [t["Task"] for t in tasks if manager.clean_word(t["Category"]) == category]
                manager.show_tasks(tasks_in_category, "All tasks in category.") if tasks_in_category \
                    else manager.error_message("No tasks found in category")
            else:
                print(manager.color(31, "Error...Invalid response"))


        elif choice in ["6", "searchtaskbykeyword"]:
            key_word = manager.clean_word(input("Enter a key Word\n"
                                               "-> "))
            tasks = load()
            filtered_tasks = [t["Task"] for t in tasks  if any(key_word in value.lower() for value in t.values())]
            if filtered_tasks:
                print("Tasks by key Words")
                manager.show_tasks(filtered_tasks)
            else:
                manager.show_log_message(manager.color(31, "No task found in keyWord!.."))


        elif choice in ["7", "clearalltask"]:
            tasks = load()
            if tasks:
                manager.warning_message("Clear", "Task")
                response = input("-> ")
                manager.warning_response(response,  None, "clear")
            else:
                manager.error_message()


        elif choice in ["8", "exitapp"]:
            manager.warning_message("Exit")
            response = manager.clean_word(input("1. yes\n"
                             "2. no\n"
                             "-> "))
            if response in ["1", "yes"]:
                break
            elif response in ["2", "no"]:
                manager.show_log_message(manager.color(32, "Aborted successfully!."))
            else:
                manager.error_message(f"Error.. Invalid response Expected '1,2'/'yes,no' got '{response}' instead!")
        else:
            print(manager.color(31,f"Error.. Invalid response Expected '1,2,3...8' got '{choice}' instead."))

    manager.show_log_message(manager.color(31,"Exited successfully!."))


