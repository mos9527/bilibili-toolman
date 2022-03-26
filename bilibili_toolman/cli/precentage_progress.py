# -*- coding: utf-8 -*-
try:
    from tqdm import tqdm
    tqdm_ = tqdm(unit='B',unit_scale=True,maxinterval=0) 
    # setting maxinterval=0 to disable tqdm's internal monitor
except:
    tqdm_ = None
def report(current,max):    
    if tqdm is not None:
        tqdm_.total = max
        tqdm_.n = current   
        tqdm_.refresh()
def close():
    # silence tqdm
    if tqdm is not None:
        tqdm_.disable = True