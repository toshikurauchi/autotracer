
def double(n):
    return 2*n

def power_of_two(n):
    power = 1
    i = 0
    while i < n:
        power = double(power)
        i += 1
    return power


for i in range(2,4):
    power = power_of_two(i)
    print('2 to the power of {0} is {1}'.format(i, power))
