# tstring-util
Utilities for Python 3.14 t-string.

Python 3.14 supports creating objects of type *string.templatelib.Template* by prefixing with a "t". 


## lazy rendering
**def render(template: Template, ctx: dict[str, object] | None = None) -> str:**

Provides ability to write t-string with function calls with deferred evaluation.
Any callable marked !fn will consume as many following interpolations as its positional args,
be invoked, and its ***stdout*** captured inline. Everything else is rendered in order. 

ctx defaults to the locals and globals of the code calling render. 

### Example
```
from numbers import Number

from tstring import render, embed


def double(value:Number)->None:
    print(f"twice {value} is {2*value}")
def test_lazy():
    number = 1
    flavor = 'spicy'
    embedx = t'Call function {double:!fn} {number} {flavor}'
    number = 2

    r = render(embedx)
    assert r ==  "Call function twice 2 is 4 spicy"
```
**def embed(template: Template, ctx: dict[str, object] | None = None) -> str:**

Provides ability to write t-string with function calls with deferred evaluation.
Any callable marked !fn will consume as many following interpolations as its positional args,
be invoked, and its ***return value*** captured and converted to string inline. Everything else is rendered in order. 

ctx defaults to the locals and globals of the code calling embed. 

### Example
```
def return_double(value:Number)->Number:
    return 2 * value

def test_lazy():
    number = 2
    flavor = 'spicy'
    embedx = t'Call return {return_double:!fn} {number} {flavor}'
    r = embed(embedx)
    assert r ==  "Call return 4 spicy"
```

## safe split
**def safe_split(tmpl: Template,sep:str|None=None) -> list[str]:**

Splits a t-string while keeping interpolations intact. This can be used to safely split a string
into input for subprocess

### Example 
```
import subprocess
from tstring import safe_split
injection = '/tmp;rm -fr /'
command = t'ls -l {injection}'
clist = safe_split(command)
subprocess.run(clist)
```

returns *ls: cannot access '/tmp;rm -fr /': No such file or directory*

Note that using a non None separator may produce empty strings in list. See *test_split.py* for examples.
## safe paths 
**path(string.templatelib.Template)->Path**

Converts t-string to a path. If any interpolations have a NUL or path separator in them, ValueError is raised.
A special case of the first character of the first element being a separator is permitted to make paths absolute.


### Example
```
from tstring import path
config = '/etc'
p = path(t'{config}/systemd')
assert p.as_posix() ==  '/etc/systemd'
```

Invalid path:
```
 no_good = 'bob/carol'
 path(t'{no_good}')
 ```

raises ValueError *Invalid character '/' in interpolation 'no_good'*
