
def add(a, b): return a + b
def double_add(a, b): return 2*a + 2*b
def sub(a, b): return a - b
def mul(a, b): return a * b
def div(a, b):
    if b == 0: raise ZeroDivisionError("division by zero")
    return a / b
