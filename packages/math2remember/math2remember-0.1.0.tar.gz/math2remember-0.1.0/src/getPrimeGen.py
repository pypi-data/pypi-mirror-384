from isPrime import isPrime 
def getPrimeGenFrom(n):
    while True:
        if isPrime(n):
            yield n
        n += 1
      
def sieve(n):
    l = [{'num':i,'isPrime': False} for i in range(0, n + 1)]
    for ele in l:
        if ele['isPrime']:
            continue
        if isPrime(ele['num']):
                ele['isPrime']=True
                idx = l.index(ele) * 2
                while idx < n + 1:
                    l[idx]['isPrime']=False    
                    idx += ele['num']
                    
    return [ele['num'] for ele in l if ele['isPrime']] 
        
def getPrimeGenTo(n):
    return sieve(n)