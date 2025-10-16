def dict_depth(my_dict: dict) -> int:
    """
    Depth dict counter help us to know nested dict structure

    :param dict my_dict
    :return int
    """
    if isinstance(my_dict, dict):
        return 1 + (max(map(dict_depth, my_dict.values())) if my_dict else 0)
    return 0


def evenly_dict_contains_list(my_dict: dict) -> bool:
    same_length = set()
    for _, lst in my_dict.items():
        if not isinstance(lst, list):
            return False
        same_length.add(len(lst))
    return len(same_length) == 1

## additional