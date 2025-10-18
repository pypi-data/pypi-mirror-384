#!/usr/bin/env python
x = lambda y: y + 1
z = lambda a: a + 2

def foo() -> int:
    def bar() -> int:
        return 5
    def baz() -> int:
        return 6
    return bar()

def bar() -> int:
    def baz() -> int:
        return 7
    return baz()

print(x(1))
print(z(1))
print(foo())
print(bar())
