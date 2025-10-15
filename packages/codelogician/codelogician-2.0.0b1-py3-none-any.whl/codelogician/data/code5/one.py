


class MyClass:

    def __init__(self, a, b, c):
        self._a = a
        self._b = b
        self._c = c

    def compute(self, d):
        return self._a * d + self._b + self._c
    

# Prove that this function always returns a positive value
def george_function(a : int, b : int):
    if a > 0:
        return a * 100
    if b < 0: return b * -20

    return 101

# Decompose this
def other_function(a : int):

    if a < -100:
        if a > -25: return -123
    elif a < 10:
        return a + 200
    else:
        350
