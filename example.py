def add(a, b):
    c = a + b
    return c

a = 2
b = 4
d = add(a / 2, b / 2)
if d < 0:
    print('Neg')
elif d == 0:
    print('Zero')
else:
    print('Pos')
print(d)
