import h5py
import pandas as pd
import numpy as np
import yaml, pickle
import os
import datetime
import copy
from tqdm import tqdm
from typing import Union, Any
from scipy.spatial import ConvexHull
from pathlib import Path

from pyshop import ShopSession
from pyprodrisk import ProdriskSession

from prodrisk_shop_simulator.cuts import Cuts, read_prodrisk_cuts, convert_prodrisk_cuts_to_shop_cuts
from prodrisk_shop_simulator.input.pump import get_pump_values, add_simple_pump, add_variable_pump

import warnings
from tables import NaturalNameWarning

from prodrisk_shop_simulator.services.shop_derived_attributes import get_max_time_delay
warnings.filterwarnings('ignore', category=NaturalNameWarning)

KEEP_RESULTS_IN_MEMORY = "keep_results_in_memory"
SAVE_RESULTS_TO_H5 = "save_results_to_h5"
SET_STARTVOLS_FROM_PRODRISK_SCEN_STARTVOLS = "set_start_vols_from_prodrisk_scen_start_vols"
class Simulator():

    def __init__(self, prodrisk_session: ProdriskSession,
                 shop_model: Union[str, ShopSession],
                 config_file: Union[str, dict],
                 price_scenarios: pd.DataFrame = None,
                 inflow_series: dict = None,
                 shop_sim_model: Union[Any, str, ShopSession] = None,
                 shop_output_attributes: dict=None,
                 ) -> "Simulator":
        '''
        Initialize the simulator.
        
        :param prodrisk_session: ProdRisk session with the long ProdRisk run already executed.
        :param shop_model: Shop session or path to yaml-file with the SHOP model to use
        :param config_file: Path to yaml-file or dict with simulator settings.
        :param price_scenarios: DataFrame with price scenarios to use in SHOP.
        :param inflow_series: Dict with inflow series to use in SHOP. Key is series name, value is DataFrame with time index and scenario columns.
        :param shop_sim_model: Shop session or path to yaml-file with the SHOP model to use in the shop_sim.
        :param shop_output_attributes: Dict with output attributes to save from SHOP. 
            If None, all txy output attributes are saved.
        '''

        print('Init simulator')
        
        # Settings
        if isinstance(config_file, str):
            with open(config_file, "r", encoding="utf-8") as file:
                self.settings = yaml.load(file, Loader=yaml.FullLoader)
        else:
            self.settings = dict(config_file)

        shop_license_path = self.settings.get("shop_license_path")
        if shop_license_path:
            os.environ["SHOP_LICENSE_PATH"] = shop_license_path

        shop_binary_path = self.settings.get("shop_binary_path")
        if shop_binary_path:
            os.environ["SHOP_BINARY_PATH"] = shop_binary_path

        if not "SHOP_BINARY_PATH" in os.environ:
            raise RuntimeError("SHOP binary path not set. Please set 'shop_binary_path' in the simulator config yaml-file, or set the environment variable 'SHOP_BINARY_PATH'.")

        if isinstance(shop_model, str):
            self.shop_model = ShopSession()
            self.shop_model.load_yaml(file_path=shop_model)
        else: 
            self.shop_model = shop_model

        self.long_prodrisk = prodrisk_session

        shop_time_res = self.shop_model.get_time_resolution()
        shop_start = shop_time_res["starttime"]
        if shop_start != self.long_prodrisk.start_time:
            raise RuntimeError(f"SHOP and ProdRisk must have same start time: {shop_start} {self.long_prodrisk.start_time}")

        shop_end = shop_time_res["endtime"]
        if shop_end != shop_start + pd.Timedelta(days=364):
            raise RuntimeError(f"SHOP end time should be 364 days after start time: {shop_end-shop_start}")

        self.price_scenarios = price_scenarios
        self.inflow_series = inflow_series
        
        # Allow running SHOP with longer horizon, but still only select results from the "shop_step_length".
        if "shop_horizon_days" in self.settings.keys():
            self.settings["shop_horizon_days"] = pd.Timedelta(days=self.settings["shop_horizon_days"])
        else:
            self.settings["shop_horizon_days"] = pd.Timedelta(days=7)


        self.settings["shop_step_length"] = pd.Timedelta(weeks=1)

        if "pop_water_value_input" not in self.settings["shop"]:
            self.settings["shop"]["pop_water_value_input"] = True

        # Modify SHOP input.
        self.modify_shop_input()

        # Setting used to run a shop_sim based on schedules based on the weekly SHOP optimizations, and save the results from this simulation.
        if "shop_sim" in self.settings["shop"] and self.settings["shop"]["shop_sim"]:
            if shop_sim_model is not None:
                if isinstance(shop_sim_model, str):
                    self.shop_sim_model = ShopSession()
                    self.shop_sim_model.load_yaml(file_path=shop_sim_model)
                else: 
                    self.shop_sim_model = shop_sim_model
            else:
                # Use the SHOP optimization model also in the shop_sim.
                if isinstance(shop_model, str):
                    self.shop_sim_model = ShopSession()
                    self.shop_sim_model.load_yaml(file_path=shop_model)
                else: 
                    self.shop_sim_model = shop_model
        else:
            self.settings["shop"]["shop_sim"] = False

        # Map ProdRisk stochastic time series to SHOP scenarios.
        self.set_up_txy_mapping()

        # Could also be of interest to map other input txys, for example minVol, minDischarge, minBypass etc.
        extra_txy_mapping = self.settings.get("extra_txy_mapping")
        if extra_txy_mapping:
            self.txy_mapping.update(extra_txy_mapping) 

        # SHOP results
        if shop_output_attributes is None:
            self.set_up_shop_output_attributes()
        else:
            self.settings['shop_output_attributes'] = shop_output_attributes
        self.shop_result_scenarios = {}

        self.attrs_with_endpoint = ["head", "storage"]

        # If shop_sim is not used, these attributes are used to set initial values in SHOP from results from SHOP optimization of previous week.
        # (object_type, optimization_result_attribute) : initial_state_attribute_in_shop
        self.attributes_from_to = {
            ("reservoir", "storage"): "start_vol",
            # ("reservoir", "head"): "start_head",
            ("generator", "committed_out"): "initial_state",
            ("pump", "committed_out"): "initial_state",
            ("tunnel", "gate_opening"): "initial_opening",
            ("river", "gate_height"): "initial_opening",
            ("river", "upstream_flow"): "past_upstream_flow",
        }

        # If shop_sim is used, these attributes are used to set initial values in SHOP from result from SHOP sim of previous week.
        # (object_type, simulation_result_attribute) : initial_state_attribute_in_shop
        if self.settings["shop"]["shop_sim"]:
            self.attributes_from_to = {
            ("reservoir", "sim_storage"): "start_vol",
            ("reservoir", "sim_head"): "start_head",
            ("generator", "sim_discharge"): "initial_state",
            ("pump", "sim_upflow"): "initial_state",
            ("tunnel", "gate_opening_schedule"): "initial_opening",
            ("river", "gate_opening_schedule"): "initial_opening",
            ("river", "sim_flow"): "past_upstream_flow",
        }

        # Make sure the initial state transition attributes are saved.
        for (obj_type, attr_name) in self.attributes_from_to.keys():
            if obj_type not in self.settings['shop_output_attributes']:
                self.settings['shop_output_attributes'][obj_type] = []
            if attr_name not in self.settings['shop_output_attributes'][obj_type]:
                self.settings['shop_output_attributes'][obj_type].append(attr_name)


        # Have to save results somewhere
        if SAVE_RESULTS_TO_H5 not in self.settings.keys():
            self.settings[SAVE_RESULTS_TO_H5] = True 
        
        if KEEP_RESULTS_IN_MEMORY not in self.settings.keys():
            self.settings[KEEP_RESULTS_IN_MEMORY] = False

        if SET_STARTVOLS_FROM_PRODRISK_SCEN_STARTVOLS not in self.settings.keys():
            self.settings[SET_STARTVOLS_FROM_PRODRISK_SCEN_STARTVOLS] = False
    
    def modify_shop_input(self):
        yaml_dump = yaml.load(self.shop_model.dump_yaml(), Loader=yaml.FullLoader)
        
        # Remove all water value inputs
        if self.settings["shop"]["pop_water_value_input"]:
            self.pop_object_type_attribute(yaml_dump, "reservoir", "water_value_input")
            self.pop_object_type_attribute(yaml_dump, "reservoir", "energy_value_input")
            self.pop_object_type_attribute(yaml_dump, "inflow_series", "cut_coeffs")
            self.pop_object_type_attribute(yaml_dump, "cut_group", "rhs")

        self.shop_model = ShopSession()
        self.shop_model.load_yaml(yaml_string=yaml.dump(yaml_dump, Dumper=yaml.Dumper))

    def pop_object_type_attribute(self, yaml_dump, object_type, attribute):
        if object_type in yaml_dump["model"]:
            for obj in yaml_dump["model"][object_type]:
                if attribute in obj:
                    obj.pop(attribute)
    

    def load_cuts_from_file(self, case_name=None, info=''):
        print("\nLoading cuts from file")
        folder=f"{self.settings['prodrisk']['cuts']['folder']}/{case_name}_{info}/" if info else f"{self.settings['prodrisk']['cuts']['folder']}/cuts_{case_name}/"
        self.prodrisk_cuts = {}
        for f in os.listdir(folder):
            if f.endswith('.pkl'):
                with open(os.path.join(folder, f), 'rb') as fp:
                    self.prodrisk_cuts[pd.Timestamp(f[4:-4])] = pickle.load(fp)

        self.shop_cuts = convert_prodrisk_cuts_to_shop_cuts(self.prodrisk_cuts)


    def save_cuts_to_file(self, case_name=None,  info=''):
        folder=f"{self.settings['prodrisk']['cuts']['folder']}/{case_name}_{info}/" if info else f"{self.settings['prodrisk']['cuts']['folder']}/cuts_{case_name}/"
        for t,v in self.prodrisk_cuts.items():
            filename = os.path.join(folder, f'cut_{t.strftime("%Y%m%d")}.pkl')
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as c:
                pickle.dump(v, c)

    def load_cuts_from_prodrisk(self):
        self.prodrisk_cuts = read_prodrisk_cuts(self.long_prodrisk)
        self.shop_cuts = convert_prodrisk_cuts_to_shop_cuts(self.prodrisk_cuts)


    def set_up_shop_output_attributes(self):
        self.settings["shop_output_attributes"] = {}
        shop = self.shop_model
        shop_api = shop.shop_api

        for obj_type in shop_api.GetObjectTypesInSystem():
            type_result_attrs = []

            for attr in shop_api.GetObjectTypeAttributeNames(obj_type):         
                
                if shop_api.GetAttributeInfo(obj_type, attr, "isOutput") and shop_api.GetAttributeInfo(obj_type, attr, "datatype") == 'txy':
                    type_result_attrs.append(attr)

            self.settings["shop_output_attributes"][obj_type] = type_result_attrs

    def set_up_txy_mapping(self):
        self.txy_mapping = {}
        area_name = self.long_prodrisk.model.area.get_object_names()[0]

        market_name = self.shop_model.model.market.get_object_names()[0]
        
        self.txy_mapping[("area", area_name, "price")] =  [(("market", market_name, "sale_price"), 1.0), (("market", market_name, "buy_price"), 1.01)]

        for mod in self.long_prodrisk.model.module.get_object_names():
            # Map module local inflow to SHOP reservoirs.
            self.txy_mapping[("module", mod, "localInflow")] =  []

            # If a inflow mapping is specified for this module, use this:
            if mod in self.settings["mapping"]["module_inflow_to_rsv"].keys():
                rsv_inflows = self.settings["mapping"]["module_inflow_to_rsv"][mod]
                for rsv, factor in rsv_inflows.items():
                    self.txy_mapping[("module", mod, "localInflow")].append((("reservoir", rsv, "inflow"), factor))
                continue

            # If only one reservoir is connected to this module:
            if mod in self.settings["mapping"]["cut_module_to_rsv"] and len(self.settings["mapping"]["cut_module_to_rsv"][mod])==1:
                
                rsv = self.settings["mapping"]["cut_module_to_rsv"][mod][0]
                self.txy_mapping[("module", mod, "localInflow")].append((("reservoir", rsv, "inflow"), 1.0))
            else:
                print(f"WARNING: Module inflow to {mod} not added to any SHOP reservoirs. Please check your mapping tables in the simulator config yaml-file!")        

    def run_serial_simulation(self, scenarios: list = None, case_name: str = None, resume_scenario: int = 0, resume_week: int = 1, start_scen_week: tuple = (0, 1), end_scen_week: tuple = None):
        """
        Start serial simulation. SHOP is simulated sequentially scenario by scenario using cuts from prodrisk as end values.
        """

        print("\nInit SHOP simulations")

        if not self.long_prodrisk.is_series_simulation.get():
            # The set_init_state method needs to be updated to not transfer information 
            # from one scenario to the next in parallel simulations...
            # Parallel simulations should also utilize parallell processing!
            exit("The simulator so far only support series simulation.")

        if scenarios is None:
            scenarios = range(resume_scenario, self.long_prodrisk.n_scenarios)

        if end_scen_week is None:
            end_scen_week = (self.long_prodrisk.n_scenarios, 52)
        
        # Check that combination of resume_week, start_scen_week, end_scen_week is valid
        if resume_scenario < start_scen_week[0]:
            print(f"\nResume scenario is {resume_scenario} which is less than start scenario {start_scen_week[0]}. Changing resume_scenario to start scenario value.")
            resume_scenario = start_scen_week[0]
        if resume_scenario == start_scen_week[0]:
            if resume_week < start_scen_week[1]:
                print(f"\nResume and start scenario are equal, while resume week is {resume_week} which is less than start week {start_scen_week[1]}. Changing resume_week to start week.")
                resume_week = start_scen_week[1]
        assert resume_scenario <= end_scen_week[0], f"Resume scenario is {resume_scenario} and end scenario {end_scen_week[0]}. Resume scenario can not be greater than end scenario."
        if resume_scenario == end_scen_week[0]:
            assert resume_week <= end_scen_week[1], f"Resume and end scenario are {resume_scenario}. Resume week is {resume_week} and end week {end_scen_week[1]}. Resume week can not be greater than end week when resume and end scenario are equal."

        # Write new SHOP
        if resume_scenario == start_scen_week[0] and resume_week == start_scen_week[1]:
            with pd.HDFStore(os.path.join(self.settings['shop']['result_folder'], f'shop_{case_name}.h5'), 'w') as store:
                pass

        for scen in scenarios:
            # Find start and end week for current scenario (1 and 52 if nothing else given)
            start_week = 1
            end_week = 52
            if scen == start_scen_week[0]:
                start_week = start_scen_week[1]
            elif scen == end_scen_week[0]:
                end_week = end_scen_week[1]
            elif scen > end_scen_week[0]:
                return

            if scen < resume_scenario or scen < start_scen_week[0]: # Skip scenario if less than resume or start scenario
                continue
            
            if scen == resume_scenario:
                sim_scen_status = self.simulate_scen_with_shop(scen=scen, case_name=case_name, resume_week=resume_week, start_week=start_week, end_week=end_week, start_scen=scen == start_scen_week[0])
            else:
                sim_scen_status = self.simulate_scen_with_shop(scen=scen, case_name=case_name, start_week=start_week, end_week=end_week, start_scen=scen == start_scen_week[0])

            if not sim_scen_status:
                print(f"Simulation failed for scenario {scen}. Aborts run...")
                return
            

    def simulate_scen_with_shop(
            self, 
            scen: int, 
            shop_io: ShopSession = None, 
            shop_sim_io: ShopSession = None, 
            case_name: str = None, 
            resume_week: int = 1, 
            start_week: int = 1, 
            end_week: int = 52, 
            start_scen: bool = False
        ) -> bool:

        """
        Simulate a scenario in SHOP based on cuts from a ProdRisk session
        
        :param scen: scenario number in the long Prodrisk run to simulate over
        :param shop_io: Shop session with input data for the whole scenario. 
            As default, this is set up based on the shop_yaml_string input given to the simulator, but this input argument may provide extra flexibility

        :return: 
            - True if simulation was successful
            - False if simulation failed
        """

        if shop_io is None:
            shop_io = self.init_shop_scen_io_based_on_input_shop_session(self.shop_model, scen=scen)

        if self.settings["shop"]["shop_sim"] and shop_sim_io is None:
            shop_sim_io = self.init_shop_scen_io_based_on_input_shop_session(self.shop_sim_model, scen=scen)

        self.shop_result_scenarios[f"scen_{scen}"] = {}

        time_resolution = shop_io.get_time_resolution()
        
        scen_start_time = time_resolution["starttime"]
        scen_end_time = time_resolution["endtime"]
        
        prev_shop = None
        tr_start = pd.date_range(scen_start_time, scen_end_time, freq=self.settings['shop_step_length'], inclusive="left")
        tr_end = tr_start + self.settings["shop_horizon_days"]

        # Convert SHOP IO to yaml string (only once to save time)
        shop_io_dict = yaml.load(shop_io.dump_yaml(), Loader=yaml.FullLoader)
        shop_io_dict.pop('time')
        for rsv in shop_io_dict['model']['reservoir'].keys():
            if 'start_head' in shop_io_dict['model']['reservoir'][rsv]:
                shop_io_dict['model']['reservoir'][rsv].pop('start_head')
            if 'start_vol' in shop_io_dict['model']['reservoir'][rsv]:
                shop_io_dict['model']['reservoir'][rsv].pop('start_vol')
        shop_io_str = yaml.dump(shop_io_dict, Dumper=yaml.Dumper)
        
        for i in tqdm(range(max(start_week, resume_week) - 1, end_week), desc=f"Scenario {scen}"):
            # The "update-functionality" must be rewritten to be based on the ProdriskSession "long_prodrisk", not on file based input...
            # This implementation should be based on get_updated_cuts() from the old simulator code!
            """ if user_input.settings.update_if.check(s, cut_week):
                if user_input.settings.follow_update and (vol_curve!=None) and (s+cut_week)>0:
                    upd_start_vol = {}
                    for mod in user_input.case_input.mod_to_rsv.keys():
                        sc = s if cut_week>0 else s-1
                        cw = cut_week-1 if sc==s else 51
                        volumes = vol_curve.get_mod_vol_in_scen(mod,sc)
                        upd_start_vol[mod] = volumes['update'][cw+1]
                    ProdriskInput.initial_state = ProdriskState(upd_start_vol)
                else:
                    get_prodrisk_startvols_from_shop_startvols(ProdriskInput, ShopInput, user_input)
                #user_input.settings.use_cuts_as_endvalue_in_prodrisk = True
                #ProdriskInput.end_value_cuts = ProdriskInput.cut_list[UserInput.settings.prodrisk_update_horizon_nweeks-1]
                new_shop_cuts, new_prodrisk_cuts, upd_prodrisk = get_updated_cuts(ProdriskInput, local_prodrisk_time, user_input, s, cut_week, TC,
                                                                        update_subfolder=f'update_scen_{s}_week_{cut_week}', long_prodrisk=long_prodrisk)
                TC.set_state('SHOP')
                if vol_curve!=None:
                    vol_curve.import_update_results(upd_prodrisk, s, cut_week)
                for w in range(user_input.settings.prodrisk_update_horizon_nweeks):
                    ShopInput.cut_list[(w+cut_week)%52] = new_shop_cuts[w]
                    #ProdriskInput.cut_list[(w+cut_week)%52] = new_prodrisk_cuts[w]
            """
            step_start_time = tr_start[i]
            step_end_time = tr_end[i]
            prev_shop = self.run_shop(shop_io_str, step_start_time, step_end_time, scen, case_name=case_name, first_scen=start_scen, first_week=(i+1)==start_week)

            if prev_shop is None:
                week_no = int((step_end_time - self.long_prodrisk.start_time).total_seconds() / (168.0 * 3600))
                print("SHOP failed for cut week: " + str(week_no) + " scen: " + str(scen))
                return False
            self.save_shop_results(
                shop=prev_shop, 
                scen=scen, 
                case_name=case_name
            )

            if self.settings["shop"]["shop_sim"]:
                prev_shop = self.run_shop_sim(
                    shop_sim_io=shop_sim_io, 
                    optimization_session=prev_shop, 
                    case_name=case_name, 
                    scen=scen
                )

                if prev_shop is None:
                    week_no = int((step_start_time - self.long_prodrisk.end_time).total_seconds() / (168.0 * 3600))
                    print("SHOP simulation failed for cut week: " + str(week_no) + " scen: " + str(scen))
                    return False

                self.save_shop_results(prev_shop, scen, case_name)

        # Return True if simulation of scenario was successfull (already returned False if something failed)
        return True


    def init_shop_scen_io_based_on_input_shop_session(self, shop_model: ShopSession, scen: int) -> ShopSession:            
        # Dump the input SHOP session to yaml-dict
        yaml_dump = yaml.load(shop_model.dump_yaml(), Loader=yaml.FullLoader) # TODO - check timing

        # Adjust start and end times of the scenario based on "shop_horizon_days". 
        # For runs with "extended SHOP horizon" (shop_horizon_days > shop_step_length) the scenario should start a few days earlier
        # Input is then found from the "previous scenario" for the extra added days.
        scen_time_res = yaml_dump.pop('time')
        scen_start_time = scen_time_res["starttime"] + self.settings["shop_step_length"] - self.settings["shop_horizon_days"]
        scen_end_time = scen_time_res["endtime"]

        # Init SHOP session with set start time, end time and input data from yaml-dict
        shop_io = ShopSession()
        shop_io.set_time_resolution(starttime=scen_start_time, endtime=scen_end_time, timeunit="hour")
        shop_io.load_yaml(yaml_string=yaml.dump(yaml_dump, Dumper=yaml.Dumper))

        # Add time series for given scenario (price, inflows, others?)
        self.add_scen_txys(shop_io, scen)

        # Use price from price_scenarios if given (ProdRisk can not store fine time resolution than it has been executed with)
        if self.price_scenarios is not None:
            n_scen = self.price_scenarios.shape[1]
            scen_before = self.price_scenarios.iloc[:, (scen - 1) % n_scen]
            starttime = scen_before.index[0]
            scen_before = scen_before[starttime+pd.Timedelta(days=357):starttime+pd.Timedelta(days=364, hours=-1)]
            scen_before.index = scen_before.index - pd.Timedelta(days=364)
            price_scen = pd.concat([
                scen_before,
                self.price_scenarios.iloc[:, scen]
            ])
            for m in shop_io.model.market:
                m.buy_price.set(price_scen + 0.01)
                m.sale_price.set(price_scen)
        
        # Set inflow series to SHOP based on finer time resolution
        if self.inflow_series is not None:
            # For each module - find correponding inflow series
            for mod in self.long_prodrisk.model.module:
                mod_name = mod.get_name()
                inflow_series_index = mod.connectedSeriesId.get()
                # Only update inflow series for the given series, otherwise use default from Prodrisk
                if not f'I-{inflow_series_index}' in self.inflow_series:
                    continue
                inflow_profile = self.inflow_series[f'I-{inflow_series_index}'][scen].resample(pd.Timedelta(hours=1)).ffill()
                local_inflow = mod.localInflow.get()[scen].resample(pd.Timedelta(hours=1)).ffill()
                scale_interval_start = scen_start_time + self.settings['shop_horizon_days'] - pd.Timedelta(days=7)
                scale_interval_end = scale_interval_start + pd.Timedelta(days=360)
                profile_scale_factor = local_inflow[scale_interval_start:scale_interval_end].sum() / inflow_profile[scale_interval_start:scale_interval_end].sum()
                
                # Use mapping to find all reservoirs using this profile and insert scaled profile for inflow_profile
                for rsv, rsv_scale_factor in self.settings['mapping']['module_inflow_to_rsv'][mod_name].items():
                    shop_io.model.reservoir[rsv].inflow.set(inflow_profile * profile_scale_factor * rsv_scale_factor)

        return shop_io

    def run_shop(
            self, 
            shop_io: str, 
            start_time: pd.Timestamp, 
            end_time: pd.Timestamp, 
            scen: int, 
            case_name: str = None, 
            first_scen: bool = False, 
            first_week: bool = False
        ) -> bool:

        """
        Run one SHOP case as part of the simulation along a scenario

        :param shop_io: Shop session with input data for the whole scenario. 
        :param shop_step_length: Step length of each SHOP case in the simulation.
        :param start_time: Start time of the weekly shop problem.
        :param end_time: End time of the weekly shop problem.
        :param scen: Scenario counter. Used by 
            - log statements
            - SHOP/cplex log file names
            - Setting initial state per scenario
            - For extracting scenario-dependent input from the long_prodrisk run (price, inflow).
            - yaml file names, if each weekly SHOP problem is said to be dumped to yaml-file (for debugging purposes).
        :param case_name: str, if set (not None), yaml files are dumped to the folder set by settings['shop']['model_folder],
            where case_name is part of the file name for each weekly shop-yaml-dump.
        :param first_scen: bool, 
        """	
        # INITIALIZE SHOP API #
        shop = ShopSession()
        shop.set_time_resolution(starttime=start_time, endtime=end_time, timeunit='hour')

        if 'log_folder' in self.settings['shop']:
            shop_log_name = f"shop_sim_log_scen_{scen}_{start_time.strftime('%Y-%m-%d')}.log"
            cplex_log_name = f"cplex_log_scen_{scen}_{start_time.strftime('%Y-%m-%d')}.log"

            if case_name is not None:
                Path(f'{self.settings["shop"]["log_folder"]}/{case_name}/').mkdir(parents=True, exist_ok=True)
                shop_log_name = f'{self.settings["shop"]["log_folder"]}/{case_name}/{shop_log_name}'
                cplex_log_name = f'{self.settings["shop"]["log_folder"]}/{case_name}/{cplex_log_name}'
            else:
                shop_log_name = f'{self.settings["shop"]["log_folder"]}/{shop_log_name}'
                cplex_log_name = f'{self.settings["shop"]["log_folder"]}/{cplex_log_name}'
            
            shop.model.global_settings.global_settings.shop_log_name.set(shop_log_name)
            shop.model.global_settings.global_settings.solver_log_name.set(cplex_log_name)

        shop.load_yaml(yaml_string=shop_io)

        if first_week:
            self.set_init_state_from_prodrisk_or_prev_scen(shop, scen, case_name, first_scen)
        else:
            self.set_init_state(shop, scen, case_name)

        # Access cuts by end time. Use different indexing for the SHOP cuts than the ProdRisk cuts
        # This provides flexibility in the horizon of the "SHOP weeks".
        while end_time not in self.shop_cuts:
            end_time -= self.settings['shop_step_length']
        week_cuts = self.shop_cuts[end_time]
        self.add_cuts(shop, week_cuts=week_cuts)
        
        # Additional mappings
        if 'txy' in self.settings['mapping']:
            for txy in self.settings['mapping']['txy']:
                shop.model[txy['shop']['type']][txy['shop']['name']][txy['shop']['attribute']].set(
                    self.long_prodrisk.model[txy['prodrisk']['type']][txy['prodrisk']['name']][txy['prodrisk']['attribute']].get()[scen] * txy['scaling']
                )

        # Run weekly SHOP case, by commands specified on the SHOP input...
        shop.load_yaml(yaml_string=yaml.dump({'commands': self.settings['shop']['commands']}, Dumper=yaml.Dumper))
        shop_status = shop.model.objective.average_objective.solver_status.get()
        if 'model_folder' in self.settings['shop']:
            if case_name is not None:
                Path(f'{self.settings["shop"]["model_folder"]}/{case_name}/').mkdir(parents=True, exist_ok=True)
                shop.dump_yaml(f'{self.settings["shop"]["model_folder"]}/{case_name}/shop_model_scen{scen}_{start_time.strftime("%Y-%m-%d")}.yaml', input_only=False)
            else:
                shop.dump_yaml(f'{self.settings["shop"]["model_folder"]}/shop_model_scen{scen}_{start_time.strftime("%Y-%m-%d")}.yaml', input_only=False)


        if shop_status is None or ("infeas" in shop_status and "Optimal" not in shop_status) or "ERROR" in shop_status or "Error" in shop_status:
            return None

        return shop
    
    def run_shop_sim(
            self, 
            shop_sim_io: ShopSession, 
            optimization_session: ShopSession, 
            case_name: str, 
            scen: int
        )-> ShopSession:

        """
        Run a SHOP simulation based on schedules from an optimization of the corresponding week.
        Use the results from these simulations as the results for each scenario in the ProdRisk-SHOP simulator.

        :param shop_sim_io: Shop session with input data for SHOP simulations for the whole scenario. 
        :param optimization_session: The shop session to set schedules from on the shop_sim session
        :param case_name: str, if set (not None), used as prefix of shop log file for the shop_sim run
        :param scen: Included in the log file names for the shop_sim runs.

        :returns: The shop_sim session, from which results saved to h5-file and/or memory dict are extracted.
        """	

        timeres = optimization_session.get_time_resolution()
        start_time = timeres['starttime']
        end_time = timeres['endtime']
        # INITIALIZE SHOP API #
        shop = ShopSession()
        shop.set_time_resolution(starttime=start_time, endtime=end_time, timeunit='hour')

        if 'log_folder' in self.settings['shop']:
            shop_log_name = f"shop_sim_log_scen_{scen}_{start_time.strftime('%Y-%m-%d')}.log"

            if case_name is not None:
                Path(f'{self.settings["shop"]["log_folder"]}/{case_name}/').mkdir(parents=True, exist_ok=True)
                shop_log_name = f'{self.settings["shop"]["log_folder"]}/{case_name}/{shop_log_name}'
            else:
                shop_log_name = f'{self.settings["shop"]["log_folder"]}/{shop_log_name}'

            shop.model.global_settings.global_settings.shop_log_name.set(shop_log_name)
        
        yaml_dump = yaml.load(shop_sim_io.dump_yaml(), Loader=yaml.FullLoader)
        yaml_dump.pop('time')
        shop.load_yaml(yaml_string=yaml.dump(yaml_dump, Dumper=yaml.Dumper))

        self.set_sim_init_state(optimization_session, shop)
        self.set_schedules(optimization_session, shop)

    
        
        # Run weekly SHOP case, by commands specified on the SHOP input...
        shop.start_shopsim(options=["gen_m3s_schedule"], values=[])
        shop_status = shop.model.objective.average_objective.solver_status.get()
        if 'model_folder' in self.settings['shop']:
            shop.dump_yaml(f'{self.settings["shop"]["model_folder"]}/shop_sim_model_{start_time.strftime("%Y-%m-%d")}.yaml')

        if shop_status is None or ("infeas" in shop_status and "Optimal" not in shop_status) or "ERROR" in shop_status or "Error" in shop_status:
            return None

        return shop         

    def set_schedules(self, optimization_session: ShopSession, simulation_session: ShopSession):

        for gen_name in simulation_session.model.generator.get_object_names():
            gen = simulation_session.model.generator[gen_name]
            #gen.production_schedule.set(optimization_session.model.generator[gen_name].production.get())
            gen.discharge_schedule.set(optimization_session.model.generator[gen_name].discharge.get())

        for pump_name in simulation_session.model.pump.get_object_names():
            pump = simulation_session.model.pump[pump_name]
            pump.upflow_schedule.set(optimization_session.model.pump[pump_name].upflow.get())

        for tunnel_name in simulation_session.model.tunnel.get_object_names():
            tunnel = simulation_session.model.tunnel[tunnel_name]
            if tunnel.gate_opening_curve.get() is not None:
                tunnel.gate_opening_schedule.set(optimization_session.model.tunnel[tunnel_name].gate_opening.get())

        for river_name in simulation_session.model.river.get_object_names():
            river = simulation_session.model.river[river_name]

            gate_opening_curve = river.gate_opening_curve.get()

            gate_height = optimization_session.model.river[river_name].gate_height.get()
            
            # Interpolate gate_height values using the gate_opening_curve as an xy mapping
            gate_opening_curve = river.gate_opening_curve.get()
            if gate_opening_curve is not None:
                # gate_opening_curve: index = opening, values = height
                # We want to invert this: for each gate_height value, find the corresponding opening
                # Interpolate opening as a function of height

                # Remove NaNs from the curve
                curve = gate_opening_curve.dropna()
                # Ensure the curve is sorted by height (values)
                sorted_curve = curve.sort_values()
                heights = sorted_curve.values
                openings = sorted_curve.index

                # Interpolate: for each gate_height, find opening
                interpolated_opening = pd.Series(
                    np.interp(gate_height.values, heights, openings),
                    index=gate_height.index
                )
                river.gate_opening_schedule.set(interpolated_opening)

    def add_cuts(self, shop: ShopSession, week_cuts: Cuts):
        my_cuts = shop.model.cut_group.add_object("my_cuts")
            
        # This correction should be possible to do inside SHOP intead (since SHOP 14?), by setting cut coefficients on each inflow series.
        # Unsure if this is done correctly wrt. units etc., so keep the safe manual correction so far...
        # SHOP documentation says the inflow_series cut coefficients should have unit EUR/Mm3. 
        # ProdRisk documentation also says the inflowSeries cut coefficients should have unit EUR/Mm3, but the old simulator RHS correction use normalized inflows in the correction.
        # Sintef should check the ProdRisk core code, and update the documentations to clarify this!
        
        # Correcting cuts in simulator - should not be combined with cut-correction in SHOP
        rhs_correction_in_shop = False
        if not rhs_correction_in_shop:
            rhs = week_cuts.get_corrected_rhs(shop)
        rhs = week_cuts.rhs
        my_cuts.rhs.set(rhs)

        for mod_name, coeffs in week_cuts.module_coeffs.items():
            for rsv_name in self.settings["mapping"]["cut_module_to_rsv"][mod_name]:
                rsv = shop.model.reservoir[rsv_name]
                rsv.water_value_input.set(coeffs)
                rsv.connect_to(my_cuts)

        if rhs_correction_in_shop:
            # RHS correction in SHOP
            for series_name, coeffs in week_cuts.series_coeffs.items():
                inflow_series = shop.model.inflow_series[series_name]
                inflow_series.cut_coeffs.set(coeffs)
                inflow_series.connect_to(my_cuts)

        return


    def set_init_state(self, shop_session: ShopSession, scen: int, case_name: str = None, timestamp: pd.Timestamp = None):
        
        
        start_time = shop_session.get_time_resolution()['starttime']
        if timestamp:
            start_time = timestamp
        
        if self.settings[KEEP_RESULTS_IN_MEMORY]:
            self.set_init_state_from_memory(shop_session=shop_session, scen=scen, start_time=start_time)
        else: 
            self.set_init_state_from_h5(shop_session=shop_session, scen=scen, case_name=case_name, start_time=start_time)

    def set_init_state_from_memory(self, shop_session: ShopSession, scen: int, start_time= pd.Timestamp):
        """
        Set the initial state of each weekly SHOP optimization problem based on results kept in dict in memory.

        """
        for (obj_type, out_attr_name), in_attr_name in self.attributes_from_to.items():
            for obj_name in shop_session.model[obj_type].get_object_names():
                out_ts = self.shop_result_scenarios[f"scen_{scen}"][obj_type][obj_name][out_attr_name]             
                self.set_init_state_per_attribute(
                    shop_session=shop_session, 
                    start_time=start_time, 
                    out_attr_name=out_attr_name, 
                    out_ts=out_ts, 
                    obj_type=obj_type, 
                    obj_name=obj_name, 
                    in_attr_name=in_attr_name
                )

    def set_init_state_from_h5(self, shop_session: ShopSession, scen: int, case_name: str = None, start_time= pd.Timestamp):
        """
        Set the initial state of each SHOP optimization problem based on results saved to h5-file.
        """
        with pd.HDFStore(os.path.join(self.settings['shop']['result_folder'], f'shop_{case_name}.h5'), 'r') as store:
            for (obj_type, out_attr_name), in_attr_name in self.attributes_from_to.items():
                for obj_name in shop_session.model[obj_type].get_object_names():
                    out_ts = store[f'scen_{scen}/{obj_type}/{obj_name}'][out_attr_name]             
                    self.set_init_state_per_attribute(
                        shop_session=shop_session, 
                        start_time=start_time, 
                        out_attr_name=out_attr_name, 
                        out_ts=out_ts, 
                        obj_type=obj_type, 
                        obj_name=obj_name, 
                        in_attr_name=in_attr_name
                    )
                    
    def set_init_state_per_attribute(
            self, 
            shop_session: ShopSession, 
            start_time: pd.Timestamp, 
            out_attr_name: str, 
            out_ts: pd.Series, 
            obj_type: str, 
            obj_name: str, 
            in_attr_name: str
        ):
        '''
        Set the initial state of a specific attribute of a specific object in SHOP, based on the output time series from the previous weekly optimization problem.
        Handles special cases for binary attributes and attributes with endpoint values.
        
        For tunnels and rivers, only set initial gate openings if the object has a gate opening curve defined.
        For rivers, the resulting gate height from the previous weeks problem is interpolated using the gate opening curve.

        :param shop_session: The SHOP session to set the initial state in.
        :param start_time: The start time of the current weekly optimization problem.
        :param out_attr_name: The name of the output attribute from the previous optimization problem.
        :param out_ts: The time series of the output attribute from the previous optimization problem.
        :param obj_type: The type of the object in SHOP (e.g., "reservoir").
        :param obj_name: The name of the object in SHOP (e.g., "reservoir_1").
        :param in_attr_name: The name of the input attribute to set in the current optimization problem.
        '''

        time_delta = 0 if out_attr_name in self.attrs_with_endpoint else 1
        if out_attr_name in ["sim_upflow", "sim_discharge"]:
            shop_session.model[obj_type][obj_name][in_attr_name].set(1 if out_ts[start_time - pd.Timedelta(hours=time_delta)] > 0 else 0)   
        elif obj_type == "tunnel" and out_attr_name == "gate_opening":
            # Only set initial tunnel gate opening if the tunnel has a gate opening curve
            tunnel = shop_session.model[obj_type][obj_name]
            if tunnel.gate_opening_curve.get() is not None:
                shop_session.model[obj_type][obj_name][in_attr_name].set(out_ts[start_time - pd.Timedelta(hours=time_delta)])
        elif obj_type == "river" and out_attr_name == "gate_height":
            # Only set initial river gate opening if the river has a gate opening curve
            river = shop_session.model[obj_type][obj_name]
            gate_opening_curve = river.gate_opening_curve.get()
            if gate_opening_curve is not None:
                gate_opening = np.interp(
                    out_ts[start_time - pd.Timedelta(hours=time_delta)], 
                    gate_opening_curve.values, 
                    gate_opening_curve.index
                )
                shop_session.model[obj_type][obj_name][in_attr_name].set(gate_opening)
        elif obj_type == "river" and in_attr_name == "past_upstream_flow":
            max_time_delay = get_max_time_delay(shop_session, river_name=obj_name)
            # Only set past_upstream_flow if there is a time delay. Assume time delay input does not change between SHOP weeks.
            if max_time_delay > 0.0:
                # past_upstream_flow is a txy attribute, so we need to set the whole series
                full_series = out_ts.loc[start_time - pd.Timedelta(hours=max_time_delay):start_time]
                shop_session.model[obj_type][obj_name][in_attr_name].set(full_series)
        else:
            shop_session.model[obj_type][obj_name][in_attr_name].set(out_ts[start_time - pd.Timedelta(hours=time_delta)])

    def set_sim_init_state(self, optimization_session: ShopSession, simulation_session: ShopSession):
        """
        Set the initial state of a weekly SHOP simulation problem, based on the initial state of the already
        solved weekly optimization problem.
        """
        init_state_attributes = [
            ("reservoir", "start_vol"),
            # ("reservoir", "start_head"),
            # ("generator", "initial_state"),
            # ("pump", "initial_state"),
            # ("tunnel", "initial_opening"),
            ("river", "past_upstream_flow"),
        ]

        for (obj_type, out_attr_name) in init_state_attributes:
            for obj_name in optimization_session.model[obj_type].get_object_names():
                if obj_type == "tunnel" and out_attr_name == "initial_opening":
                    if simulation_session.model[obj_type][obj_name].gate_opening_curve.get() is None:
                        continue  # No initial opening
                simulation_session.model[obj_type][obj_name][out_attr_name].set(optimization_session.model[obj_type][obj_name][out_attr_name].get())

# TODO: should work for start_time.month!=1 or 12 too
    def set_init_state_from_prodrisk_or_prev_scen(self, shop_io: ShopSession, scen: int, case_name: str, first_scen: bool = True):
        """
        Set the initial state of the first weekly SHOP optimization problem in a scenario.
        The initial state is set based on the results from the last weekly SHOP optimization problem in the previous scenario,
        except for the first scenario, where the initial state is set based on the long Prodrisk run.   
        
        TODO: past_upstream_flow should also be transferred from the previous scenario, but this is not implemented yet.

        :param shop_io: The SHOP session to set the initial state in.
        :param scen: The scenario number in the long Prodrisk run.
        :param case_name: The case name used for logging and file naming.
        :param first_scen: Bool, True if this is the first scenario in the long Prodrisk run.

        """
        #Calculate overlap time (start before regular start time)
        overlap_time = self.settings["shop_horizon_days"] - self.settings["shop_step_length"]

        #Use last timestep in prodrisk (minus any overlap) to get initial values from last scenario
        #This skips days 365 and 366 to have a 364 day loop in SHOP
        if not first_scen:
            time_stamp = self.long_prodrisk.end_time - overlap_time
            self.set_init_state(shop_io, scen-1, case_name, time_stamp)
            return

        time_res = shop_io.get_time_resolution()
        start_time = time_res["starttime"]

        #For first week in scenario 0, we must be careful if we have an overlap
        prodrisk_scen = scen
        #Use start time in scenario 0 if we have no overlap
        if start_time == self.long_prodrisk.start_time:
            time_stamp = start_time
        else:
            #If we have an overlap, roll back to the end of the last scenario in Prodrisk
            time_stamp = self.long_prodrisk.start_time + pd.Timedelta(weeks=52) - overlap_time
            prodrisk_scen = (scen - 1)%self.long_prodrisk.n_scenarios

        for mod_name, rsvs in self.settings['mapping']['cut_module_to_rsv'].items():

            mod = self.long_prodrisk.model.module[mod_name]

            # Get start volumes from result attribute 'scenario_start_volumes' if specified
            if self.settings[SET_STARTVOLS_FROM_PRODRISK_SCEN_STARTVOLS]:
                start_vol = mod.scenario_start_volumes.get()[scen]
            else:
                prodrisk_rsv_vol = mod.reservoirVolume.get()[prodrisk_scen]
                start_vol = prodrisk_rsv_vol[time_stamp]

            vol_head_prodrisk = mod.volHeadCurve.get()
            start_head = -1
            if vol_head_prodrisk is not None:
                start_head = np.interp(start_vol, vol_head_prodrisk.index, vol_head_prodrisk.values)

            try:
                rsvs_with_start_vol = self.settings['mapping']['init_with_start_vol']
            except KeyError:
                rsvs_with_start_vol = []

            for rsv_name in rsvs:
                rsv = shop_io.model.reservoir[rsv_name]
                if start_head < 0.0 or rsv_name in rsvs_with_start_vol:
                    shop_start_vol = np.maximum(0.0,start_vol)

                    #Distribute volume by equal percentage if multiple reservoirs is connected to the module (probably should use start_head instead)
                    if len(rsvs) > 1:
                        shop_start_vol = shop_start_vol * rsv.max_vol.get() / (mod.rsvMax.get() + 1e-10)

                    shop_start_vol = np.minimum(rsv.max_vol.get(),shop_start_vol)

                    rsv.start_vol.set(shop_start_vol)
                else:
                    #Make sure start head is within the reservoir bounds in SHOP
                    shop_start_head = np.minimum(rsv.vol_head.get().values[-1], start_head)
                    shop_start_head = np.maximum(rsv.lrl.get(), shop_start_head)

                    rsv.start_head.set(shop_start_head)

    def save_shop_results(self, shop: ShopSession, scen: int, case_name: str = None):
        '''
        Save results from weekly SHOP problem to h5-file and/or in memory dict.

        The settings 'save_results_to_h5' and 'keep_results_in_memory' control if results are saved to h5-file and/or in memory dict.
        As default, the results are saved to h5-file, while saving in memory is optional.

        The result attributes to save per object type is specified in the settings['shop_output_attributes'] dict.
        If this is not specified by the user, all output txy attributes are saved (consume much disk space and/or memory).
        '''
        if self.settings[SAVE_RESULTS_TO_H5]: 
            self.save_shop_results_to_h5(shop=shop, scen=scen, case_name=case_name)
        
        if self.settings[KEEP_RESULTS_IN_MEMORY]:
            self.save_shop_results_in_dict(shop=shop, scen=scen)

    def save_shop_results_to_h5(self, shop: ShopSession, scen: int, case_name: str = None):
        '''
        Save results from weekly SHOP problem to h5-file.

        The results are stored in a h5-file with a structure like:
        /scen_0/reservoir/R1
        /scen_0/reservoir/R2
        /scen_0/generator/G1
        /scen_1/reservoir/R1
        /scen_1/reservoir/R2
        ... 

        Each object has a dataframe with the selected result attributes as columns, and a time index.

        The result attributes to save per object type is specified in the settings['shop_output_attributes'] dict.
        ''' 
        with pd.HDFStore(os.path.join(self.settings['shop']['result_folder'], f'shop_{case_name}.h5')) as store:
            
            file_keys = store.keys()
            
            scen_time_res = self.shop_model.get_time_resolution()
            scen_start_time = scen_time_res["starttime"] + self.settings["shop_step_length"] - self.settings["shop_horizon_days"]
            scen_end_time = scen_time_res["endtime"]
            time_index = pd.date_range(scen_start_time, scen_end_time, freq=pd.Timedelta(hours=1))
            for obj_type, result_attrs in self.settings["shop_output_attributes"].items():
                for name in shop.model[obj_type].get_object_names():
                    result_attrs = {attr: shop.model[obj_type][name][attr].get() for attr in result_attrs}
                    result_attr_names = [attr_name for attr_name, value in result_attrs.items() if value is not None]
                    arr = [value for value in result_attrs.values() if value is not None]
                    
                    if len(arr) == 0:
                        continue
                    
                    res_df = pd.concat(arr, axis=1)
                    res_df.columns = result_attr_names
                    if not f'/scen_{scen}/{obj_type}/{name}' in file_keys:
                        df = pd.DataFrame(
                            index=time_index,
                            data=np.zeros((len(time_index), len(res_df.columns))),
                            columns=result_attr_names
                        )
                    else:
                        df = store[f'scen_{scen}/{obj_type}/{name}']
                    df.update(res_df)
                    store[f'scen_{scen}/{obj_type}/{name}'] = df

    def save_shop_results_in_dict(self, shop: ShopSession, scen: int):
        '''
        Save results from weekly SHOP problem in a dict in memory.

        The results are stored in a dict with a structure like:
        shop_result_scenarios = {
            'scen_0': {
                'reservoir': {
                    'R1': {
                        'storage': pd.DataFrame,
                    }
                },
                'generator': {
                    'G1': {
                        'production': pd.DataFrame,
                    }
                },
            },
            'scen_1': {
                'reservoir': {
                    'R1': {
                        'storage': pd.DataFrame,
                    }
                },
                'generator': {
                    'G1': {
                        'production': pd.DataFrame,
                    }
                },
            },
            ... 
        }

        The result attributes to save per object type is specified in the settings['shop_output_attributes'] dict.
        ''' 
            
        scen_time_res = self.shop_model.get_time_resolution()
        scen_start_time = scen_time_res["starttime"] + self.settings["shop_step_length"] - self.settings["shop_horizon_days"]
        scen_end_time = scen_time_res["endtime"]
        time_index = pd.date_range(scen_start_time, scen_end_time, freq=pd.Timedelta(hours=1))
        for obj_type, result_attrs in self.settings["shop_output_attributes"].items():
            if not obj_type in self.shop_result_scenarios[f"scen_{scen}"].keys():
                self.shop_result_scenarios[f"scen_{scen}"][obj_type] = {}
            for name in shop.model[obj_type].get_object_names():
                result_attrs = {attr: shop.model[obj_type][name][attr].get() for attr in result_attrs}
                result_attr_names = [attr_name for attr_name, value in result_attrs.items() if value is not None]
                arr = [value for value in result_attrs.values() if value is not None]
                
                if len(arr) == 0:
                        continue
                    
                res_df = pd.concat(arr, axis=1)
                res_df.columns = result_attr_names
                if not name in self.shop_result_scenarios[f"scen_{scen}"][obj_type].keys():
                    df = pd.DataFrame(
                        index=time_index,
                        data=np.zeros((len(time_index), len(res_df.columns))),
                        columns=result_attr_names
                    )
                else:
                    df = self.shop_result_scenarios[f"scen_{scen}"][obj_type][name]
                df.update(res_df)
                self.shop_result_scenarios[f"scen_{scen}"][obj_type][name] = df

    def add_scen_txys(self, shop_io: ShopSession, scen: int):
        time_resolution = shop_io.get_time_resolution()
        
        prev_scen_end_time = time_resolution["endtime"]
        prev_scen_start_time = prev_scen_end_time - self.settings["shop_horizon_days"]

        next_scen_start_time = time_resolution["starttime"]
        next_scen_end_time = next_scen_start_time + self.settings["shop_step_length"]

        for (prodrisk_type, prodrisk_name, prodrisk_attr), shop_attrs in self.txy_mapping.items():
            prodrisk_txy = self.long_prodrisk.model[prodrisk_type][prodrisk_name][prodrisk_attr]
            
            info = prodrisk_txy.info()

            prodrisk_txy = prodrisk_txy.get()

            # Select given scenario from the stochastic ProdRisk result
            if info["datatype"] == "txy_stochastic":
                # Add input data from previous and next scenarios, to allow shop_horizon_days != shop_step_length
                prev_scen_txy = prodrisk_txy[(scen-1) % self.long_prodrisk.n_scenarios]
                prev_scen_selection = prev_scen_txy.loc[prev_scen_start_time:prev_scen_end_time]
                prev_scen_update = pd.Series(index=[idx - pd.Timedelta(days=364) for idx in prev_scen_selection.index],
                                             data=prev_scen_selection.values)
                
                next_scen_txy = prodrisk_txy[(scen+1) % self.long_prodrisk.n_scenarios]
                next_scen_selection = next_scen_txy.loc[next_scen_start_time:next_scen_end_time]
                next_scen_update = pd.Series(index=[idx + pd.Timedelta(days=364) for idx in next_scen_selection.index],
                                             data=next_scen_selection.values)
                
                prodrisk_txy = prodrisk_txy[scen]
                prodrisk_txy = prodrisk_txy.reindex(pd.date_range(time_resolution["starttime"], time_resolution["endtime"], freq="h"))

                prodrisk_txy.update(prev_scen_update)
                prodrisk_txy.update(next_scen_update)
                prodrisk_txy = prodrisk_txy.dropna()
                if next_scen_start_time < prodrisk_txy.index[0]:
                    prodrisk_txy = pd.concat([pd.Series(index=[next_scen_start_time], data=[np.nan]), prodrisk_txy]).bfill()

            for ((shop_type, shop_name, shop_attr), factor) in shop_attrs:
                shop_io.model[shop_type][shop_name][shop_attr].set(factor*prodrisk_txy)

    def update_prodrisk_rsv_curves_from_shop(self):
        shop = self.shop_model
        prodrisk = self.long_prodrisk
        config = self.settings

        for pr_rsv, shop_rsvs in tqdm(config['mapping']['rsv_vol_head_from_shop'].items(), total=len(config['mapping']['rsv_vol_head_from_shop'].items()), desc="Updating ProdRisk rsv curves from SHOP"):
            if len(shop_rsvs) == 1:
                prodrisk.model.module[pr_rsv].volHeadCurve.set(shop.model.reservoir[shop_rsvs[0]].vol_head.get())
            else:
                # Find all head values where one or several curves are given
                vol_head_curves = [shop.model.reservoir[shop_rsv].vol_head.get() for shop_rsv in shop_rsvs]
                head_arr = vol_head_curves[0].values
                for vol_head in vol_head_curves[1:]:
                    head_arr = np.concatenate((head_arr, np.setdiff1d(vol_head.values, head_arr)))
                head_arr.sort()
                vol_arr = None
                for vol_head in vol_head_curves:
                    vols = np.interp(head_arr, vol_head.values, vol_head.index)
                    vols[vols < 0] = 0.0
                    if vol_arr is None:
                        vol_arr = vols
                    else:
                        vol_arr = vol_arr + vols
                prodrisk.model.module[pr_rsv].volHeadCurve.set(pd.Series(index=vol_arr, data=head_arr, name=0.0))

            max_vol = sum([shop.model.reservoir[shop_rsv].max_vol.get() for shop_rsv in shop_rsvs])
            prodrisk.model.module[pr_rsv].rsvMax.set(max_vol)

    def update_prodrisk_q_max_from_shop(self):
        shop = self.shop_model
        prodrisk = self.long_prodrisk
        config = self.settings

        for (mod, plant) in config['mapping']['mod_to_plant'].items():
            if plant == "":
                continue
            
            plant_max = self.get_plant_qmax(plant)

            hyd_copl = self.long_prodrisk.model.module[mod].hydraulicType.get()

            if hyd_copl[0] > 0:
                mod_max = self.get_hyd_copl_qmax(mod)
            else:
                mod_max = self.long_prodrisk.model.module[mod].maxDischargeConst.get()
                if mod_max > plant_max:
                    self.long_prodrisk.model.module[mod].maxDischargeConst.set(plant_max)
    
    def update_pq_curves_from_shop(self):
        prodrisk = self.long_prodrisk
        config = self.settings

        shop_dict_orig =  yaml.load(self.shop_model.dump_yaml(), Loader=yaml.FullLoader)
        starttime = datetime.datetime(2022, 1, 1)
        shop_dict_orig['time']['starttime'] = starttime
        shop_dict_orig['time']['endtime'] = starttime + datetime.timedelta(minutes=50)
        shop_dict_orig['time']['timeunit'] = 'minute'
        shop_dict_orig['time']['timeresolution'] = {starttime: 1}

        if 'generator' in shop_dict_orig['model']:
            for _, gen in shop_dict_orig['model']['generator'].items():
                gen['startcost'] = {
                    starttime: 0
                }
                gen['stopcost'] = {
                    starttime: 0
                }
        if 'pump' in shop_dict_orig['model']:
            for _, pump in shop_dict_orig['model']['pump'].items():
                pump['startcost'] = {
                    starttime: 0
                }
                pump['stopcost'] = {
                    starttime: 0
                }
        if 'river' in shop_dict_orig['model']:
            for _, river in shop_dict_orig['model']['river'].items():
                river.pop('delta_head_ref_up_flow_curve', None)
                river.pop('delta_head_ref_down_flow_curve', None)
                river.pop('up_head_flow_curve', None)
                river['flow_schedule'] = {
                    starttime: 0
                }
        if 'gate' in shop_dict_orig['model']:
            for _, gate in shop_dict_orig['model']['gate'].items():
                gate.pop('min_flow', None)
        for _, rsv in shop_dict_orig['model']['reservoir'].items():
            rsv['inflow'] = {
                starttime: 0
            }
            rsv['energy_value_input'] = 150

        for (_, market) in shop_dict_orig['model']['market'].items():
            market['buy_price'] = {
                starttime: 100,
            }
            market['sale_price'] = {
                starttime: 99.99,
            }

        n_modules=len(config['mapping']['mod_to_plant'])
        if 'PQ_mapping' in config['mapping']:
            for mod, attr in tqdm(config['mapping']['PQ_mapping'].items(), total=n_modules, desc="Updating ProdRisk pq curves from SHOP"):
                plant_names = attr['plant']
                shop_dict = copy.deepcopy(shop_dict_orig)
                bypass_names = config['mapping']['module_bypass_to_gate'][mod]
                up_head = attr['up_head']
                up_rsvs = attr['up_rsv']
                if not isinstance(up_rsvs, list):
                    up_rsvs = [up_rsvs]
                for up_rsv in up_rsvs:
                    shop_dict['model']['reservoir'][up_rsv].pop('start_vol', None)
                    shop_dict['model']['reservoir'][up_rsv]['start_head'] = up_head

                shop_dict['model']['discharge_group'] = {
                    f'DG_{mod}': {}
                }
                if isinstance(plant_names, str):
                    plant_names = [plant_names]
                for plant_name in plant_names:
                    shop_dict['connections'].append({
                        'from': f'DG_{mod}',
                        'from_type': 'discharge_group',
                        'to': plant_name,
                        'to_type': 'plant'
                    })
                for bypass_name in bypass_names:
                    shop_dict['connections'].append({
                        'from': f'DG_{mod}',
                        'from_type': 'discharge_group',
                        'to': bypass_name,
                        'to_type': 'gate'
                    })
                down_head = attr['down_head']
                #down_rsvs=None
                if 'down_rsv' in attr:
                    down_rsvs = attr['down_rsv']
                    if not isinstance(down_rsvs, list):
                        down_rsvs = [down_rsvs]
                    for down_rsv in down_rsvs:
                        shop_dict['model']['reservoir'][down_rsv].pop('start_vol', None)
                        shop_dict['model']['reservoir'][down_rsv]['start_head'] = down_head
                nominal_head = up_head - down_head

                temp_shop = ShopSession()
                yaml.Dumper.ignore_aliases = lambda *args : True
                temp_shop.load_yaml(yaml_string=yaml.dump(shop_dict, Dumper=yaml.Dumper))

                #set discharge array
                if 'q_arr' in attr.keys():
                    q_arr = attr['q_arr'] #set discharge array from input if given. 
                else: #if input not given: find q array from the generators turb_eff_curves
                    for plant_name in plant_names:
                        gen_list=temp_shop.model.plant[plant_name].generators
                        if len(gen_list)==1: #if only one generator, set q_arr from its turb eff curve
                            gen=gen_list[0]
                            q_arr=gen.turb_eff_curves.get()[0].index
                        else: # if more than one generator: find maximum total discharge and make a two point array
                            q_max=0
                            for gen in gen_list:
                                q_max+=gen.turb_eff_curves.get()[0].index[-1]
                            q_arr=[0, q_max]

                    
                t_arr = [starttime + datetime.timedelta(minutes=i) for i in range(len(q_arr))]
                temp_shop.model.discharge_group[f'DG_{mod}'].min_discharge_m3s.set(pd.Series(q_arr, t_arr)) # | {t_arr[-1] + datetime.timedelta(minutes=1): np.nan}

                temp_shop.print_model([], ['mymodel.lp'])
                temp_shop.start_sim([], [1])

                for i in range(3):
                    for rsv in up_rsvs + down_rsvs:
                        temp_shop.model.reservoir[rsv].inflow.set(0)
                    for plant_name in plant_names:
                        discharge = temp_shop.model.plant[plant_name].discharge.get()
                        for related in temp_shop.model.plant[plant_name].get_relations():
                            if related.get_name() in up_rsvs:
                                related.inflow.set(related.inflow.get() + discharge)
                            if related.get_name() in down_rsvs:
                                related.inflow.set(related.inflow.get() - discharge)
                    for bypass_name in bypass_names:
                        discharge = temp_shop.model.gate[bypass_name].discharge.get()
                        for related in temp_shop.model.gate[bypass_name].get_relations():
                            if related.get_name() in up_rsvs:
                                related.inflow.set(related.inflow.get() + discharge)
                            if related.get_name() in down_rsvs:
                                related.inflow.set(related.inflow.get() - discharge)
                    temp_shop.start_sim([], [1])
                Q = sum([temp_shop.model.plant[plant_name].discharge.get().values.round(6) for plant_name in plant_names])
                P = sum([temp_shop.model.plant[plant_name].production.get().values.round(6) for plant_name in plant_names])
                _, idx = np.unique(Q, return_index=True)
                Q = Q[idx]
                P = P[idx]
                while Q[0] == 0:
                    Q = Q[1:]
                    P = P[1:]
                
                idx = np.diff(P) > 0
                idx = np.insert(idx, 0, True)
                Q = Q[idx]
                P = P[idx]

                points = np.column_stack((Q,P))
                if len(points) > 2:
                    hull = ConvexHull(points)
                    idx = np.sort(np.unique(hull.simplices.flatten()))
                    Q = Q[idx]
                    P = P[idx]

                # Set updated PQ-kurve on prodrisk modell
                #print(f'Old PQ-curves {mod}\n')
                #print(prodrisk.model.module[mod].PQcurve.get())
                prodrisk.model.module[mod].PQcurve.set(pd.Series(
                    name=nominal_head, index=P, data=Q
                ))
                prodrisk.model.module[mod].maxDischarge.set(pd.Series(index=[starttime], data=[Q[-1]]))
                prodrisk.model.module[mod].maxDischargeConst.set(Q[-1])
                prodrisk.model.module[mod].nominalHead.set(nominal_head)            
                #print(f'New PQ-curves {mod}\n')
                #print(prodrisk.model.module[mod].PQcurve.get())

        if 'pump_mapping' in config['mapping']:
            for (pump, attr) in config['mapping']['pump_mapping'].items():
                plant_names = attr['plant']
                if isinstance(plant_names, str):
                    plant_names = [plant_names]
                PQ = {}
                # Find PQ-kurve for two different heads to estimate pump parameters
                for up_head in attr['up_heads']:
                    shop_dict = copy.deepcopy(shop_dict_orig)
                    bypass_names = config['mapping']['module_bypass_to_gate'][mod]
                    # up_head = attr['up_head']
                    up_rsvs = attr['up_rsv']
                    if not isinstance(up_rsvs, list):
                        up_rsvs = [up_rsvs]
                    for up_rsv in up_rsvs:
                        shop_dict['model']['reservoir'][up_rsv].pop('start_vol', None)
                        shop_dict['model']['reservoir'][up_rsv]['start_head'] = up_head

                    down_head = attr['down_head']
                    if 'down_rsv' in attr:
                        down_rsvs = attr['down_rsv']
                        if not isinstance(down_rsvs, list):
                            down_rsvs = [down_rsvs]
                        for down_rsv in down_rsvs:
                            shop_dict['model']['reservoir'][down_rsv].pop('start_vol', None)
                            shop_dict['model']['reservoir'][down_rsv]['start_head'] = down_head
                    nominal_head = up_head - down_head

                    n_pump_pts = 140
                    t_arr = [starttime + datetime.timedelta(minutes=i) for i in range(n_pump_pts)]
                    shop_dict['time']['endtime'] = starttime + datetime.timedelta(minutes=n_pump_pts)
                    
                    for (_, market) in shop_dict['model']['market'].items():
                        market['buy_price'] = {t: 150 - 0.5 * i for (i, t) in enumerate(t_arr)}
                        market['sale_price'] = {t: 149.99 - 0.5 * i for (i, t) in enumerate(t_arr)}

                    temp_shop = ShopSession()
                    yaml.Dumper.ignore_aliases = lambda *args : True
                    temp_shop.load_yaml(yaml_string=yaml.dump(shop_dict, Dumper=yaml.Dumper))
                    temp_shop.start_sim([], [1])
                    
                    for i in range(3):
                        for rsv in up_rsvs + down_rsvs:
                            temp_shop.model.reservoir[rsv].inflow.set(0)
                        for plant_name in plant_names:
                            upflow = temp_shop.model.plant[plant_name].upflow.get()
                            for related in temp_shop.model.plant[plant_name].get_relations():
                                if related.get_name() in up_rsvs:
                                    related.inflow.set(related.inflow.get() - upflow)
                                if related.get_name() in down_rsvs:
                                    related.inflow.set(related.inflow.get() + upflow)
                        for bypass_name in bypass_names:
                            discharge = temp_shop.model.gate[bypass_name].discharge.get()
                            for related in temp_shop.model.gate[bypass_name].get_relations():
                                if related.get_name() in up_rsvs:
                                    related.inflow.set(related.inflow.get() + discharge)
                                if related.get_name() in down_rsvs:
                                    related.inflow.set(related.inflow.get() - discharge)
                        temp_shop.start_sim([], [1])
                    Q = sum([temp_shop.model.plant[plant_name].upflow.get().values.round(6) for plant_name in plant_names])
                    P = sum([temp_shop.model.plant[plant_name].consumption.get().values.round(6) for plant_name in plant_names])
                    _, idx = np.unique(Q, return_index=True)
                    Q = Q[idx]
                    P = P[idx]
                    while Q[0] == 0:
                        Q = Q[1:]
                        P = P[1:]
                    PQ[nominal_head] = {
                        'p': list(P),
                        'q': list(Q)
                    }
                h_arr = list(PQ.keys())
                h_max = max(h_arr)
                h_min = min(h_arr)
                max_h_upflow = PQ[h_max]['q'][-1]
                min_h_upflow = PQ[h_min]['q'][-1]
                if attr['n_seg'] == 1:
                    p_avg = 0.5 * (PQ[h_max]['p'][-1] + PQ[h_min]['p'][-1])
                    add_simple_pump(prodrisk, pump, p_avg, attr['topology'], max_h_upflow, min_h_upflow, h_max, h_min)
                else:
                    max_h_upflows, min_h_upflows, average_powers = get_pump_values(PQ, max_h_upflow, min_h_upflow, attr['n_seg'])
                    add_variable_pump(prodrisk, pump, h_max, h_min, attr['topology'], average_powers, max_h_upflows, min_h_upflows)

    def update_min_q_from_shop(self):
        config = self.settings
        for mod, gates in config['mapping']['module_bypass_to_gate'].items():
            min_flow = sum([self.shop_model.model.gate[gate_name].min_flow.get() for gate_name in gates if self.shop_model.model.gate[gate_name].min_flow.get() is not None])
            if not isinstance(min_flow, pd.Series):
                min_flow = pd.Series(index=[self.shop_model.get_time_resolution()['starttime']], data=[min_flow])
            # Repeat min q schedule yearly for ProdRisk
            min_flow = pd.concat([pd.Series(index=min_flow.index + pd.Timedelta(days=365*y), data=min_flow.values) for y in np.arange(np.ceil(self.long_prodrisk._n_weeks/52))])
            self.long_prodrisk.model.module[mod].minBypass.set(min_flow)

    def run_input_consistency_check(self):
        if "cut_module_to_rsv" in self.settings["mapping"].keys():
            # Reservoir tests
            self.check_rsv_max()
            self.check_vol_head()
        else:
            print("WARNING: Unable to compare ProdRisk and SHOP reservoir data due to missing mapping table 'cut_module_to_rsv' on the config file.")

        if "mod_to_plant" in self.settings["mapping"].keys():
            # Plant tests
            self.check_q_max()
            self.check_outlet_line()
        else:
            print("WARNING: Unable to compare ProdRisk and SHOP plant data due to missing mapping table 'mod_to_plant' on the config file.")
        
        # Time series input logging (comparisons are not relevant)
        self.check_time_series()
        #self.check_shop_time_series()
        print("\n")



    def check_time_series(self, check_object_types = ["module"]) -> None:
        print("\n\n ########## Check time series inputs ##########\n")
        print(" ########## Prints all time series constraints in ProdRisk ##########")
        print(" ########## Writes out different between ProdRisk and SHOP input if a mapping table is specified on the config file ##########")

        time_res = self.shop_model.get_time_resolution()

        compare_time_series = True
        if "compare_txy_attributes" not in self.settings["mapping"].keys():
            print("WARNING! No time series mapping table specified, so unable to compare time series input!")
            compare_time_series = False

        for object_type in check_object_types:
            # Iterate over all attributes of each object type
            object_attributes = self.long_prodrisk._pb_api.GetObjectTypeAttributeNames(object_type)
            for attribute_name in object_attributes:
                # Get license
                license_name = self.long_prodrisk._pb_api.GetAttributeInfo(object_type, attribute_name, 'license_name')
                if "INTERNAL" in license_name:
                    continue
                
                compare_object_type_time_series = (compare_time_series and 
                                                   object_type in self.settings["mapping"]["compare_txy_attributes"].keys())

                # Gather table data from prodrisk
                data_type = self.long_prodrisk._pb_api.GetAttributeInfo(object_type, attribute_name, 'datatype')

                # No other time dependent data than price and inflow is currently mapped from ProdRisk to SHOP...
                if data_type not in ["txy", "txy_stochastic"]:
                    continue

                # Some ProdRisk attributes are not relevant in SHOP: refVol, energyEquivalent, others?
                if attribute_name in ["inflowScenarios", "price", "refVol", "energyEquivalent"]:
                    continue

                for obj_name in self.long_prodrisk.model[object_type].get_object_names():
                    prodrisk_txy = self.long_prodrisk.model[object_type][obj_name][attribute_name].get()

                    compare_attr_time_series = (compare_object_type_time_series and 
                                                obj_name in self.settings["mapping"]["compare_txy_attributes"][object_type].keys() and
                                                attribute_name in self.settings["mapping"]["compare_txy_attributes"][object_type][obj_name].keys())

                    if prodrisk_txy is not None:
                        print(f"Attribute {attribute_name} is set for {object_type} {obj_name}.")
                        prodrisk_txy = prodrisk_txy[time_res["starttime"]:time_res["endtime"]]
                        shop_txy = 0*prodrisk_txy
                        if compare_attr_time_series:
                            found_shop_input = False
                            for (shop_type, shop_name, shop_attr) in self.settings["mapping"]["compare_txy_attributes"][object_type][obj_name][attribute_name]:
                                shop_txy_component = self.shop_model.model[shop_type][shop_name][shop_attr].get()
                                if shop_txy_component is not None:
                                    found_shop_input = True
                                    shop_txy = shop_txy + shop_txy_component.reindex(prodrisk_txy.index)
                            if not found_shop_input:
                                print(f"WARNING! 'compare_txy_attributes' mapping data set for {object_type}, {obj_name}, {attribute_name}, but none of the corresponding SHOP attributes where set!")
                            elif max(abs((shop_txy-prodrisk_txy))) > 1.e-3:
                                print(f"WARNING! The SHOP input data differs from the series set on {object_type}, {obj_name}, {attribute_name}")    



    def check_shop_time_series(self) -> None:
        print("\n\n ########## Check SHOP time series input ##########\n")
        print("########## Time dependent SHOP constraints should be set with care. ##########")
        print("########## Are they valid for all weeks and scenarios in the simulation? ##########\n")

        shop_object_names = self.shop_model.shop_api.GetObjectTypeNames()
        for object_name in shop_object_names:
            # Iterate over all attributes of each object type
            object_attributes = self.shop_model.shop_api.GetObjectTypeAttributeNames(object_name)
            for attribute in object_attributes:
                # Get license
                license_name = self.shop_model.shop_api.GetAttributeInfo(object_name, attribute, 'licenseName')
                if "INTERNAL" in license_name:
                    continue

                # Gather table data from shop
                object_type = object_name
                attribute_name = attribute
                data_type = self.shop_model.shop_api.GetAttributeInfo(object_name, attribute, 'datatype')

                if data_type in ["txy"] and attribute_name not in ["inflow", "price"]:

                    for obj_name in self.shop_model.model[object_type].get_object_names():
                        if self.shop_model.model[object_type][obj_name][attribute_name].get() is not None:
                            print(f"Attribute {attribute_name} is set for {object_type} {obj_name}.")
                            txy = self.shop_model.model[object_type][obj_name][attribute_name].get()
                            print(f"First 10 values: {[txy.values[i] for i in range(10)]}\n")

    def check_rsv_max(self) -> None:
        print("\n\n ##########  Check reservoir capacities ########## \n")
        for mod, rsvs in self.settings["mapping"]["cut_module_to_rsv"].items():
            mod_max = self.long_prodrisk.model.module[mod].rsvMax.get()
            rsvs_max = 0.0
            for rsv in rsvs:
                rsvs_max += self.shop_model.model.reservoir[rsv].max_vol.get()

            if abs(mod_max-rsvs_max) > 1.e-4:
                print(f"Difference in max_vol for module {mod}. ProdRisk: {mod_max}, SHOP: {rsvs_max}")

    def check_vol_head(self) -> None:
        print("\n\n ########## Check reservoir vol head curves ##########\n")
        for mod, rsvs in self.settings["mapping"]["cut_module_to_rsv"].items():
            print(f"\nModule: {mod}")
            mod_vol_head = self.long_prodrisk.model.module[mod].volHeadCurve.get()

            if self.long_prodrisk.model.module[mod].rsvMax.get() < 1.e-5:
                print(f"Skip comparing vol head curves, as rsvMax is < 1e-5")
                continue

            if mod_vol_head is None:
                print(f"Missing volHeadCurve for module {mod} in ProdRisk.")
                continue

            for vol, head in zip(mod_vol_head.index, mod_vol_head.values):
                shop_vol = 0.0
                for rsv in rsvs:
                    rsv_vol_head = self.shop_model.model.reservoir[rsv].vol_head.get()
                    if head > max(rsv_vol_head.values) or head < min(rsv_vol_head.values):
                        print(f"ProdRisk head: {head} for module {mod} not in vol head "
                            f"curve for the SHOP reservoir {rsv}."
                            f"lrl: {self.shop_model.model.reservoir[rsv].lrl.get()}, "
                            f"hrl: {self.shop_model.model.reservoir[rsv].hrl.get()}")
                        continue

                    shop_vol += np.interp(head, rsv_vol_head.values, rsv_vol_head.index)

                if abs(vol - shop_vol) > 1e-6:
                    print(f"Difference in vol_head curves for module {mod} at head {head}. ProdRisk: {vol}, SHOP: {shop_vol}")

    def get_coupled_modules(self, gathering_mod) -> list:
        gath_mod_nr = self.long_prodrisk.model.module[gathering_mod].number.get()
        coupled_modules = []
        for mod in self.long_prodrisk.model.module.get_object_names():
            topo = self.long_prodrisk.model.module[mod].topology.get()
            if topo[0] == gath_mod_nr:
                coupled_modules.append(mod)
        return coupled_modules

    def get_hyd_copl_qmax(self, mod) -> float:
        coupled_modules = self.get_coupled_modules(mod)
        qmax = 0.0
        if len(coupled_modules) > 2:
            print(f"Warning: More than 2 modules discharge to {mod}. Are all these hydraulic coupled? {coupled_modules}.")
        for coupled_mod in coupled_modules:
            qmax = max(qmax, self.long_prodrisk.model.module[coupled_mod].maxDischargeConst.get())
        return qmax


    def check_q_max(self):
        print("\n\n ########## Check plant discharge capacities ########## \n")
        for mod, plant in self.settings["mapping"]["mod_to_plant"].items():
            if plant == "":
                continue

            hyd_copl = self.long_prodrisk.model.module[mod].hydraulicType.get()

            if hyd_copl[0] > 0:
                mod_max = self.get_hyd_copl_qmax(mod)
            else:
                mod_max = self.long_prodrisk.model.module[mod].maxDischargeConst.get()

            plant_max = self.get_plant_qmax(plant)

            if abs(mod_max-plant_max) > 1.e-6:
                print(f"Difference in qmax for plant {plant}. ProdRisk: {mod_max}, SHOP: {plant_max}")

    def check_outlet_line(self):
        print("\n\n ########## Check plant outlet lines ##########\n")
        for mod, plant in self.settings["mapping"]["mod_to_plant"].items():
            plants = plant
            if isinstance(plants, str):
                plants = [plants]
            for plant in plants:
                if plant in self.shop_model.model.plant.get_object_names():
                    hyd_copl = self.long_prodrisk.model.module[mod].hydraulicType.get()

                    if hyd_copl[0] > 0:
                        mod_outlet = self.get_hyd_copl_outlet_line(mod)
                    else:
                        mod_outlet = self.long_prodrisk.model.module[mod].submersion.get()

                    plant_outlet = self.shop_model.model.plant[plant].outlet_line.get()

                    if abs(mod_outlet - plant_outlet) > 1.e-3:
                        print(f"Difference in outlet lines for plant {plant}. ProdRisk: {mod_outlet}, SHOP: {plant_outlet}")

    def get_hyd_copl_outlet_line(self, mod) -> float:
        coupled_modules = self.get_coupled_modules(mod)
        outlet_lines = []
        if len(coupled_modules) > 2:
            print(f"Warning: More than 2 modules discharge to {mod}. Are all these hydraulic coupled? {coupled_modules}.")
        for coupled_mod in coupled_modules:
            outlet_lines.append(self.long_prodrisk.model.module[coupled_mod].submersion.get())

        if outlet_lines[0] != outlet_lines[1]:
            print(f"Outlet lines different for two hydraulic coupled modules: "
                f"{coupled_modules[0]} and {coupled_modules[1]}. First value is used.")
        return outlet_lines[0]

    def get_plant_qmax(self, plant) -> float:
        qmax = 0.0
        plants = plant
        if isinstance(plants, str):
            plants = [plants]
        for plant in plants:
            if plant in self.shop_model.model.plant.get_object_names():
                for gen in self.shop_model.model.plant[plant].generators:
                    gen_qmax = 0.0
                    for curve in gen.turb_eff_curves.get():
                        gen_qmax = max(gen_qmax, max(curve.index))
                    qmax += gen_qmax

        return qmax
