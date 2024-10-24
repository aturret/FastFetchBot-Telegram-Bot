from typing import Optional


def list_to_string(lst: Optional[list | str], divider: str = ",") -> str:
    if type(lst) is str:
        return lst
    return divider.join(lst)
