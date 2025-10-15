import os


def to_lower_camel(string: str) -> str:
    if string == "public_url":
        return "publicURL"

    camel_case = "".join(word.capitalize() for word in string.split("_"))
    lower_camel_case = camel_case[0].lower() + camel_case[1:]
    return lower_camel_case


def directory_exists(folder_path: str) -> bool:
    return os.path.exists(folder_path)


def directory_empty(folder_path: str) -> bool:
    return len(os.listdir(folder_path)) == 0


def file_exists(file_path: str) -> bool:
    return os.path.isfile(file_path)
