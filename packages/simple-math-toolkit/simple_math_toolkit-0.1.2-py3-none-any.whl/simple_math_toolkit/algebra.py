
import math
def quadratic_roots(a, b, c):
    if a == 0:
        if b == 0: raise ValueError("Both a and b are zero; not an equation")
        return (-c / b, )
    d = b*b - 4*a*c
    sqrt_d = math.sqrt(d) if d >= 0 else math.sqrt(-d) * 1j
    return ((-b - sqrt_d) / (2*a), (-b + sqrt_d) / (2*a))
