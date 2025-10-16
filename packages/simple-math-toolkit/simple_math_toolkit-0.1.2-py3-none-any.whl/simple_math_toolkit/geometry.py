
import math
def area_circle(r):
    if r < 0: raise ValueError("radius must be non-negative")
    return math.pi * r * r

def perimeter_rectangle(w, h):
    if w < 0 or h < 0: raise ValueError("width/height must be non-negative")
    return 2*(w + h)
