import sys
import os

# Aktuelles Verzeichnis des Skripts ermitteln
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '../src')
sys.path.append(src_dir)
from getPrimeGen import getPrimeGenFrom, getPrimeGenTo 

def testGetPrimeGenFrom():
    g = getPrimeGenFrom(-2)
    assert next(g) == 2
    assert next(g) == 3
    assert next(g) == 5
    assert next(g) == 7
    
def testGetPrimeGenTo():
<<<<<<< HEAD
=======
    
>>>>>>> ba7de50 (Init.)
    assert [2]==getPrimeGenTo(2)
    assert [2,3]==getPrimeGenTo(4)
    assert [2,3, 5]==getPrimeGenTo(5)
    assert [2,3, 5]==getPrimeGenTo(6)
    assert [2,3,5,7]==getPrimeGenTo(7)
<<<<<<< HEAD
    
=======
    
if __name__ == '__main__':
    getPrimeGenTo(2)
>>>>>>> ba7de50 (Init.)
