import yaml
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from pathlib import Path
import h5py

import warnings
from tables import NaturalNameWarning
warnings.filterwarnings('ignore', category=NaturalNameWarning)

def get_case_result(store: pd.io.pytables.HDFStore, object_type: str = '', object_name: str = '', scenario: int = None):
    return store.__getattr__(f'scen_{scenario}/{object_type}/{object_name}')
    
def get_case_objects(store: pd.io.pytables.HDFStore, object_type: str = ''):
    return [h5_path[2] for h5_path in [list(filter(None, k.split('/'))) for k in store.keys()] if h5_path[1] == object_type]

def get_scenarios(store: pd.io.pytables.HDFStore) -> list[int]:
    return [int(s.split('_')[1])for s in np.unique([h5_path.split('/')[1] for h5_path in store.keys()])]

def get_object_types(store: pd.io.pytables.HDFStore):
    return np.unique([h5_path[2] for h5_path in [h5_path.split('/') for h5_path in store.keys()]])

def trim_scenario(series: pd.Series) -> pd.Series:
    years, counts = np.unique(series.index.year, return_counts=True)
    year = years[counts.argmax()]
    return series[f'{year}':f'{year}']

def update_attribute_data(store: pd.io.pytables.HDFStore, object_type: str , object_name: str , scenario: int, data: pd.DataFrame ):
    store[f'scen_{scenario}/{object_type}/{object_name}']=data

def copy_file(old_path, new_path, ignore_scenarios_after):
    h5r=h5py.File(old_path, 'r')
    with h5py.File(new_path, 'w') as h5w:
        for obj in h5r.keys():
            if ignore_scenarios_after is not None:
                if int(obj.replace('scen_',''))>ignore_scenarios_after:
                    continue  #skip copying of scenarios we want to ignore
            h5r.copy(obj, h5w )       
    h5r.close()


"""Clean h5 result files"""
#The function "clean_results_h5" ensures continuous data for all shop scenarios, by updating the end of each scenario with data from the next scenario
#Each scenario is also trimmed so that its length is exactly one year
#The processed results are saved to a new folder with the same name as the result folder set in the system_config_file plus "_prepped"
#Scenarios after ignore_scenarios_after will be ignored and not written to the new result files.
#For testing: If overwrite is turned off, the processed results will be saved to a new folder with the suffix _prepped

#todo: if ignore_scenarios_after is set, check if data should still be taken from the next (ignored) scenario or not. 

def update_result_file(w_store, r_store, ignore_scenarios_after, case):
    object_types=get_object_types(r_store)
    scenarios=get_scenarios(r_store)
    scenarios.sort()
    n_scenarios=len(scenarios) if not ignore_scenarios_after else ignore_scenarios_after
    for i, this_scen in tqdm(enumerate(scenarios), total=n_scenarios, desc=f'Processing result files for {case}'):
        if ignore_scenarios_after is not None: #check if current scenario should be ignored
            if this_scen>ignore_scenarios_after:
                break
        for object_type in object_types:
            objects=get_case_objects(r_store, object_type=object_type)
            for object in objects:
                this_scenario_obj_df=get_case_result(r_store, object_type, object, scenario=this_scen) #get object data for current scenario
                if isinstance(this_scenario_obj_df, pd.DataFrame):
                    if (i != len(scenarios)-1): #if scenario is not last:
                        next_scen=scenarios[i+1]
                        next_scenario_obj_df=get_case_result(r_store, object_type, object, scenario=next_scen) #get object data for next scenario
                        next_starttime=next_scenario_obj_df.index[0] 
                        this_endtime=this_scenario_obj_df.index[-1]
                        data=next_scenario_obj_df[next_scenario_obj_df.index<this_endtime-pd.Timedelta(weeks=52)] #extract data from beginning of next scenario
                        data.index=data.index+pd.offsets.DateOffset(years=1) #change dates by one year
                        this_scenario_obj_df=this_scenario_obj_df[this_scenario_obj_df.index<next_starttime+pd.Timedelta(weeks=52)+pd.Timedelta(days=1)] #remove last part of this scenario
                        this_scenario_obj_df=pd.concat((this_scenario_obj_df, data)) #add data from beginning of next scenario
                        this_scenario_obj_df=trim_scenario(this_scenario_obj_df)
                    else: #if scenario is last
                        this_scenario_obj_df=get_case_result(r_store, object_type, object, scenario=this_scen)
                        this_scenario_obj_df=trim_scenario(this_scenario_obj_df)
                    update_attribute_data(w_store, object_type , object , this_scen, this_scenario_obj_df)


def prepare_results_h5(shop_result_path, cases, ignore_scenarios_after=None):
    for case in cases:
            path=os.path.join(shop_result_path, f'shop_{case}.h5') #path to results
            with pd.HDFStore(path, 'a') as store:
                update_result_file(store, store, ignore_scenarios_after, case)

def prepare_results_h5_new_folder(shop_result_path, cases, ignore_scenarios_after=None):
        for case in cases:
            path=os.path.join(shop_result_path, f'shop_{case}.h5') #path to raw results
            new_path=shop_result_path+f'_prepped/shop_{case}.h5' #path to new result folder
            Path(shop_result_path+f'_prepped/').mkdir(parents=True, exist_ok=True) #create folder if it doesnt exist already
            copy_file(path, new_path, ignore_scenarios_after)
            with pd.HDFStore(path, 'r') as store:
                with pd.HDFStore(new_path, 'w') as w_store:
                    update_result_file(w_store, store, ignore_scenarios_after, case)

def clean_results_h5(config_path, ignore_scenarios_after=None, overwrite=True):
    with open(config_path, 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    shop_result_path = config['shop']['result_folder']
    cases = [file.replace('.h5','').replace('shop_','') for file in os.listdir(shop_result_path) if file.endswith('.h5')] # Get available cases
    if overwrite:
        prepare_results_h5(shop_result_path, cases, ignore_scenarios_after)
    else:
        prepare_results_h5_new_folder(shop_result_path, cases, ignore_scenarios_after)