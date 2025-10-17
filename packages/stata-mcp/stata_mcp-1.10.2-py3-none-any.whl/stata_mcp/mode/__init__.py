import asyncio
import sys
from pathlib import Path

from .langchain_agent import StataAgent


def run_agent_mode():
    print("Welcome to use Stata-MCP Agent mode!")
    work_dir = input("Please set your work path, all of file will display here. "
                     "\ndefault work path-> (~/Downloads/StataAgent), with typing `d`\n>>> ")
    if work_dir.lower() == "d" or work_dir == "":
        work_dir = None
    else:
        work_dir = Path(work_dir)  # TODO: in the future add a path check.

    model = input("Please set your model, default model is gpt-5 provided by OpenAI , with typing `d` \n>>> ")
    if model.lower() == "d" or model == "":
        model = "gpt-5"
    agent = StataAgent(model=model, work_dir=work_dir)

    print("========== Notes ==========")
    print("As present, the mode don't support multi-chat.")
    print("All of the task is individual now.")

    print("========== Start ==========")
    first_time = True
    while True:
        if first_time:
            data_source = input("Please set your data source, enter the data file abs path.\n>>> ")
        else:
            is_old_data = input("Is this data file the same as the last one? (y/n) \n>>> ")
            if is_old_data.lower() == "y":
                pass
            else:
                data_source = input("Please set your data source, enter the data file abs path.\n>>> ")
        first_time = False
        task = input("Please type your task, enter the task description.\n>>> ")
        asyncio.run(agent.run(data_source, task))

        is_exit = input("Is this the end of your task? (y/n) \n>>> ")
        if is_exit.lower() == "y":
            break
    print("Thank you for your use.")
    print("========== End ==========")
    sys.exit(0)


__all__ = [
    "run_agent_mode",
]
