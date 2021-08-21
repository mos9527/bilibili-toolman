try:
    from tqdm import tqdm
    tqdm_ = tqdm(desc='↑', unit='B', unit_scale=True)  
except:
    tqdm_ = None
def report(current,max_val):
    if tqdm_ is None:return
    tqdm_.total = max_val
    tqdm_.n = current    
    tqdm_.update(0)
    tqdm_.refresh()
def close():
    if tqdm_ is None:return
    tqdm_.close()