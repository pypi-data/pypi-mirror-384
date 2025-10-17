#!/usr/bin/env python3
import logging

from tstring import render, tstring_logger


def double(value):
    print(f"twice {value} is {2*value}")

def return_double(value):
    return 2 * value

def test_lazy():
    number = 1
    flavor = 'spicy'
    embedx = t'Call function {double:!fn} {number} {flavor}'
    number = 2


    r = render(embedx)
    print(r)
    assert r ==  "Call function twice 2 is 4 spicy"

    embedx = t'Call return {return_double:!fn} {number} {flavor}'
    r = render(embedx)
    print(r)
logging.basicConfig()
tstring_logger.setLevel(logging.DEBUG)
test_lazy()
