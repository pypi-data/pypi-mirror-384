import sys
sys.path.append('../src')
from isPrime import isPrime

def testIsPrime():
    assert isPrime(0)==False
    assert isPrime(-2)==False
    assert isPrime(1)==False
    assert isPrime(2)==True
    assert isPrime(4)==False
    assert isPrime(3)==True
    assert isPrime(20)==False
    assert isPrime(21)==False
    assert isPrime(23)==True