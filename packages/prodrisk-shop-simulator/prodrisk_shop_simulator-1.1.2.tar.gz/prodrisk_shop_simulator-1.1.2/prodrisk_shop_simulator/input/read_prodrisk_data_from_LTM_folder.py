import math
import os
import sys
import h5py
import numpy as np
import itertools
import pandas as pd
import shutil
#from wrapper import Objects as OBJ
#from wrapper import GetSetFunctions as IO

from pyprodrisk import ProdriskSession


# The functions below are used to load input from a v10 EOPS folder into a ProdriskSession
# The following input is read:
# Module data from model.h5
# Price forecast from PRISREKKE.PRI
# Inflow scenarios from ScenarioData.h5
# Settings from PRODRISK.CPAR (note: some settings are re-set by python code.
# Time dependent module restrictions from DYNMODELL.SIMT:
### max/min for reservoir, discharge and bypass, reference volume and energy equivalents.
# Water values from VVERD_000.EOPS

class InputObject(object):

	def __init__(self, static_model, initial_state, txys, stxys):

		self.static_model = static_model
		self.txys = txys
		self.stxys = stxys
		self.start_week = 1
		self.start_scen = 0

		self.initial_state = initial_state

def build_prodrisk_model(LTM_input_folder, n_weeks=156, start_time="2030-01-07", n_price_levels=7,license_path='',solver_path='', ignore_objects=None, price_file="PRISREKKE.PRI"):
    ScenF = h5py.File(os.path.join(LTM_input_folder,'ScenarioData.h5'), 'r')
    names = list(ScenF.keys())
    model_name = names[0]
    ScenF.close()
    # INITIALIZE PRODRISK API #
    prodrisk = ProdriskSession(license_path=license_path, silent=True, log_file='api_log.py', solver_path=solver_path)
    prodrisk.set_optimization_period(pd.Timestamp(start_time), n_weeks=n_weeks)
    #prodrisk.keep_working_directory = True   # Keep temp run-folder for debugging purposes.
                                              # Overstyres av settings!

    #prodrisk.prodrisk_path = r"C:\Prodrisk\core"
    #prodrisk.temp_dir = r"C:\Prodrisk\pyprodrisk\temp"

    get_n_scen(prodrisk, LTM_input_folder, model_name)


    # BUILD MODEL#
    prodrisk.is_series_simulation = True

    prodrisk.price_periods.set(pd.Series(data=get_price_periods(LTM_input_folder), index=[prodrisk.start_time + pd.Timedelta(hours=i) for i in range(168)]))

    # prodrisk.use_coin_osi = False
    # prodrisk.n_scenarios = 58
    #
    # prodrisk.n_price_levels = 7  # number of levels in discrete price model (include max and min)
    # prodrisk.n_processes = 7  # number of mpi processes
    #
    #set_price_periods(prodrisk, res="3H")
    #
    # prodrisk.deficit_power_cost = 200.0
    # prodrisk.surplus_power_cost = 0.01

    # Assumes consistency in files model.h5 and ScenarioData.h5.
    ignore_modules = ignore_objects['module'] if ignore_objects and 'module' in ignore_objects else []
    ignore_pumps = ignore_objects['pump'] if ignore_objects and 'pump' in ignore_objects else []
    ignore_inflowSeries = ignore_objects['inflowSeries'] if ignore_objects and 'inflowSeries' in ignore_objects else []

    add_inflow_series(prodrisk, LTM_input_folder, model_name, ignore_inflowSeries)
    add_modules(prodrisk, LTM_input_folder, model_name, ignore_modules)
    add_pumps(prodrisk, LTM_input_folder, model_name, ignore_pumps)

    add_area_object(prodrisk, LTM_input_folder, n_price_levels, price_file)

    add_settings(prodrisk, LTM_input_folder)

    set_start_vols(prodrisk, LTM_input_folder, model_name, ignore_modules)

    add_module_restrictions(prodrisk, LTM_input_folder)

    return prodrisk


def set_price_periods(prodrisk, res="weekly"):
    # The time resolution is specified by the price period time series.
    # Currently only values for the first week (168 hours) are used.
    # For each week, the average of the hourly price values are used as the price for each period.

    if res == "weekly":
        prodrisk.price_periods = pd.Series(
            index=[prodrisk.start_time],
            data=np.arange(1, 2)
        )
    elif res == "3H":
        prodrisk.price_periods = pd.Series(
            index=[prodrisk.start_time + pd.Timedelta(hours=3 * i) for i in range(56)],
            data=np.arange(1, 57)
        )
    elif res == "6H":
        prodrisk.price_periods = pd.Series(
            index=[prodrisk.start_time + pd.Timedelta(hours=6 * i) for i in range(28)],
            data=np.arange(1, 29)
        )



def set_start_vols(prodrisk, LTM_input_folder, model_name, ignore_modules: list[str]=[]):

    start_vols = get_start_volumes(LTM_input_folder, model_name)
    for mod, vol in start_vols.items():
        if mod in ignore_modules:
            continue

        prodrisk.model.module[mod].startVol.set(vol)

    return True


def get_n_scen(prodrisk, data_dir, model_name):
    model_file = h5py.File(data_dir + "model.h5", 'r')

    param_path = 'hydro_data/hydro_parameters'

    params = model_file.get(param_path)

    prodrisk.n_scenarios = params['value'][3]

    return


def add_modules(prodrisk, data_dir, model_name, ignore_modules: list[str]=[]):
    model_file = h5py.File(data_dir + "model.h5", 'r')

    system_path = 'hydro_data/' + model_name.upper()

    PQcurves = {}
    energy_equivalents = {}
    pq = model_file.get(system_path + '/PQ_curve')
    for key in pq.keys():
        if "curve" in key:
            Q = np.array(pq[key]["M3s"])
            P = np.array(pq[key]["MW"])
            PQcurves[int(pq[key]["id"][0])] = [P, Q]
            # energy_equivalents[int(pq[key]["id"][0])] = float(pq[key]["local_conv_"][0])

    res_curves = {}
    res = model_file.get(system_path + '/res_curves')

    for key in res.keys():
        try:
            int(key)
        except ValueError:
            continue
        if ("Kote" in res[key]):
            res_curves[int(key)] = [np.array(res[key]["Vol"]), np.array(res[key]["Kote"])]

    module_data = model_file.get(system_path + '/Module_data')
    for i in range(module_data.size):
        mod_name = module_data[i]['res_name'].decode("iso-8859-1").strip()
        # Ignore module if in ignore list
        if mod_name in ignore_modules:
            continue

        # From Bernt: Our H5-files should be encoded with iso-8859-1
        mod = prodrisk.model.module.add_object(module_data[i]['res_name'].decode("iso-8859-1").strip())

        mod.name.set(module_data[i]['res_name'].decode("iso-8859-1").strip())
        mod.plantName.set(module_data[i]['plant_name'].decode("iso-8859-1").strip())
        mod.number.set(module_data[i]['res_id'])
        mod.ownerShare.set(1.0)
        mod.regulationType.set(module_data[i]['reg_res'])

        mod.rsvMax.set(module_data[i]['max_res'])
        mod.connectedSeriesId.set(prodrisk.model.inflowSeries[module_data[i]['r_infl_name'].decode("iso-8859-1").strip()].seriesId.get())
        mod.connected_unreg_series_id.set(prodrisk.model.inflowSeries[module_data[i]['u_infl_name'].decode("iso-8859-1").strip()].seriesId.get())
        mod.meanRegInflow.set(module_data[i]['r_infl_rvol'])
        mod.meanUnregInflow.set(module_data[i]['u_infl_rvol'])
        mod.nominalHead.set(module_data[i]['nom_elevation'])
        mod.submersion.set(module_data[i]["Undervannstand"])
        if(module_data[i]['res_id'] in res_curves.keys()):
            mod.volHeadCurve.set(pd.Series(name=0.0, index=res_curves[module_data[i]['res_id']][0], data=res_curves[module_data[i]['res_id']][1]))

        mod.reservoirMaxRestrictionType.set(module_data[i]['res_up_lim_type'])
        mod.reservoirMinRestrictionType.set(module_data[i]['res_low_lim_type'])
        mod.regulationDegree.set(module_data[i]["reg_level"])

        # Set refVol to improve convergence of first main iteration.
        # Default value for this attribute is 0% filling for all weeks, which gives a large gap between the converging F- and K-cost.

        if(module_data[i]['res_id'] in PQcurves.keys()):
            mod.PQcurve.set(pd.Series(name=module_data[i]['nom_elevation'], index=PQcurves[module_data[i]['res_id']][0], data=PQcurves[module_data[i]['res_id']][1]))

        mod.energyEquivalentConst.set(module_data[i]['conv_factor'])
        mod.maxDischargeConst.set(module_data[i]['max_flow'])
        mod.maxProd.set(module_data[i]['prod_cap'])
        mod.maxBypassConst.set(module_data[i]['max_bypass'])
        mod.topology.set([module_data[i]['flow_to'], module_data[i]['bypass_to'], module_data[i]['spill_to']])
        mod.hydraulicType.set([module_data[i]['copl_kode'], module_data[i]['copl_number'], module_data[i]['copl_cap']])

    # Get module time series for modules from dynmodell.SIMT
    #getdynmodellSeries(data_dir, modules) TODO!!
    #getStraffdotCPAR() TODO

    return True


def adjust_inflow(prodrisk, inflow, ADJUST_INFLOW):

    # Ukentlige skaleringsfaktorer fra siste klimaprosjektet Birger var med i.
    # Skaleringsfaktorene er laget for serie 592-A, som ble brukt for alle modulene i RSK i dette prosjektet.
    # Echam: Tysk. Hadam: Engelsk.

    if ADJUST_INFLOW == "ECHAM":
        echam = np.array(
            [1.35, 2.01, 2.52, 2.83, 2.72, 1.93, 1.67, 1.48, 1.41, 1.5, 1.83, 2.17, 2.13, 2.17, 2.02, 1.89, 2.19, 1.71,
             1.18, 1.05, 0.99, 1, 1.07, 1.07, 1.04, 1.01, 0.95, 0.92, 0.91, 0.91, 0.96, 0.99, 1, 1, 1.02, 1.17, 1.3,
             1.41, 1.43, 1.45, 1.6, 1.54, 1.67, 1.83, 1.5, 1.49, 1.47, 1.5, 1.11, 0.95, 0.89, 0.88])
        echam = np.repeat(echam, 7)

        echam = (1.07/1.23)*echam   # Faktorene gav +23 % økning i årlig tilsig på seriene i RSK-datasettet for denne analysen. Justerer ned til 7%.

        scaling_ts = pd.Series(data=echam, index=[prodrisk.start_time + pd.Timedelta(days=i) for i in range(echam.size)])
    elif ADJUST_INFLOW == "HADAM":
        hadam = np.array(
            [2.07, 2.22, 2.52, 2.75, 2.77, 2.65, 2.3, 2.32, 2.38, 1.79, 1.95, 2.09, 1.94, 2.1, 2.42, 2.73, 3.8, 3.12,
             2.22, 1.71, 1.38, 1.04, 0.9, 0.79, 0.69, 0.7, 0.58, 0.51, 0.5, 0.5, 0.57, 0.62, 0.65, 0.73, 0.78, 0.84,
             0.94, 1.07, 1.11, 1.11, 1.2, 1.21, 1.3, 1.71, 2.04, 2.42, 2.58, 3.05, 2.39, 2.23, 1.88, 2.08])
        hadam = np.repeat(hadam, 7)

        hadam = (1.07/1.23)*hadam   # Faktorene gav +23 % økning i årlig tilsig på seriene i RSK-datasettet for denne analysen. Justerer ned til 7%.

        scaling_ts = pd.Series(data=hadam, index=[prodrisk.start_time + pd.Timedelta(days=i) for i in range(hadam.size)])
    elif ADJUST_INFLOW == "ORIGINAL_7":
        # Bruker historikken uskalert, men legger på konstant 7% i klimakorreksjon på alle serier.
        original_scaling = (1.07/1.0)*np.ones(364)
        scaling_ts = pd.Series(data=original_scaling, index=[prodrisk.start_time + pd.Timedelta(days=i) for i in range(364)])

    for scen in inflow.columns:
        inflow[scen] = inflow[scen].multiply(scaling_ts)

    return inflow


def add_inflow_series(prodrisk, data_dir, model_name, ignore_inflowSeries: list[str]=[]):
    model_file = h5py.File(data_dir + "model.h5", 'r')
    watermarkdata = model_file.get('hydro_data/' + model_name.upper() + '/Watermark_data')

    counter = 1
    for i in range(watermarkdata.size):
        serie_name = watermarkdata['infl_name'][i].decode('utf-8')
        if serie_name in ignore_inflowSeries:
            continue
        inflow_serie = prodrisk.model.inflowSeries.add_object(serie_name)
        inflow_serie.seriesId.set(counter)
        inflow_serie.histAverageInflow.set(watermarkdata['average_inflow'][i])

        counter = counter+1


    for serie_name in prodrisk.model.inflowSeries.get_object_names():
        inflow_364d = get_yearly_inflow(prodrisk, data_dir, serie_name, model_name)

        inflow_scenarios = set_up_scenarios_from_yearly(prodrisk, inflow_364d)

        # fig = px.line(inflow_scenarios, labels={
        #     "index": "Date",
        #     "value": "Inflow [m3/s]",
        #     "variable": "Scenario"
        # })
        # fig.show()

        prodrisk.model.inflowSeries[serie_name].inflowScenarios.set(inflow_scenarios)

    return True


def set_up_scenarios_from_yearly(prodrisk, series):
    indices = pd.DatetimeIndex([])
    next_indices = series.index

    n_years = math.ceil(prodrisk.n_weeks/52)

    series_size = series.values.shape
    steps_in_year = series_size[0]
    n_scen = series_size[1]

    data = np.zeros((steps_in_year*n_years, n_scen))

    for year in range(n_years):
        indices = indices.append(next_indices)
        next_indices = next_indices + pd.offsets.DateOffset(days=364)


        data[year*steps_in_year:(year+1)*steps_in_year, 0:n_scen-year] = series.values[0:steps_in_year, year:n_scen]

        for y in range(year):
            data[year * steps_in_year:(year + 1) * steps_in_year, n_scen - year+y] = series.values[0:steps_in_year, y]

    
    # Slice dataframe to allow partial year simulation
    if prodrisk.n_weeks % 52 != 0:
        upper_bound_day_index = prodrisk.n_weeks * 7
        
        data = data[0:upper_bound_day_index, :]
        indices = indices[0:upper_bound_day_index]

    scenarios = pd.DataFrame(data=data, index=indices)

    return scenarios


def get_yearly_inflow(prodrisk, data_dir, serie_name, model_name):
    scenario_data_file = h5py.File(data_dir + "ScenarioData.h5", 'r')
    data = {}

    counter = 0
    for key in scenario_data_file.get(model_name.upper() + '/' + serie_name).keys():
        h5scenario = scenario_data_file.get(model_name.upper() + '/' + serie_name)[key]
        daily_index = [prodrisk.start_time + pd.Timedelta(days=i) for i in range(52 * 7)]

        data[f"scen{counter}"] = np.array(h5scenario)[0:52*7]
        counter += 1
        if counter == prodrisk.n_scenarios:
            break

    return pd.DataFrame(index=daily_index, data=data)


def add_area_object(prodrisk, LTM_input_folder, n_price_levels, price_file="PRISREKKE.PRI"):
    area = prodrisk.model.area.add_object("my_area")

    price_52w = get_yearly_price_ts(prodrisk, LTM_input_folder, price_file)

    price = set_up_scenarios_from_yearly(prodrisk, price_52w)

    # fig = px.line(price, labels={
    #     "index": "Date",
    #     "value": "Price [EUR/MWh]",
    #     "variable": "Scenario"
    # })
    # fig.show()

    area.price.set(price)
    prodrisk.n_price_levels = n_price_levels
    water_values = get_water_values(LTM_input_folder, prodrisk.n_weeks, n_price_levels)
    area.waterValue.set(water_values)

    return True


def get_yearly_price_ts(prodrisk, LTM_input_folder, price_file="PRISREKKE.PRI"):
    price_df = get_price_scenarios(prodrisk.start_time, LTM_input_folder, price_file, n_weeks=52, n_scen=prodrisk.n_scenarios)

    return price_df


def get_start_volumes(data_dir, model_name):
    start_volume_file_path = data_dir + model_name + ".SMAG"
    start_volumes = {}
    with open(start_volume_file_path, 'r') as volume_file:
        data = volume_file.readlines()
        dummy = data[0]
        for line in data[1:]:
            line = line.split(',')
            mod_name = line[0].replace("'", "").replace(" ", '').strip()
            start_volumes[mod_name] = float(line[1])
    return start_volumes

def get_price_scenarios(start_time, data_dir, price_file_name, n_weeks=-1, n_scen=-1):

    price_periods = get_sequential_price_periods(data_dir)
    start_hours = price_periods.keys()
    seq_periods = price_periods.values()

    price_input_file_path = data_dir + '/' + price_file_name
    price_scenarios = []
    with open(price_input_file_path, 'r') as price_file:
        all_data = price_file.readlines()
        separator = all_data[0][1]
        if n_weeks == -1:
            n_weeks = int(all_data[4].split(separator)[0])
        n_price_periods = int(all_data[6].split(separator)[0])
        all_price_data = all_data[8:]
        price_data = [line.split(separator) for line in all_price_data]
        for i in range(0, len(price_data), n_price_periods):
            scenario = []
            listcompr = [price_data[i+j][2:] for j in range(n_price_periods)]
            merged = []

            for liste in zip(*listcompr):
                ny_liste = []
                for elem in liste:
                    try:
                        ny_liste.append(float(elem.replace(all_data[0][2], ".")))
                    except ValueError:
                        continue
                merged.append(ny_liste)

            #merged = [[float(i.replace(all_data[0][2], ".")) for i in liste] for liste in zip(*listcompr)]
            for week in merged:
                
                # Skip empty week arrays
                if len(week) == 0:
                    continue
                
                seq_week = [week[i-1] for i in seq_periods]
                scenario.extend(seq_week)
            price_scenarios.append(scenario[0:n_weeks*len(seq_periods)])

    if n_scen == -1:
        n_scen = len(price_scenarios)

    price_df = pd.DataFrame(
        #index=[start_time + pd.Timedelta(hours=3 * i) for i in range(len(price_scenarios[0]))],
        index=[start_time + pd.Timedelta(hours=168*w + h) for w in range(n_weeks) for h in start_hours],
        data={
            f"scen{i}": price_scenarios[i] for i in range(n_scen)
        },
    )

    return price_df


def get_price_periods(data_dir):
    price_period_file_path = data_dir + '/PRISAVSNITT.DATA'
    price_periods = []
    with open(price_period_file_path, 'r') as price_period_file:
        all_data = price_period_file.readlines()
        n_price_levels = int(all_data[1].split(',')[0])
        price_periods_data = all_data[n_price_levels + 2:]
        for line in price_periods_data:
            line = list(map(int, line.split(',')[:-1]))
            price_periods.extend(line)

    return price_periods


def get_sequential_price_periods(data_dir):
    price_periods = get_price_periods(data_dir)

    start_hours = [0]
    seq_to_acc = [price_periods[0]]
    for h in range(1, 168):
        if price_periods[h] != price_periods[h-1] or h % 24 == 0:
            start_hours.append(h)
            seq_to_acc.append(price_periods[h])

    return dict(zip(start_hours, seq_to_acc))


# Read settings from PRODRISK.CPAR
def add_settings(prodrisk, data_dir):
    fileNameSettings = data_dir + "PRODRISK.CPAR"
    try:
        with open(fileNameSettings, 'r') as settings_file:
            all_data = settings_file.readlines()
    except FileNotFoundError:
        print("File 'PRODRISK.CPAR' not found, trying with lowercase 'prodrisk'...")

        fileNameSettings = data_dir + "prodrisk.CPAR"
        try:
            with open(fileNameSettings, 'r') as settings_file:
                all_data = settings_file.readlines()
        except FileNotFoundError:
            print("No prodrisk.CPAR file found")
            return

    data = [line.split(',')[0].split() for line in all_data]
    dataDict = {line[0]:line[1] for line in data}

    settingInfoDict = {
        "STAITER": ("max_iterations", int),
        "MINITER": ("min_iterations", int),
        "STAITER1": ("max_iterations_first_run", int),
        "MINITER1": ("min_iterations_first_run", int),
        "FKONV": ("convergence_criteria", float),
        "STOR": ("inf", float),
        "ALFASTOR": ("alfa_max", float),
        "CTANK": ("water_ration_cost", float),
        "CFORB_STYR": ("bypass_cost", float),
        "CFLOM_STYR": ("overflow_cost", float),
        "TOMMAX": ("max_relaxation_iterations", int),
        "HALDKUT": ("max_cuts_created", int),
        "STR_MAGBR": ("reservoir_soft_restriction_cost", float),
        "ANTBRU1": ("first_relaxation_parameter", int),
        "SLETTE_FREKV": ("second_relaxation_parameter", int),
        "SLETTE_TOL": ("relaxation_tolerance", float),
        "RESSTOY": ("residual_model", int),
        "JUKE_AGGR_PRAVSN": ("aggregated_price_period_start_week", int),
        "JSEKV_STARTUKE": ("sequential_price_period_start_week", int),
        "JSEKV_SLUTTUKE": ("sequential_price_period_end_week", int),
        "PQValg": ("use_input_pq_curve", int),
        "MagBal": ("reservoir_balance_option", int),
        "FramSomSluttsim": ("forward_model_option", int),
        "PrisScenStrategi": ("price_scenario_option", int)
    }

    for key, value in dataDict.items():
        try:
            getattr(prodrisk, settingInfoDict[key][0]).set(settingInfoDict[key][1](value))
        except KeyError:
            continue



# Read module restrictions from the binary file DYNMODELL.SIMT. To understand this, read the documentation for this file (AN Filstruktur_V10).
def add_module_restrictions(prodrisk, data_dir):
    dynmodell = read_dynmodell(data_dir)

    n_mod = dynmodell['Blokk1']['first6Ints'][2]
    n_weeks = dynmodell['Blokk1']['first6Ints'][4]

    if n_weeks < prodrisk.n_weeks:
        print(f"WARNING: Restrictions from DYNMODELL.SIMT read for {n_weeks} weeks. Simulation period is set to {prodrisk.n_weeks} weeks. Restrictions for the last {prodrisk.n_weeks - n_weeks} weeks of the simulation period may be set incorrectly?")

    module_indices = dynmodell['Blokk'+str(n_weeks+2)][0:n_mod]

    MAMAX = {mod: np.zeros(n_weeks) for mod in module_indices}
    MAMIN = {mod: np.zeros(n_weeks) for mod in module_indices}
    MAGREF = {mod: np.zeros(n_weeks) for mod in module_indices}
    ENEKV = {mod: np.zeros(n_weeks) for mod in module_indices}
    QMAX = {mod: np.zeros(n_weeks) for mod in module_indices}
    QMIN = {mod: np.zeros(n_weeks) for mod in module_indices}
    QFOMAX = {mod: np.zeros(n_weeks) for mod in module_indices}
    QFOMIN = {mod: np.zeros(n_weeks) for mod in module_indices}


    # First read out to python dicts, to ensure correct sorting is maintained
    for w in range(n_weeks):
        for i in range(n_mod):
            week_block = dynmodell['Blokk'+str(w+2)]
            mod = module_indices[i]
            MAMAX[mod][w] = week_block[i*8]
            MAMIN[mod][w] = week_block[i * 8+1]
            MAGREF[mod][w] = week_block[i*8+2]
            ENEKV[mod][w] = week_block[i*8+3]
            QMAX[mod][w] = week_block[i*8+4]
            QMIN[mod][w] = week_block[i*8+5]
            QFOMAX[mod][w] = week_block[i*8+6]
            QFOMIN[mod][w] = week_block[i*8+7]


    weekly_indices = [prodrisk.start_time + pd.Timedelta(weeks=w) for w in range(n_weeks)]

    # Add information to module objects
    for module_name in prodrisk.model.module.get_object_names():
        mod = prodrisk.model.module[module_name]
        mod_number = mod.number.get()
        if mod_number not in module_indices:
            continue

        if np.min(MAMAX[mod_number]) < mod.rsvMax.get():
            mod.maxVol.set(pd.Series(data=MAMAX[mod_number], index=weekly_indices))

        if np.max(MAMIN[mod_number]) > 0.0:
            mod.minVol.set(pd.Series(data=MAMIN[mod_number], index=weekly_indices))

        mod.refVol.set(pd.Series(data=MAGREF[mod_number], index=weekly_indices))

        if np.any(ENEKV[mod_number] != mod.energyEquivalentConst.get()):
            mod.energyEquivalent.set(pd.Series(data=ENEKV[mod_number], index=weekly_indices))

        if np.min(QMAX[mod_number]) < mod.maxDischargeConst.get():
            if np.min(QMAX[mod_number]) != np.max(QMAX[mod_number]):
                mod.maxDischarge.set(pd.Series(data=QMAX[mod_number], index=weekly_indices))
            else:
                mod.maxDischargeConst.set(QMAX[mod_number][0])

        if np.max(QMIN[mod_number]) > 0.0:
            mod.minDischarge.set(pd.Series(data=QMIN[mod_number], index=weekly_indices))

        if np.min(QFOMAX[mod_number]) < mod.maxBypassConst.get():
            if np.min(QFOMAX[mod_number]) != np.max(QFOMAX[mod_number]):
                mod.maxBypass.set(pd.Series(data=QFOMAX[mod_number], index=weekly_indices))
            else:
                mod.maxBypassConst.set(QFOMAX[mod_number][0])

        if np.max(QFOMIN[mod_number]) > 0.0:
            mod.minBypass.set(pd.Series(data=QFOMIN[mod_number], index=weekly_indices))


    return

# Currently not in use...
def get_hydro_parameters(data_dir):
    model_file = h5py.File(data_dir + "model.h5", 'r')
    hydroparametersdata = model_file.get('hydro_data/hydro_parameters')
    hydro_parameters = {}
    for i in range(hydroparametersdata.size):
        hydro_parameters[hydroparametersdata[i]['parameter'].decode("utf-8")] = hydroparametersdata[i]['value']
    return hydro_parameters

# Currently not in use...
def getNumModules(data_dir, model_name):
    fileNameModel = data_dir + "model.h5"
    model_file = h5py.File(fileNameModel, 'r')
    numModules = model_file.get('hydro_data/' + model_name + '/numb_of_modules')[0]
    return numModules


def add_pumps(prodrisk, data_dir, model_name, ignore_pumps: list[str]=[]):
    model_file = h5py.File(data_dir + "model.h5", 'r')

    pumps = []
    pump_data = model_file.get('hydro_data/' + model_name + '/Pumpe_data')
    if pump_data is not None:
        for i in range(pump_data.size):
            pump_name = pump_data[i]['name'].decode("utf-8")
            if pump_name in ignore_pumps: # Skip if pump is ignored
                continue
            pump = prodrisk.model.pump.add_object(pump_name)
            pump.ownerShare.set(1.0)
            pump.name.set(pump_name)
            pump.maxPumpHeight.set(1.0)
            pump.minPumpHeight.set(0.0)
            pump.maxHeightUpflow.set(pump_data[i]['Pumpekap_1']+pump_data[i]['Pumpekap_2'])
            pump.minHeightUpflow.set(pump_data[i]['Pumpekap_1'])
            pump.averagePower.set(pump_data[i]['Pumpekap_3'])
            pump.topology.set([pump_data[i]['con_to_pla'], pump_data[i]['to_res'], pump_data[i]['from_res']])

    return

# Reads binary file VVERD_000.EOPS. To understand this, read the documentation for this file (AN Filstruktur_V10?).
def get_water_values(data_dir, last_week, n_levels):
    fileName = data_dir + "VVERD_000.EOPS"

    with open(fileName, "rb") as f:
        header = np.fromfile(f, dtype=np.uint32, count=3)
        LBlokk = int(header[0])
        NTMag = header[1]
        NTPris = header[2]
        vals_in_block = int(LBlokk/4)

        file = np.fromfile(f, dtype=np.float32)

        last_week_pos = vals_in_block-3 + vals_in_block*last_week
        VV_lastweek = file[last_week_pos:last_week_pos+vals_in_block]

        f.close()

    refs = []
    x = []
    y = []

    for i in range(n_levels):
        refs.append(i)

        for n in range(51):
            x.append(np.real(100 - n * 2))

        vv_pris = VV_lastweek[NTMag * i : NTMag * (i + 1)]
        y.append(vv_pris[:])

    x_values = np.array(x).reshape((n_levels, 51))
    y_values = np.array(y).reshape((n_levels, 51))
    wv = [pd.Series(name=ref, index=x_val, data=y_val) for ref, x_val, y_val in zip(refs, x_values, y_values)]

    return wv

# Reads binary file DYNMODELL.SIMT. To understand this, read the documentation for this file (AN Filstruktur_V10).
def read_dynmodell(data_dir):
    File = {}
    with open(data_dir+'/DYNMODELL.SIMT', "rb") as f:
        Blokk1 = {}
        Blokk2 = {}


        # Blokk 1
        first6Ints = np.fromfile(f, dtype=np.int32, count=6)
        seriesNames = []
        for i in range(first6Ints[5]):
            seriesNames.append(np.fromfile(f,dtype=np.byte, count=40))
        eget = np.fromfile(f, dtype=np.int32, count=1)
        nkontr = np.fromfile(f, dtype=np.int32, count=1)
        IDKONTRAKT = []
        for i in range(nkontr[0]):
            IDKONTRAKT.append(np.fromfile(f, dtype=np.int32, count=1))
        last9Ints = np.fromfile(f, dtype=np.int32, count=9)
        filePos = (17+nkontr)*4+40*first6Ints[5]
        dummy = np.fromfile(f, dtype=np.int32, count=int((first6Ints[0]-filePos)/4))

        Blokk1['first6Ints'] = first6Ints
        Blokk1['seriesNames'] = seriesNames
        Blokk1['eget'] = eget
        Blokk1['nkontr'] = nkontr
        Blokk1['IDKONTRAKT'] = IDKONTRAKT
        Blokk1['last9Ints'] = last9Ints
        Blokk1['dummy'] = dummy

        File['Blokk1'] = Blokk1

        # Blokk 2-JANT+1
        for i in range(first6Ints[4]):
            File['Blokk'+str(i+2)] = np.fromfile(f, dtype=np.single, count=int(first6Ints[0]/4))

        # Remaining blocks
        for i in range(12):
            File['Blokk'+str(first6Ints[4]+2+i)] = np.fromfile(f, dtype=np.int32, count=int(first6Ints[0]/4))


        f.close()

    return File


# def duration_curve(time_series, plot_title="Duration curve", y_axis='', plot_path='', y_axis_range=None, x_range=None):

#     fig = go.Figure()

#     line_styles = ["solid", "dash"]
#     i = 0
#     for name, time_serie in time_series.items():
#         y = np.sort(time_serie.values.flatten("F"))[::-1]
#         x = np.arange(0, 100, 100 / y.size)

#         fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=name, line={'dash': line_styles[i]}))
#         ++i

#     fig.update_layout(
#         #title=plot_title,
#         xaxis_title="%",
#         yaxis_title=y_axis,
#         font=dict(
#             size=12,
#         )
#     )

#     if y_axis_range is not None:
#         fig.update_layout(yaxis_range=[y_axis_range[0], y_axis_range[1]])

#     if x_range is not None:
#         fig.update_layout(xaxis_range=[x_range[0], x_range[1]])
#         plot_title = f'{plot_title}_{x_range[0]}_{x_range[1]}'
#     if plot_path == '':
#         fig.show()
#     else:
#         fig.write_image(f'{plot_path}/{plot_title}.svg')
#     return


# def convert_prodrisk_session_to_wrapper_objects(prodrisk):
#     staticModel = []
#     prodriskCore = prodrisk._pb_api

#     object_names = prodriskCore.GetObjectNamesInSystem()
#     object_types = prodriskCore.GetObjectTypesInSystem()

#     input_objects = ["area", "module", "inflowSeries", "pump"]

#     object_dict = {}
#     for type, name in zip(object_types, object_names):

#         if type not in input_objects:
#             continue

#         if type not in object_dict:
#             object_dict[type] = [name]
#         else:
#             object_dict[type] += [name]

#     for objectType, nameList in object_dict.items():
#         allAttributeNames = list(prodriskCore.GetObjectTypeAttributeNames(objectType))
#         inputAttributeNames = []

#         for attributeName in allAttributeNames:

#             isInput = prodriskCore.GetAttributeInfo(objectType, attributeName, "isInput")
#             if isInput == "False":
#                 continue
#             datatype = prodriskCore.GetAttributeInfo(objectType, attributeName, "datatype")
#             if datatype == "txy" or datatype == "stxy":
#                 continue

#             inputAttributeNames.append(attributeName)

#         for objectName in nameList:
#                 attributes = []
#                 for attributeName in inputAttributeNames:
#                     datatype = prodriskCore.GetAttributeInfo(objectType, attributeName, "datatype")

#                     value = prodrisk.model[objectType][objectName][attributeName].get()
#                     if value is not None:
#                         if datatype == "xy":
#                             attributes.append(OBJ.Attribute(attributeName, "xy", OBJ.XyCurve(value.index, value.values)))
#                         elif datatype in ["xy_list", "xy_array"]:
#                             xy = []
#                             for element in value:
#                                 xy.append(OBJ.XyCurve(element.index, element.values, element.name))
#                             attributes.append(OBJ.Attribute(attributeName, "xy_array", xy))
#                         else:
#                             attributes.append(OBJ.Attribute(attributeName, datatype, value))
#                 staticModel.append(OBJ.ModelObject(objectType, objectName, attributes))

#         #connections = getConnections(shop)
#         #for connection in connections:
#         #	staticModel.append(OBJ.ModelObject("connect", connection, connections[connection]))

#     return staticModel

##############################
# The following functions return data from LTM files as python objects instead
# of passing them directly to a prodrisk session
def read_model_name(data_dir):
    ScenF = h5py.File(os.path.join(data_dir,'ScenarioData.h5'), 'r')
    names = list(ScenF.keys())
    model_name = names[0]
    ScenF.close()
    return model_name

def read_n_scen(data_dir, model_name):
    mod_file_name = os.path.join(data_dir, 'model.h5')
    model_file = h5py.File(mod_file_name, 'r')

    param_path = 'hydro_data/hydro_parameters'
    params = model_file.get(param_path)

    return params['value'][3]

def read_yearly_inflow(data_dir, serie_name, model_name, dt_start, n_scen=-1):
    scenario_data_file = h5py.File(os.path.join(data_dir,"ScenarioData.h5"), 'r')
    data = {}

    counter = 0
    for key in scenario_data_file.get(model_name.upper() + '/' + serie_name).keys():
        h5scenario = scenario_data_file.get(model_name.upper() + '/' + serie_name)[key]
        daily_index = [dt_start + pd.Timedelta(days=i) for i in range(52 * 7)]

        data[f"scen{counter}"] = np.array(h5scenario)[0:52*7]
        counter += 1
        if counter == n_scen:
            break

    return pd.DataFrame(index=daily_index, data=data)


def read_yearly_price_ts(LTM_input_folder, dt_start, n_scenarios=-1):

    price_df = get_price_scenarios(dt_start, LTM_input_folder, "PRISREKKE.PRI", n_weeks=52, n_scen=n_scenarios)

    return price_df  # 1H resolution

def read_module_restrictions(data_dir, dt_start, horizon_weeks=52):
    dynmodell = read_dynmodell(data_dir)

    n_mod = dynmodell['Blokk1']['first6Ints'][2]
    n_weeks = dynmodell['Blokk1']['first6Ints'][4]

    if n_weeks < horizon_weeks:
        print(f"WARNING: Restrictions from DYNMODELL.SIMT read for {n_weeks} weeks. Simulation period is set to {horizon_weeks} weeks. Restrictions for the last {horizon_weeks - n_weeks} weeks of the simulation period may be set incorrectly?")

    module_indices = dynmodell['Blokk'+str(n_weeks+2)][0:n_mod]

    MAMAX = {mod: np.zeros(n_weeks) for mod in module_indices}
    MAMIN = {mod: np.zeros(n_weeks) for mod in module_indices}
    MAGREF = {mod: np.zeros(n_weeks) for mod in module_indices}
    ENEKV = {mod: np.zeros(n_weeks) for mod in module_indices}
    QMAX = {mod: np.zeros(n_weeks) for mod in module_indices}
    QMIN = {mod: np.zeros(n_weeks) for mod in module_indices}
    QFOMAX = {mod: np.zeros(n_weeks) for mod in module_indices}
    QFOMIN = {mod: np.zeros(n_weeks) for mod in module_indices}


    # First read out to python dicts, to ensure correct sorting is maintained
    for w in range(n_weeks):
        for i in range(n_mod):
            week_block = dynmodell['Blokk'+str(w+2)]
            mod = module_indices[i]
            MAMAX[mod][w] = week_block[i*8]
            MAMIN[mod][w] = week_block[i * 8+1]
            MAGREF[mod][w] = week_block[i*8+2]
            ENEKV[mod][w] = week_block[i*8+3]
            QMAX[mod][w] = week_block[i*8+4]
            QMIN[mod][w] = week_block[i*8+5]
            QFOMAX[mod][w] = week_block[i*8+6]
            QFOMIN[mod][w] = week_block[i*8+7]

    min_weeks = min(n_weeks, horizon_weeks)
    weekly_indices = [dt_start + pd.Timedelta(weeks=w) for w in range(min_weeks)]

    mod_restrictions = {}
    for mod_id in module_indices:
        mod_restrictions[(mod_id, 'maxVol')] = pd.Series(data=MAMAX[mod_id][0:min_weeks], index=weekly_indices)
        mod_restrictions[(mod_id, 'minVol')] = pd.Series(data=MAMIN[mod_id][0:min_weeks], index=weekly_indices)
        mod_restrictions[(mod_id, 'refVol')] = pd.Series(data=MAGREF[mod_id][0:min_weeks], index=weekly_indices)
        mod_restrictions[(mod_id, 'energyEquivalent')] = pd.Series(data=ENEKV[mod_id][0:min_weeks], index=weekly_indices)
        mod_restrictions[(mod_id, 'maxDischarge')] = pd.Series(data=QMAX[mod_id][0:min_weeks], index=weekly_indices)
        mod_restrictions[(mod_id, 'minDischarge')] = pd.Series(data=QMIN[mod_id][0:min_weeks], index=weekly_indices)
        mod_restrictions[(mod_id, 'maxBypass')] = pd.Series(data=QFOMAX[mod_id][0:min_weeks], index=weekly_indices)
        mod_restrictions[(mod_id, 'minBypass')] = pd.Series(data=QFOMIN[mod_id][0:min_weeks], index=weekly_indices)

    return mod_restrictions


def read_inflow_series(data_dir, model_name, dt_start, encoding='utf-8'):
    mod_file_name = os.path.join(data_dir, 'model.h5')
    model_file = h5py.File(mod_file_name, 'r')
    watermarkdata = model_file.get('hydro_data/' + model_name.upper() + '/Watermark_data')

    infl_series = {}
    for i in range(watermarkdata.size):
        infl_name = watermarkdata['infl_name'][i].decode(encoding)

        av_inflow = watermarkdata['average_inflow'][i] #inflow_serie.histAverageInflow.set(

        inflow_364d = read_yearly_inflow(data_dir, infl_name, model_name, dt_start)

        infl_series[infl_name] = [i+1, av_inflow, inflow_364d]
        #prodrisk.model.inflowSeries[serie_name].inflowScenarios.set(inflow_scenarios)

    return infl_series


#if __name__ == "__main__":
#
#    start_time = pd.Timestamp("2030-01-07")
#    data_dir = r"C:\Users\Hansha\Documents\HydroCenSimulator\simulator\cases\basecase\prodrisk\\"
#    system_name = "SYSTEM"
#
#    prodrisk = ProdriskSession()
#    prodrisk.set_optimization_period(pd.Timestamp(start_time), n_weeks=156)
#
#    get_n_scen(prodrisk, data_dir, system_name)
#
#    add_inflow_series(prodrisk, data_dir, system_name)
#
#    price = get_price_scenarios(start_time, os.getcwd(), "prisrekke.PRI", n_weeks=52, n_scen=prodrisk.n_scenarios)
#    duration_curve({'HydroCen price': price}, y_axis="EUR/MWh")


