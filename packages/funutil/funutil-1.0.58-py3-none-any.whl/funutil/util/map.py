def deep_get(data: dict, *args):
    if not data:
        return None
    try:
        for arg in args:
            if isinstance(arg, int) and isinstance(data, list) and arg < len(data):
                data = data[arg]
            if isinstance(arg, str) and isinstance(data, dict) and arg in data:
                data = data[arg]
            else:
                return None
    except Exception as e:
        print(e)
        return None
    return data


def find_get(data: dict, *args):
    if not data:
        return None
    for arg in args:
        if arg in data:
            return data[arg]
    return None
