# import numpy as np

# from pyprodrisk import ProdriskSession
# from pyshop import ShopSession

# class InputConsistencyCheck():
#     def __init__(self, 
#                 prodrisk: ProdriskSession,
#                 shop: ShopSession,
#                 settings: dict) -> None:
#         self.prodrisk = prodrisk
#         self.shop = shop
#         self.settings = settings
                
#         self.check_all_input()

    
#     def check_all_input(self) -> None:

#         if "cut_module_to_rsv" in self.settings["mapping"].keys():
#             # Reservoir tests
#             self.check_rsv_max()
#             self.check_vol_head()
#         else:
#             print("WARNING: Unable to compare ProdRisk and SHOP reservoir data due to missing mapping table 'cut_module_to_rsv' on the config file.")

#         if "mod_to_plant" in self.settings["mapping"].keys():
#             # Plant tests
#             self.check_q_max()
#             self.check_outlet_line()
#         else:
#             print("WARNING: Unable to compare ProdRisk and SHOP plant data due to missing mapping table 'mod_to_plant' on the config file.")
        
#         # Time series input logging (comparisons are not relevant)
#         self.check_time_series()
#         #self.check_shop_time_series()



#     def check_time_series(self, check_object_types = ["module"]) -> None:
#         print("\n\n ########## Check time series inputs ##########\n")
#         print(" ########## Prints all time series constraints in ProdRisk ##########")
#         print(" ########## Writes out different between ProdRisk and SHOP input if a mapping table is specified on the config file ##########")

#         time_res = self.shop.get_time_resolution()

#         compare_time_series = True
#         if "compare_txy_attributes" not in self.settings["mapping"].keys():
#             print("WARNING! No time series mapping table specified, so unable to compare time series input!")
#             compare_time_series = False

#         for object_type in check_object_types:
#             # Iterate over all attributes of each object type
#             object_attributes = self.prodrisk._pb_api.GetObjectTypeAttributeNames(object_type)
#             for attribute_name in object_attributes:
#                 # Get license
#                 license_name = self.prodrisk._pb_api.GetAttributeInfo(object_type, attribute_name, 'license_name')
#                 if "INTERNAL" in license_name:
#                     continue
                
#                 compare_object_type_time_series = (compare_time_series and 
#                                                    object_type in self.settings["mapping"]["compare_txy_attributes"].keys())

#                 # Gather table data from prodrisk
#                 data_type = self.prodrisk._pb_api.GetAttributeInfo(object_type, attribute_name, 'datatype')

#                 # No other time dependent data than price and inflow is currently mapped from ProdRisk to SHOP...
#                 if data_type not in ["txy", "txy_stochastic"]:
#                     continue

#                 # Some ProdRisk attributes are not relevant in SHOP: refVol, energyEquivalent, others?
#                 if attribute_name in ["inflowScenarios", "price", "refVol", "energyEquivalent"]:
#                     continue

#                 for obj_name in self.prodrisk.model[object_type].get_object_names():
#                     prodrisk_txy = self.prodrisk.model[object_type][obj_name][attribute_name].get()

#                     compare_attr_time_series = (compare_object_type_time_series and 
#                                                 obj_name in self.settings["mapping"]["compare_txy_attributes"][object_type].keys() and
#                                                 attribute_name in self.settings["mapping"]["compare_txy_attributes"][object_type][obj_name].keys())

#                     if prodrisk_txy is not None:
#                         print(f"Attribute {attribute_name} is set for {object_type} {obj_name}.")
#                         prodrisk_txy = prodrisk_txy[time_res["starttime"]:time_res["endtime"]]
#                         shop_txy = 0*prodrisk_txy
#                         if compare_attr_time_series:
#                             found_shop_input = False
#                             for (shop_type, shop_name, shop_attr) in self.settings["mapping"]["compare_txy_attributes"][object_type][obj_name][attribute_name]:
#                                 shop_txy_component = self.shop.model[shop_type][shop_name][shop_attr].get()
#                                 if shop_txy_component is not None:
#                                     found_shop_input = True
#                                     shop_txy = shop_txy + shop_txy_component.reindex(prodrisk_txy.index)
#                             if not found_shop_input:
#                                 print(f"WARNING! 'compare_txy_attributes' mapping data set for {object_type}, {obj_name}, {attribute_name}, but none of the corresponding SHOP attributes where set!")
#                             elif max(abs((shop_txy-prodrisk_txy))) > 1.e-3:
#                                 print(f"WARNING! The SHOP input data differs from the series set on {object_type}, {obj_name}, {attribute_name}")    



#     def check_shop_time_series(self) -> None:
#         print("\n\n ########## Check SHOP time series input ##########\n")
#         print("########## Time dependent SHOP constraints should be set with care. ##########")
#         print("########## Are they valid for all weeks and scenarios in the simulation? ##########\n")

#         shop_object_names = self.shop.shop_api.GetObjectTypeNames()
#         for object_name in shop_object_names:
#             # Iterate over all attributes of each object type
#             object_attributes = self.shop.shop_api.GetObjectTypeAttributeNames(object_name)
#             for attribute in object_attributes:
#                 # Get license
#                 license_name = self.shop.shop_api.GetAttributeInfo(object_name, attribute, 'licenseName')
#                 if "INTERNAL" in license_name:
#                     continue

#                 # Gather table data from shop
#                 object_type = object_name
#                 attribute_name = attribute
#                 data_type = self.shop.shop_api.GetAttributeInfo(object_name, attribute, 'datatype')

#                 if data_type in ["txy"] and attribute_name not in ["inflow", "price"]:

#                     for obj_name in self.shop.model[object_type].get_object_names():
#                         if self.shop.model[object_type][obj_name][attribute_name].get() is not None:
#                             print(f"Attribute {attribute_name} is set for {object_type} {obj_name}.")
#                             txy = self.shop.model[object_type][obj_name][attribute_name].get()
#                             print(f"First 10 values: {[txy.values[i] for i in range(10)]}\n")

#     def check_rsv_max(self) -> None:
#         print("\n\n ##########  Check reservoir capacities ########## \n")
#         for mod, rsvs in self.settings["mapping"]["cut_module_to_rsv"].items():
#             mod_max = self.prodrisk.model.module[mod].rsvMax.get()
#             rsvs_max = 0.0
#             for rsv in rsvs:
#                 rsvs_max += self.shop.model.reservoir[rsv].max_vol.get()

#             if abs(mod_max-rsvs_max) > 1.e-4:
#                 print(f"Difference in max_vol for module {mod}. ProdRisk: {mod_max}, SHOP: {rsvs_max}")

#     def check_vol_head(self) -> None:
#         print("\n\n ########## Check reservoir vol head curves ##########\n")
#         for mod, rsvs in self.settings["mapping"]["cut_module_to_rsv"].items():
#             print(f"\nModule: {mod}")
#             mod_vol_head = self.prodrisk.model.module[mod].volHeadCurve.get()

#             if self.prodrisk.model.module[mod].rsvMax.get() < 1.e-5:
#                 print(f"Skip comparing vol head curves, as rsvMax is < 1e-5")
#                 continue

#             if mod_vol_head is None:
#                 print(f"Missing volHeadCurve for module {mod} in ProdRisk.")
#                 continue

#             for vol, head in zip(mod_vol_head.index, mod_vol_head.values):
#                 shop_vol = 0.0
#                 for rsv in rsvs:
#                     rsv_vol_head = self.shop.model.reservoir[rsv].vol_head.get()
#                     if head > max(rsv_vol_head.values) or head < min(rsv_vol_head.values):
#                         print(f"ProdRisk head: {head} for module {mod} not in vol head "
#                             f"curve for the SHOP reservoir {rsv}."
#                             f"lrl: {self.shop.model.reservoir[rsv].lrl.get()}, "
#                             f"hrl: {self.shop.model.reservoir[rsv].hrl.get()}")
#                         continue

#                     shop_vol += np.interp(head, rsv_vol_head.values, rsv_vol_head.index)

#                 if abs(vol - shop_vol) > 1e-6:
#                     print(f"Difference in vol_head curves for module {mod} at head {head}. ProdRisk: {vol}, SHOP: {shop_vol}")

#     def get_coupled_modules(self, gathering_mod) -> list:
#         gath_mod_nr = self.prodrisk.model.module[gathering_mod].number.get()
#         coupled_modules = []
#         for mod in self.prodrisk.model.module.get_object_names():
#             topo = self.prodrisk.model.module[mod].topology.get()
#             if topo[0] == gath_mod_nr:
#                 coupled_modules.append(mod)
#         return coupled_modules

#     def get_hyd_copl_qmax(self, mod) -> float:
#         coupled_modules = self.get_coupled_modules(mod)
#         qmax = 0.0
#         if len(coupled_modules) > 2:
#             print(f"Warning: More than 2 modules discharge to {mod}. Are all these hydraulic coupled? {coupled_modules}.")
#         for coupled_mod in coupled_modules:
#             qmax = max(qmax, self.prodrisk.model.module[coupled_mod].maxDischargeConst.get())
#         return qmax


#     def check_q_max(self):
#         print("\n\n ########## Check plant discharge capacities ########## \n")
#         for mod, plant in self.settings["mapping"]["mod_to_plant"].items():
#             if plant == "":
#                 continue

#             hyd_copl = self.prodrisk.model.module[mod].hydraulicType.get()

#             if hyd_copl[0] > 0:
#                 mod_max = self.get_hyd_copl_qmax(mod)
#             else:
#                 mod_max = self.prodrisk.model.module[mod].maxDischargeConst.get()

#             plant_max = self.get_plant_qmax(plant)

#             if abs(mod_max-plant_max) > 1.e-6:
#                 print(f"Difference in qmax for plant {plant}. ProdRisk: {mod_max}, SHOP: {plant_max}")

#     def check_outlet_line(self):
#         print("\n\n ########## Check plant outlet lines ##########\n")
#         for mod, plant in self.settings["mapping"]["mod_to_plant"].items():
#             if plant == "":
#                 continue

#             hyd_copl = self.prodrisk.model.module[mod].hydraulicType.get()

#             if hyd_copl[0] > 0:
#                 mod_outlet = self.get_hyd_copl_outlet_line(mod)
#             else:
#                 mod_outlet = self.prodrisk.model.module[mod].submersion.get()

#             plant_outlet = self.shop.model.plant[plant].outlet_line.get()

#             if abs(mod_outlet - plant_outlet) > 1.e-3:
#                 print(f"Difference in outlet lines for plant {plant}. ProdRisk: {mod_outlet}, SHOP: {plant_outlet}")

#     def get_hyd_copl_outlet_line(self, mod) -> float:
#         coupled_modules = self.get_coupled_modules(mod)
#         outlet_lines = []
#         if len(coupled_modules) > 2:
#             print(f"Warning: More than 2 modules discharge to {mod}. Are all these hydraulic coupled? {coupled_modules}.")
#         for coupled_mod in coupled_modules:
#             outlet_lines.append(self.prodrisk.model.module[coupled_mod].submersion.get())

#         if outlet_lines[0] != outlet_lines[1]:
#             print(f"Outlet lines different for two hydraulic coupled modules: "
#                 f"{coupled_modules[0]} and {coupled_modules[1]}. First value is used.")
#         return outlet_lines[0]

#     def get_plant_qmax(self, plant) -> float:
#         qmax = 0.0
#         for gen in self.shop.model.plant[plant].generators:
#             gen_qmax = 0.0
#             for curve in gen.turb_eff_curves.get():
#                 gen_qmax = max(gen_qmax, max(curve.index))
#             qmax += gen_qmax

#         return qmax


