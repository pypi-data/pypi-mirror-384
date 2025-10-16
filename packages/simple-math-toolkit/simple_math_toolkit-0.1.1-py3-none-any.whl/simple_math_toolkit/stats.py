
def mean(values):
    values = list(values)
    if not values: raise ValueError("mean() of empty sequence")
    return sum(values) / float(len(values))

def median(values):
    values = sorted(values); n = len(values)
    if n == 0: raise ValueError("median() of empty sequence")
    mid = n // 2
    return values[mid] if n % 2 == 1 else (values[mid - 1] + values[mid]) / 2.0
