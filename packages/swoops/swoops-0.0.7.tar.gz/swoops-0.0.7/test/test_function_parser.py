"""
Written by Jason Krist
06/03/2024

Written with assistance from Github Copilot (using GPT-4.1)
"""

import sys
from os import path
from pprint import pprint
from typing import Tuple, Optional

testdir = path.dirname(path.realpath(__file__))
appendpath = path.realpath(path.join(testdir, "../src"))
print(f"appendpath: {appendpath}")
sys.path.insert(0, appendpath)

from swoops import function_parser as fp  # type: ignore # pylint: disable=E0611,E0401,C0413

def test_fun_1(pos1:float, pos2:list[dict[str,float]], kw1:Optional[str]=None, *args, **kwargs)->Tuple[str,float,list]:
    float1 = pos1
    list1 = pos2
    string1 = ""
    if kw1 is not None:
        string1 = kw1
    return string1, float1, list1

def test_fun_2(*args, **kwargs)->Tuple[tuple,dict]:
    return args, kwargs

if __name__ == "__main__":
    print("")
    script_path = path.realpath(__file__)
    functions = fp.parse_functions(file_path = script_path)
    for function_dict in functions.values():
        pprint(function_dict)
        print("")
        sorted_args = sorted(function_dict['args'].values(), key=lambda x: x['position'])
        print(sorted_args)
        print("")
        sorted_returns = sorted(function_dict['returns'].values(), key=lambda x: x['position'])
        print(sorted_returns)
        print("")

    # script_path = r'C:\Users\jkris\OneDrive\2022_onward\2025\python\swoops\src\swoops\gui\helper.py'
    # functions = get_python_functions(script_path)
    # for function_dict in functions:
    #     pprint(function_dict)
    #     print("")