"""Independent arithmetic for retained-data audits; no benchmark/helper imports."""
import hashlib,math,random
from pathlib import Path

def median(values):
    values=sorted(values);n=len(values)
    if not n:raise AssertionError('empty observation set')
    return values[n//2] if n%2 else (values[n//2-1]+values[n//2])/2

def quantile(values,q):
    values=sorted(values);at=(len(values)-1)*q;lo=math.floor(at);hi=math.ceil(at)
    return values[lo]+(values[hi]-values[lo])*(at-lo)

def close(actual,expected):
    if not math.isclose(float(actual),expected,rel_tol=1e-10,abs_tol=1e-6):
        raise AssertionError(f'reported {actual!r}, independently computed {expected!r}')

def draws(n,count,seed):
    rng=random.Random(seed)
    return [[rng.randrange(n) for _ in range(n)] for _ in range(count)]

def interval(values,samples):
    values=[median(values[index] for index in sample) for sample in samples]
    return [quantile(values,.025),quantile(values,.975)]

def token_seed(seed,token):
    return seed^int.from_bytes(hashlib.sha256(token.encode()).digest()[:8],'big')

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def baseline_pairs(versions):
    assert versions[:2]==['master','current']
    return [('master',v) for v in versions[1:]]+[('current',v) for v in versions[2:]]

def pairs(versions):
    comparisons=baseline_pairs(versions)
    if 'route' in versions and 'final' in versions:comparisons.append(('route','final'))
    if 'pool' in versions and 'final' in versions:comparisons.append(('final','pool'))
    return comparisons

def declared_pairs(versions,declared):
    baseline=baseline_pairs(versions);declared=list(map(tuple,declared))
    allowed=[baseline]
    if 'route' in versions and 'final' in versions:allowed.append(baseline+[('route','final')])
    if 'pool' in versions and 'final' in versions:allowed.append(baseline+[('final','pool')])
    assert declared in allowed,('unexpected comparison plan',declared,allowed)
    return declared
