from functools import reduce

def f(x):
    return x*x

r1 = map(f,[1,2,3,4,5,6,7,8,9])

def add(x,y):
    return x+y

print("*".center(80,"-"))

relust = reduce(add,list(r1))

print(relust)


aTuple = (123, 'xyz', 'zara', 'abc');
aList = list(aTuple)
print(aTuple)
print(aList)
blist = list(aTuple)
print(blist)

