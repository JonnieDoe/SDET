#!/usr/bin/python -tt
# -*- coding: utf-8 -*-

"""Helper module."""


class Colors(object):
    """Color class for pretty print in TTY."""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[3m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = "\033[3m"


def search_dict_for_value(value_to_search, key_to_search, dkt: dict):
    """Search a dict for a key.
    :param value_to_search: Value to search in dict key
    :param key_to_search: Key to search for [immutable]
    :param dkt: dictionary to search in [dict]
    """

    for key, values in dkt.items():
        if not isinstance(values, dict):
            return False

        if value_to_search == values.get(key_to_search):
            return key
