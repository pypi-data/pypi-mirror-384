import os
import sys
from typing import List
from dotenv import load_dotenv, find_dotenv, dotenv_values
from types import SimpleNamespace
from deprecated import deprecated

def fast_loadenv_then_append_path(keys:List[str]=["PROJECT_ROOT"], verbose=False) -> SimpleNamespace:

    env_path = find_dotenv(usecwd=True)
    load_res = load_dotenv(dotenv_path=env_path)

    if keys is not None and len(keys) > 0:
        for key in keys:
            value = os.getenv(key)
            if value and os.path.exists(value) and os.path.isdir(value):
                sys.path.append(value)
                if verbose:
                    print(f"appending {value} to sys.path")

    # env_values = dotenv_values(dotenv_path=env_path)
    # if append:
    #     for _, value in env_values.items():
    #         if os.path.exists(value) and os.path.isdir(value):
    #             sys.path.append(value)
    env_values = dotenv_values(dotenv_path=env_path)
    ns = SimpleNamespace(**env_values)
    return ns

