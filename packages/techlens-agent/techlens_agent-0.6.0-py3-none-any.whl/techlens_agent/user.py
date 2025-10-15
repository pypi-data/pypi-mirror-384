from typing import List, Callable, Union


def __get_input__(t: str):
    return input(t)


def repeat_prompt(prompt: str, valid: List[str], default_val: Union[str, None] = None):
    prompt += "\n"
    resp = __get_input__(prompt).lower()
    while resp not in valid:
        if default_val and not resp:
            return default_val
        resp = __get_input__(prompt).lower()
    return resp


def repeat_boolean_prompt(
    prompt: str, logger: Union[Callable, None] = None, default_val: bool = False
):
    valid_strs = ["y", "n"]
    print_opts = "(y/N)"
    d = "n"

    if default_val is True:
        print_opts = "(Y/n)"
        d = "y"

    logger(prompt)
    resp = repeat_prompt(prompt=print_opts, valid=valid_strs, default_val=d)

    return resp.lower() == "y"
