from tqdm import tqdm
tqdm_ = tqdm(desc='↑', unit='B', unit_scale=True)  
def report(current,max_val):
    tqdm_.total = max_val
    tqdm_.n = current    
    tqdm_.update(0)
    tqdm_.refresh()
def close():
    tqdm_.close()