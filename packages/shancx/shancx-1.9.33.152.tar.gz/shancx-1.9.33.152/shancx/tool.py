
from itertools import product
def validate_param_list(param_list):
    if len(param_list) == 0:
        raise ValueError("param_list cannot be empty.")    
    for sublist in param_list:
        if len(sublist) == 0:
            raise ValueError("Sub-lists in param_list cannot be empty.")   
from concurrent.futures import ProcessPoolExecutor as PoolExecutor, as_completed 
import sys
from tqdm import tqdm 
def Mulsub(task, param_list, num=6):
    print(f"Pro num {num}")
    validate_param_list(param_list)
    if len(param_list) == 1:
        product_list = [(x,) for x in param_list[0]]
    else:
        product_list = list(product(*param_list))
    with PoolExecutor(max_workers=num) as executor:
        try:           
            futures = [executor.submit(task, item) for item in product_list]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing tasks", unit="task"):  
                pass
        except KeyboardInterrupt:
            sys.exit(1)    