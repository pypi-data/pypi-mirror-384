# coding: utf-8

from typing import Iterable, Tuple


class UrlSettings:
    FILE_PATH_KEY = "file_path"
    DATA_PATH_KEY = "path"
    FILE_PREFIX = "file_prefix"


def split_query(query: str) -> dict:
    result = dict()
    for s in query.split("&"):
        if not s:
            continue
        name, _, value = s.partition("=")
        prev_value = result.get(name)
        if prev_value:
            value = join_string(prev_value, value, "/")
        result[name] = value
    return result


def join_query(query_items: Iterable[Tuple[str, str]]) -> str:
    return "&".join(f"{k}={v}" for k, v in query_items)


def join_string(a: str, b: str, sep: str):
    aslash = a.endswith(sep)
    bslash = b.startswith(sep)
    if aslash and bslash:
        return a[:-1] + b
    elif aslash or bslash:
        return a + b
    else:
        return a + sep + b


def join_path(path_items: tuple) -> str:
    if not isinstance(path_items, tuple):
        raise TypeError
    return ":".join(path_items)


def split_path(path: str):
    return path.split(":")
