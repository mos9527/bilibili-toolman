import tqdm
pbar = None
def report_progress(current,max_val):
    global pbar
    if not pbar and (current<max_val):
        pbar = tqdm.tqdm(desc='Uploading',total=max_val,unit='B',unit_scale=True)         
    pbar.update(current - pbar.n)
    if (current>=max_val):
        pbar.reset()
        pbar.close()        