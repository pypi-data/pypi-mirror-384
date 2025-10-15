import numpy as np
import pandas as pd
import datetime as dt
from tqdm import tqdm

from pyshop import ShopSession
from pyprodrisk import ProdriskSession

class Cuts():
	"""
	Data structure for all cut data from one week
	
	:param rhs: The "right hand side" of the cuts. Attribute cutRHS on area-object in ProdRisk. Attribute rhs on cut_group object in SHOP.
	:param module_coeffs: The module/reservoir cut coefficients. Attribute cutCoeffs on module object in ProdRisk. Attribute cut_coeffs on reservoir object in SHOP.
	:param series_coeffs: The inflowSeries/inflow_series cut coefficients. Attribute cutCoeffs on inflowSeries object in ProdRisk. Attribute cut_coeffs on inflow_series object in SHOP.
	:param series_mean: Metadata weekly mean of the inflow to given series in ProdRisk. Required for correct correction of cut rhs before sending to SHOP.
	:param series_std: Metadata weekly standard deviation of the inflow to given series in ProdRisk. Required for correct correction of cut rhs before sending to SHOP. 
	:param cut_frequency: Metadata describing how frequent each cut has been binding during the ProdRisk optimization. 
	:param ref_prices: Metadata describing the weekly mean prices which the different cut coefficients and cut rhs reffer to. 
		Set as reference ("name" of pd.Series) of the cut data sent to SHOP. Required for correct interpolation of cuts inside SHOP. Set to None on "SHOP cuts", as the prices are then set as reference on the other series.
	
	"""
	def __init__(self, rhs: list[pd.Series], module_coeffs: dict[str, list[pd.Series]], series_coeffs: dict[str, list[pd.Series]], series_mean: dict[str, float], series_std: dict[str, float], cut_frequency: list[pd.Series], ref_prices: list[float] = None):
		
		self.rhs = rhs
		self.module_coeffs = module_coeffs
		self.series_coeffs = series_coeffs
		self.series_mean = series_mean
		self.series_std = series_std
		self.cut_frequency = cut_frequency
		self.ref_prices = ref_prices

	def get_corrected_rhs(self, shop: ShopSession):
		"""
		Function for correcting the the right hand side of the cuts based on the actual sum of inflows to all reservoirs connected to each inflow_series in SHOP. 
		The correction is done outside SHOP, as it is doubtfull if the correction method inside SHOP is consistent with how it should be done (defined inside the ProdRisk core code, not documented anywhere...)
		[Ticket #161] on the ProdRisk portal request SINTEF to follow up on this!

		:param shop: ShopSession with inflow input added. The session has to have inflow_series, and that they are connected to the reservoirs.
		"""
		
		corrected_rhs = []
		sum_shop_inflow = {}

		# Use the SHOP input as mapping of inflow series to reservoirs.
		# In the old simulator code, a separate mapping table was set up...
		reservoirs_per_serie = get_reservoirs_per_series(shop)
		timeres = shop.get_time_resolution()
		starttime = timeres['starttime']
		endtime = timeres['endtime']

		for series_name in self.series_coeffs:
			sumQ = 0.0
			
			for rsv in reservoirs_per_serie[series_name]:
				inflow = shop.model.reservoir[rsv].inflow.get()[starttime:endtime]
				if inflow is not None:
					reversed_inflow = list(reversed(inflow.values))
					sumQ += np.sum(reversed_inflow[0:168])

			sum_shop_inflow[series_name] = sumQ * 3600

		for price_point, rhs in enumerate(self.rhs):
			new_rhs = rhs
			for series_name, coeffs in self.series_coeffs.items():

				mean_q = self.series_mean[series_name]
				std_q = self.series_std[series_name]
				shop_q = sum_shop_inflow[series_name]

				if std_q == 0 or np.isnan(mean_q) or np.isnan(std_q):
					normalized_q = 0
				else:
					normalized_q = (shop_q - mean_q) / std_q

				# Correct inflow for all series
				new_rhs += coeffs[price_point]*normalized_q
			corrected_rhs.append(new_rhs) 

		return corrected_rhs
	
def get_reservoirs_per_series(shop: ShopSession):
	#Find and write all connections
	all_types = shop.shop_api.GetObjectTypesInSystem()
	all_names = shop.shop_api.GetObjectNamesInSystem()

	series_to_rsv = {}

	for series_name in shop.model.inflow_series.get_object_names():
		
		series_to_rsv[series_name] = []
	
		#Get connected reservoirs
		related_indices = shop.shop_api.GetRelations("inflow_series", series_name, "connection_standard")
		
		for i in related_indices:   
			rel_name = all_names[i]
			rel_type = all_types[i]

			# Only interested in connected reservoirs...
			if rel_type != "reservoir":
				continue
			
			if rel_name in shop.model.reservoir.get_object_names():
				series_to_rsv[series_name].append(rel_name)
			
	return series_to_rsv

def read_prodrisk_cuts(prodrisk: ProdriskSession, cut_weeks: list = None) -> dict[pd.Timestamp, Cuts]:
	
	"""
	Function for reading cuts from a ProdriskSession. Note: this function only works on a freshly run ProdriskSession! 
	The cuts are read from the binary file KUTT.SDDP in the temporary working directory, which is gone after the ProdriskSession close down.
	Pyprodrisk thus do not offer any functionality/data structure for keeping the cuts from a run, so the user has to extract the cuts 
	week by week and save them somewhere else. 


	:param prodrisk: a pyprodrisk session which just now was run.
	:param cut_weeks: list of week numbers which cuts should be extracted for. Default: will read cuts from all weeks in the prdrisk session.
	"""

	time_format = "%Y%m%d%H%M"
		
	prodrisk_cuts = {}
	
	if cut_weeks is None:
		cut_weeks = range(prodrisk.n_weeks)

	module_names = prodrisk.model.module.get_object_names()
	series_names = prodrisk.model.inflowSeries.get_object_names()
	area_name = prodrisk.model.area.get_object_names()[0]
	my_area = prodrisk.model.area[area_name]

	price_band = prodrisk.model.area[area_name].priceBand.get()
	series_inflows = get_series_inflows(prodrisk)

	prodriskCore = prodrisk._pb_api
	for cut_week in tqdm(cut_weeks, total=min(len(cut_weeks), 52), desc="Reading ProdRisk cuts"):
		cut_time = prodrisk.start_time + pd.Timedelta(weeks=cut_week)

		prodriskCore.SetCutTime(dt.datetime.strftime(cut_time, time_format))
		prodriskCore.ReadCutResults()
		#print("Done reading cuts for week ", week)

		# TODO: Bug in pyprodrisk (ticket#162): Price band missing results from last week. This hack will prevent a crash.
		ref_price_cut_week = min(cut_week, price_band.values.shape[0]-1)
		ref_prices = [scenario for scenario in price_band.values[:][ref_price_cut_week]]
		rhs = my_area.cutRHS.get()
		cut_frequency = my_area.cutFrequency.get()

		mod_coeffs = {}
		for mod_name in module_names:
			coeffs = prodrisk.model.module[mod_name].cutCoeffs.get()
			if (coeffs is not None):
				mod_coeffs[mod_name] = coeffs

		series_coeffs = {}
		for series_name in series_names:
			coeffs = prodrisk.model.inflowSeries[series_name].cutCoeffs.get()
			series_coeffs[series_name] = coeffs

		series_mean = {}
		series_std = {}
		for series_name in series_names:
			if not series_name in series_inflows:
				continue
			Q = [3600 * 168 * scenario for scenario in series_inflows[series_name].loc[cut_time:cut_time+pd.Timedelta(weeks=1)-pd.Timedelta(hours=1)].resample('W').mean().values]

			series_mean[series_name] = np.mean(Q)
			series_std[series_name] = np.std(Q, ddof=1)  # ddof = 1 results in the sample standard deviation

		prodrisk_cuts[cut_time] = Cuts(rhs, mod_coeffs, series_coeffs, series_mean, series_std, cut_frequency, ref_prices)
	
	
	return prodrisk_cuts

def set_prodrisk_cuts(long_prodrisk: ProdriskSession, prodrisk_cuts: dict, prodrisk: ProdriskSession, cut_weeks: list=None) -> None:
	
	"""
	Function for setting prodrisk_cuts read from a ProdRisk session "long_prodrisk" as input on a new session "prodrisk". Will be used in update runs.

	:param long_prodrisk: cuts got from this session
	:param prodrisk_cuts: cuts from this earlier session
	:param prodrisk: set cuts on this session
	:param cut_weeks: list of week numbers which cuts should be copied for. Default: will read cuts from all weeks in the prdrisk session.
	"""
	time_format = "%Y%m%d%H%M"
			
	if cut_weeks is None:
		cut_weeks = range(prodrisk.n_weeks)

	area_name = prodrisk.model.area.get_object_names()[0]
	my_area = prodrisk.model.area[area_name]

	my_area.priceBand.set(long_prodrisk.model.area[area_name].priceBand.get())
	my_area.priceTransition.set(long_prodrisk.model.area[area_name].priceTransition.get())

	for mod_name in prodrisk.model.module.get_object_names():
		prodrisk.model.module[mod_name].localInflow.set(long_prodrisk.model.module[mod_name].localInflow.get())



	for cut_week in cut_weeks:
		cut_time = prodrisk.start_time + pd.Timedelta(weeks=cut_week)
		prodrisk._pb_api.SetCutTime(dt.datetime.strftime(cut_time, time_format))

		week_cuts = prodrisk_cuts[cut_time]

		my_area.cutRHS.set(week_cuts.rhs)
		my_area.cutFrequency.set(week_cuts.cut_frequency)

		for mod_name, coeffs in week_cuts.module_coeffs.items():
			prodrisk.model.module[mod_name].cutCoeffs.set(coeffs)
			
		for series_name, coeffs in week_cuts.series_coeffs.items():
			prodrisk.model.inflowSeries[series_name].cutCoeffs.set(coeffs)

		prodrisk._pb_api.WriteCutResults()
	
	

def get_series_inflows(prodrisk: ProdriskSession) -> dict[str, pd.Series]:
    
	series_inflows = {}

	module_names = prodrisk.model.module.get_object_names()
	series_names = prodrisk.model.inflowSeries.get_object_names()
	

	for mod_name in module_names:
		mod = prodrisk.model.module[mod_name]
		local_inflow = mod.localInflow.get()

		connectedSeriesId = mod.connectedSeriesId.get()
		for series_name in series_names:
			seriesId = prodrisk.model.inflowSeries[series_name].seriesId.get()
			if seriesId == connectedSeriesId:
				if series_name in series_inflows.keys():
					series_inflows[series_name] = series_inflows[series_name] + local_inflow
				else:
					series_inflows[series_name] = local_inflow

	return series_inflows


def convert_prodrisk_cuts_to_shop_cuts(prodrisk_cuts: dict[pd.Timestamp, Cuts]) -> dict[pd.Timestamp, Cuts]:
	"""
	Function for converting the cuts from a ProdRisk session so that they may be given as input to SHOP. 
		- Returns a dictionary, where the keys refer to the end of the week each set of cuts are valid for.
		- Cuts with all zero coefficients and right hand side are removed. ProdRisk creates n_scenarios set
		of cuts per iteration, so might provide "zero cuts" if max_iterations is set less than 
		max_cuts_created/n_scenarios...
		- Change the index of the dict with weekly cuts. pyprodrisk use the first hour of the week
		as the "reference time" for the cuts of a week. pyshop assumes the end values are valid for
		the end of the optimization period, so the endtime of a shop session is a more suited key
		to look up in a dictionary.
		- The unit of the cut rhs and cut coefficients are changed from kEUR/Mm3 (pyprodrisk) to EUR/Mm3 (pyshop).
		- The sign of the cut rhs is switched, due to different sign convensions. 
			- In ProdRisk, area cutRHS describe "the future expected cost" (usually a large negative number).
			- In SHOP, the cut_group rhs describe "the future expected income".
		- The weekly reference prices are added as references on the pd.Series with cut coefficients and cut rhs.


	:param prodrisk_cuts: dictionary with Cuts per week. The keys refer to the start of the given week where the
	cuts describe the water value at the end of the week...
	"""
	
	shop_cuts = {}

	for cut_time, cuts in prodrisk_cuts.items():
		
		# See if there are zero cuts (all coeffs and rhs are zero)
		tolerance = 1e-5
		n_cuts = cuts.rhs[0].size
		zeros_in_rhs = [i for i, val in enumerate(cuts.rhs[0].values) if abs(val) < tolerance]

		for index in zeros_in_rhs:
			is_real_zero = True
			for mod_name, coeffs in cuts.module_coeffs.items():
				if abs(coeffs[0].values[index]) > tolerance:
					is_real_zero = False
					break

			if is_real_zero:
				n_cuts = index
				break
		# Is there a guarantee that all following cuts are also zero??
		# Why not check series coeff. as well?
		# Does the order of the cuts matter in SHOP?
		# Should we use cut_crequency as a filter? 

		n_price_points = len(cuts.cut_frequency)
		module_coeffs = {}
		series_coeffs = {}
		
		cut_frequency = [cuts.cut_frequency[i].iloc[0:n_cuts] for i in range(n_price_points)]

		for mod_name, coeffs in cuts.module_coeffs.items():
			module_coeffs[mod_name] = [1000*coeffs[i].iloc[0:n_cuts] for i in range(n_price_points)]
			
		for series_name, coeffs in cuts.series_coeffs.items():
			if coeffs is None:
				continue
			series_coeffs[series_name] = [1000*coeffs[i].iloc[0:n_cuts] for i in range(n_price_points)]

		rhs = [-1000*cuts.rhs[i].iloc[0:n_cuts] for i in range(n_price_points)]
			
		# Update "name" of all cut data structures to the weekly mean price of given price point. 
		# This is used as a reference in SHOP, to interpolate the cuts for the closest price points
		for pp in range(len(rhs)):
			rhs[pp].name = cuts.ref_prices[pp]

			for mod_name, coeff in module_coeffs.items():
				coeff[pp].name = cuts.ref_prices[pp]
			for series_name, coeff in series_coeffs.items():
				coeff[pp].name = cuts.ref_prices[pp]

		# Use end week as index for the SHOP cuts, to increase flexibility of the "SHOP week" horizon beyond 1 week.
		# The cuts describe the water value at the end of a given week, but pyprodrisk use the first hour of the week as timestamp for "this weeks cuts".
		shop_cut_time = cut_time + pd.Timedelta(weeks=1)
		shop_cuts[shop_cut_time] = Cuts(rhs, module_coeffs, series_coeffs, cuts.series_mean, cuts.series_std, cut_frequency)
		
	return shop_cuts