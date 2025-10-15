def g(x: int) -> int:
    if x > 22:
        return 9
    else:
        return 100 + x
      
def f(x: int) -> int:
    if x > 99:
        return 100
    elif 70 > x > 23:
        return 89 + x
    elif x > 20:
        return g(x) + 20
    elif x > -2:
        return 103
    else:
        return 99
# Hello
      