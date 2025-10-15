def deep_get(data: dict, *args):
    if not data:
        return None
    for arg in args:
        if isinstance(arg, int) or arg in data:
            try:
                data = data[arg]
            except Exception as e:
                print(e)
                return None
        else:
            return None
    return data


def find_get(data: dict, *args):
    if not data:
        return None
    for arg in args:
        if arg in data:
            return data[arg]
    return None
