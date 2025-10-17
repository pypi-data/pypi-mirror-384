#!/usr/bin/env python3
from numbers import Number

from tstring import render

def double(value:Number)->None:
    print(f"twice {value} is {2*value}")

def return_double(value:Number)->Number:
    return 2 * value

def test_lazy():
    number = 1
    flavor = 'spicy'
    embedx = t'Call function {double:!fn} {number} {flavor}'
    number = 2


    r = render(embedx)
    assert r ==  "Call function twice 2 is 4 spicy"

    embedx = t'Call return {return_double:!fn} {number} {flavor}'
    r = render(embedx)
    assert r ==  "Call return 4 spicy"
