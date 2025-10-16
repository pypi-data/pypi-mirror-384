import argparse
import os
from swai.const import SWAI
from swai.user import User
from swai.tasks import TaskManager
from swai.utils.print_once import print_once_per_terminal
from swai.utils.test_dependence import test_dependence
from swai.version import __version__
from swai.data_precess import process_data

class Controller:
    def __init__(self, parser: argparse.ArgumentParser):
        self.args = parser.parse_args()
        self.parser = parser
        print_once_per_terminal(message=SWAI)


    def run(self):
        if self.args.command is None or self.args.command == 'help':
            self.parser.print_help()
        elif self.args.command == "deps":
            test_dependence()
        elif self.args.command == "version":
            print(f"SWAI Version: {__version__}")
        elif self.args.command == "process":
            process_data(self.args)
        elif self.args.command == "login":
            User.login(self.args.api_key)
        else:
            user = User()
            task_manager = TaskManager(user.api_key, self.args)
            if self.args.command == "submit":
                task_manager.submit_task(self.args.task_type, self.args.task_input, self.args.subscribe_email, self.args.description)
            elif self.args.command == "list":
                task_manager.list_tasks(
                    self.args.status, self.args.task_id, self.args.task_type, self.args.limit)
            elif self.args.command == "cancel":
                task_manager.cancel_task(self.args.task_id)
            elif self.args.command == "download":
                task_manager.download_task(self.args.task_id, self.args.output)