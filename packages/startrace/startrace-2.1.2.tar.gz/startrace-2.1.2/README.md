# Star Trace

A lightweight, ultra-configurable string library.

Created by William Dean Coker

This package is on the [PyPI](https://pypi.org/project/startrace/), and can be installed with:

```bash
pip install startrace
```

---

## Important Note:

This library allows <font color=E93820>**arbitrary code execution**</font> if the user allows it or doesn't configure it 
properly. If you run config settings from untrusted sources, be aware they could run harmful commands
on your system. So only run structures from trusted sources or screen configuration before 
running it.

### Frequently Asked Questions

<details>
    <summary><strong>What is arbitrary code execution?</strong></summary>

Arbitrary code execution is when a program runs code that the user has not written. For instance, 
if a user creates a `Token` or `Pattern` with the right args, StarTrace could run a command 
on the user's system that could be harmful.
</details>

<details>
    <summary><strong>Why allow arbitrary code execution?</strong></summary>

There are many cases in which you may want a Token to access runtime variables. This feature alone 
was the reason I re-wrote this library, as in the old version, Tokens were created once from static
values and printed to strings. This meant that if you had a runtime var, say real world sensor, and 
you wanted to print it as a string in a Token/Pattern, there was no way to access it. 

This feature allows you to link Tokens to runtime variables and output them as strings.
</details>

<details>
    <summary><strong>How can I disable/screen it?</strong></summary>

The only Token that uses this feature is the `LinkToken`. To disable it, whenever you create a 
`LinkToken` or `Pattern`, just don't pass in the `allow_eval` boolean flag, or set it to `False`:

```python
from startrace import Pattern, LinkToken

link = "some_runtime_var"
context = {
    "some_runtime_var": 10,
}

# All of these will throw an error because they are trying 
#   to run code but are not allowed to
LinkToken(link, context, False)
LinkToken(link, context)
Pattern([
    LinkToken(link, context, False)
    LinkToken(link, context)
], False)
# Or you can just leave the eval_allowed flag out of the Pattern constructor
```

<details>
    <summary><strong>What if I use dicts (import from YAML/JSON)?</strong></summary>

If you build your `Pattern` from dicts, then you must be even more careful, especially if you 
are building from JSON/YAML/etc. Make sure before running that the config file you're loading
from is trusted. See example:

```python
from startrace import Pattern

some_runtime_var = "some_value"

config = {
    "tokens": [
        {"type": "link", "link": "some_runtime_var"},
    ],
    "global_context": {
        "some_runtime_var": some_runtime_var,
    },
    "allow_eval": True,
}
# When evaluated, this function will run the code in LinkToken
#   and print the value of some_runtime_var
Pattern(config)

safe_config = {
    "tokens": [
        {"type": "link", "link": "some_runtime_var"},
    ],
    "global_context": {},
    "allow_eval": False,
}
# This will throw an error because it is not allowed to run code, 
#   but LinkTokens were created
Pattern(safe_config)

tokens = [
    {"type": "link", "link": "some_runtime_var"},
]
context = {}
allow_eval = False
# This will throw an error because it is not allowed to run code, 
#   but LinkTokens were created
Pattern(tokens, context, allow_eval)
```

Note how there are several ways to create a `Pattern` such that arbitrary code execution is not 
allowed. Also note that if you pass `allow_eval=False` to `Pattern`, then no matter what the `config`
says, `Pattern.allow_eval` will be `False`, because the arguments always supersede the config.

</details>

</details>

---

## Quick Start

```python
from startrace import *

# Simple pattern with runtime variables
sensor = Link(23.5)
test_name = Link("experiment_1")

context = {"sensor": sensor, "test": test_name}

pattern = Pattern([
    LinkToken("test()", context, True),
    ConstToken("_"),
    LinkToken("sensor()", context, True),
    ConstToken(".csv")
], context, True)

print(pattern)  # "experiment_1_23.5.csv"

# Update runtime values
sensor.set(28.3)
print(pattern)  # "experiment_1_28.3.csv"
```

---

## Star Trace User Guide

Star Trace works on a Token-Pattern-based system, designed to make combinations of strings, 
values, and even runtime variables.

### Tokens

A Token is an object that holds information that, when evaluated, will return a string. Each Token
subclass has these methods:
- `evaluate()`: returns a string representation of the Token
- `next()`: increments the internal index of the Token and returns the next value
- `last()`: decrements the internal index of the Token and returns the previous value
- `to_dict()`: returns a dict representation of the Token

#### Constant Token: `ConstToken`

A Constant Token can be made from any value or class that has a string representation. Upon passing
the value into the `ConstToken` constructor, it will be stored in the `ConstToken.value` attribute.

Attributes:
- `value`: the value that the Token will return as a str when evaluated

```python
from startrace import ConstToken

x = 10
s = "Hello World"

tok_x = ConstToken(x)
tok_s = ConstToken(s)

print(tok_x) # "10"
print(tok_x.evaluate()) # "10"
print(tok_x.value) # 10
print(tok_s) # "Hello World"
```

#### List Token: `ListToken`

A List Token holds a list of values, kind of like a list of `ConstToken`s, created by passing in
a list of values (with a `__str__` method) that will be stored in the `ListToken.values` attribute.

When evaluated, it will return a string representation of the current value (index=0). Then when 
incremented (`next()` or `+ int`), the internal index will be incremented and the next value will 
be returned on the next call to `evaluate()`. `Next()` will return `True` while there are indexes
to increment through. Once it runs out, it will return `False` and reset the index to 0. List Tokens
also have a method `last()`, that will decrement the index in the same manner as `next()`. They also
have an attribute `iter`, which holds the iterator for the list (value, start, end, step).

Attributes:
- `values`: the list of values that the Token will index and return as a str when evaluated
- `iter`: the iterator for the list (value, start, end, step)

```python
from startrace import ListToken

values = [1, 2, 3]

tok = ListToken(values)

while True:
    print(tok)
    if not tok.next():
        break
```

will print:

```text
1
2
3
```

#### Range Token: `RangeToken`

A Range Token holds a range of values, similar to a List Token (in that they both have an `iter`
attribute), but instead of holding and returning a list of values, Range Tokens only hold `iter`
and just return the current value.

Attributes:
- `iter`: the iterator for the range (value, start, end, step)

```python
from startrace import RangeToken

tok = RangeToken(1, 12, 4)

while True:
    print(tok)
    if not tok.next():
        break
```

will print:

```text
1
5
9
```

#### Time Token: `TimeToken`

A Time Token is different from the other Tokens so far. It is the first Token that uses runtime 
variables (non-constant values). It is used to create a string representation of the current date
and/or time.

There are several modes that can be used to create a Time Token:
- date: `year-month-day`
- time: `hour:minute:second`
- datetime: `year-month-day_hour:minute:second`
- iso: `year-month-dayThour:minute:second`
- custom: `custom_format` - see below

<details>
    <summary>Custom Time Tokens</summary>

Time Tokens use the `datetime` module to create a string representation of the current date and/or 
time. You can create a custom Time Token format by passing in a valid datetime format string to the
`TimeToken` constructor. See the 
[datetime module docs](https://docs.python.org/3/library/datetime.html#datetime.datetime.strftime)
for more info.

</details>

Attributes:
- `mode`: the mode of the Time Token
- `fmt`: the format of the Time Token

```python
from startrace import TimeToken

tok_d = TimeToken("date")
tok_t = TimeToken("time")
tok_dt = TimeToken("datetime")
tok_iso = TimeToken("iso")
tok_custom = TimeToken("custom", "%Y-%m-%d %H:%M:%S")

print(tok_d) # "2025-10-9"
print(tok_t) # "10:52:39"
print(tok_dt) # "2025-10-9_10:52:39"
print(tok_iso) # "2025-10-9T10:52:39"
print(tok_custom) # "2025-10-9 10:52:39"
```

#### Link Token: `LinkToken`

Link Tokens are the most powerful Token type. They hold a reference to a runtime variable along with
a context table. When evaluated, these tokens will access runtime variables, call functions, and 
execute code to get data to return as a string. However, this power is not free, as it requires 
extra care to use safely, due to the possibility of arbitrary code execution. See the **Important
Note** section above for more info.

To create a Link Token, you must pass in a reference to a runtime variable for the Link Token to 
access, along with its context table. The context table is a dictionary that holds runtime 
variables that can be accessed by the Link Token.

Attributes:
- `_link`: the statements to be executed to get the value of the Link Token
- `_context`: the context table for the Link Token
- `_allow_eval`: whether the Link Token is allowed to run code
Note these are all private attributes because they shouldn't be updated after the Token is created.

```python
from startrace import LinkToken

x = 10
def y(n):
    return n ** 2

context = {
    "x": x,
    "y": y,
}

tok = LinkToken("y(x)", context, True)

print(tok) # 100
```

However, the real power of LinkTokens comes from the Link class. In the above example, if we were to
change the value of `x` to 20 and printed the result of the Link Token, it would still return 100. 
This is because the Link Token is only accessing the value of `x` in the context table, and not the
value of `x` in the global scope, which is where we changed it. To fix this, we need to use Links. 

```python
from startrace import Link, LinkToken

x = Link(10)
def y(n):
    return n ** 2

context = {
    "x": x,
    "y": y,
}

tok = LinkToken("y(x)", context, True)
print(tok) # 100
x.set(20)
print(tok) # 400
```

Oversimplifying a bit, Python has two main types of variables:
- Mutable: can be changed
- Immutable: can't be changed

Essentially, any time you rest some python vars, it completely deletes the old one and creates a new var
with the same name:

```python
x = 10 # This is an immutable int, so if we reset it, the context is reset
y = [10] # This is a mutable list, so the values inside can be changed without resetting context

x = 20 # This will reset x
y[0] = 20 # This doesn't reset y
y = [20] # This will reset y
```

The Link class is simply a mutable wrapper around a runtime variable. Allowing any non-mutable or
immutable variable to be changed without resetting the LinkTable context.

<details>
    <summary>What happens if I change an immutable runtime var that isn't a link?</summary>

Say you make a LinkToken like so:

```python
from startrace import LinkToken

x = 10
def y(n):
    return n ** 2

context = {
    "x": x,
    "y": y,
}

tok = LinkToken("f(x)", context, True)
```

If we change the value of `x`, the LinkToken's context will not be updated, thus to the LinkToken, `x`
is still 10. Similarly, if we change `y` to some other function, the LinkToken will still use the
old `y` function. 

So in short nothing will break or throw errors, but the LinkToken will not be able to access the
new value of `x` or `y`.

</details>

Another aspect of LinkTokens is that they will automatically attempt to run the links you pass in
by default, so it will throw errors early on if you give it missing context or a bad link. However,
you can disable this behavior by passing `check_link=False` to the `LinkToken` constructor (the 4rth
argument).

#### Implicit Token Generation

Note that while it is generally good practice to create Tokens explicitly, you may also simply
pass in the values you will be using to generate a new Token into the base `Token` constructor.

```python
from startrace import Token

Token(10) # ConstToken
Token("Hello World") # ConstToken
Token([1, 2, 3]) # List Token
Token(1, 12, 4) # Range Token
Token("date") # Time Token
Token("y(x)", context, True) # Link Token
```

### Patterns

A Pattern is a combination of Tokens that can be evaluated to return a string. It is created by 
passing in a list of Tokens to the `Pattern` constructor, along with a global context table and 
allow_eval flag (required to create Link Tokens, see **Important Note** section above).

Attributes:
- `tokens`: the list of Tokens that make up the Pattern
- `_global_context`: the global context table for the Pattern
- `_allow_eval`: whether the Pattern is allowed to run code

```python
from startrace import *

x = Link(10)
def y(n):
    return n ** 2
y_l = Link(y)

context = {
    "x": x,
    "y": y_l,
}
allow_eval = True

pat = Pattern([
    ConstToken(10),
    ConstToken("Hello World"),
    ListToken([1, 2, 3]),
    RangeToken(1, 12, 4),
    TimeToken("date"),
    LinkToken("y(x)", context, allow_eval)
], context, allow_eval)

print(pat) # 10Hello World1110-9-25100
```

While this may seem kind of pointless, the real power of Star Trace comes from Patterns because 
of their ability to create complex but still structured strings. Let's say we're writing a program
that reads sensor data and saves it to a file. We can create a file name Pattern that takes in
the current test name, the current date, and the current time, and then save the data to a file
with that name.

```python
from startrace import *

test_name = "test_1"

context = {
    "test_name": test_name,
}

pat = Pattern(
    [
        LinkToken("test_name", context, True),
        ConstToken("_"),
        TimeToken("date"),
        ConstToken("_"),
        TimeToken("time"),
        ConstToken(".csv"),
    ],
    context,
    True
)

print(pat) # test_1_2025-10-9_10:52:39.csv
```

Or say we had a large database of sensor data we want to analyze, but all the data is stored in files
with this name format: `test_1_iteration_1.csv`, where the test number ranges from 1 to 3 and the
iteration number can be from 1 to 10, but we only want `[1, 4, 5]`. We can create a Pattern to sequentially read in all the files
for use.

```python
from startrace import *

pat = Pattern(
    [
        ConstToken("test_"),
        RangeToken(1, 3, 1),
        ConstToken("_iteration_"),
        ListToken([1, 4, 5]),
        ConstToken(".csv"),
    ]
)

while True:
    print(pat)
    if not pat.next():
        break
```

will print:

```text
test_1_iteration_1.csv
test_1_iteration_4.csv
test_1_iteration_5.csv
test_2_iteration_1.csv
test_2_iteration_4.csv
test_2_iteration_5.csv
test_3_iteration_1.csv
test_3_iteration_4.csv
test_3_iteration_5.csv
```

### Other Notes

#### Patterns and Context

When creating Patterns with LinkTokens, each Link Token must have it's context to access runtime vars.
However, there are also several vars that might be commonly used by all LinkTokens. So I added the 
`global_context` argument to the `Pattern` constructor. This argument is a dictionary that holds
runtime variables that can be accessed by all Link Tokens. 

```python
from startrace import *

x = 10
z = 8
def y(n):
    return n ** 2

local_context_1 = {
    "x": x
}
local_context_2 = {
    "z": z
}
global_context = {
    "y": y,
}

pat_1 = Pattern(
    [
        LinkToken("y(x)", local_context_1, True),
        LinkToken("y(z)", local_context_2, True),
    ],
    global_context,
    True
)
```

In this case, both Link Tokens will have access to the `y` function, but only the first Link Token
will have access to the `x` variable, and only the second Link Token will have access to the `z`
variable. Thus, you can separate the context of each Link Token.

#### Dict Config

Both the Pattern and Token constructors accept a dict as an argument. Generally the dict structure 
should copy that of it's intended token type. 

Token Type Mappings:
- `const`: `ConstToken`
- `list`: `ListToken`
- `range`: `RangeToken`
- `time`: `TimeToken`
- `link`: `LinkToken`

This is an example of how to create a Pattern from a dict:

```python
from startrace import *

config = {
    "tokens": [
        {"type": "const", "value": 10},
        {"type": "const", "value": "Hello World"},
        {"type": "list", "values": [1, 2, 3]},
        {"type": "range", "start": 1, "end": 12, "step": 4},
        {"type": "time", "mode": "date"},
        {"type": "link", "link": "y(x)", "context": {"x": 10}},
    ],
    "global_context": {
        "y": lambda n: n ** 2,
    },
    "allow_eval": True,
}

pat = Pattern(config)
```

**Important Note**: If you do not pass in an `allow_eval` flag to the Pattern constructor when building
from a dict, then the flag will be set solely by the config, so make sure your config dict is trusted.

Also note that all Star Trace classes have a `to_dict()` method that can be used to convert a 
Token/Pattern to a dict.

#### Iters

The `ListToken` and `RangeToken` classes have an `iter` attribute that holds the iterator for the 
list/range. This is useful for when you want to iterate through the list/range. 

Attributes:
- `value`: the current value of the list/range
- `start`: the start of the list/range
- `end`: the end of the list/range
- `step`: the step of the list/range

Methods:
- `next()`: increments `value` by `step`, returning `True` while `value < end` and `False` otherwise
- `last()`: decrements `value` by `step`, returning `True` while `value > start` and `False` otherwise

```python
from startrace import Iter

i = Iter(0, 1, 12, 4)

while True:
    print(i.value)
    if not i.next():
        break
```

will print:

```text
0
4
8
12
```

---

## License

This project is under the GNU General Public License, feel free to modify or distribute this 
code however you see fit

<font size=4px color=#6E6E6E>Though a little link back to here would be nice</font>