######################################################
#
# Swiss-EnergyScope (SES) MILP modeling framework
# Model file
# Author: Stefano Moret
# Date: 27.10.2017
# Model documentation: Moret S. (2017). "Strategic Energy Planning under Uncertainty". PhD Thesis n. 7961, EPFL, Switzerland (Chapter 1). (http://dx.doi.org/10.5075/epfl-thesis-7961)
# For terms of use and how to cite this work please check the ReadMe file. 
#
######################################################

### SETS [Figure 1.3] ###

## MAIN SETS: Sets whose elements are input directly in the data file
set PERIODS; # time periods
set SECTORS; # sectors of the energy system
set END_USES_INPUT; # Types of demand (end-uses). Input to the model
set END_USES_CATEGORIES; # Categories of demand (end-uses): electricity, heat, mobility
set END_USES_TYPES_OF_CATEGORY {END_USES_CATEGORIES}; # Types of demand (end-uses).
set RESOURCES; # Resources: fuels (wood and fossils) and electricity imports 
set BIOMASS within RESOURCES;
set EXPORT within RESOURCES; # exported resources 
set END_USES_TYPES := setof {i in END_USES_CATEGORIES, j in END_USES_TYPES_OF_CATEGORY [i]} j; # secondary set
set TECHNOLOGIES_OF_END_USES_TYPE {END_USES_TYPES}; # set all energy conversion technologies (excluding storage technologies)
set STORAGE_TECH; # set of storage technologies 
set STORAGE_ALL;
set INFRASTRUCTURE; # Infrastructure: DHN, grid, and intermediate energy conversion technologies (i.e. not directly supplying end-use demand)
set INTERMIDIATE_RESOURCES within RESOURCES;
set RENEW within RESOURCES;

## Biomasss
set BIO_PRODUCT;

## set for CCUS
set CO2_CATEGORY;
set TECHNOLOGIES_OF_CC;
set TECHNOLOGIES_OF_CCS;
set TECHNOLOGIES_OF_CCU;
set TECHNOLOGIES_OF_CCUS:=TECHNOLOGIES_OF_CC union TECHNOLOGIES_OF_CCS union TECHNOLOGIES_OF_CCU;


## Mobility [@Tuong-Van Nguyen, Jonas Schnidrig]
set TECHNOLOGIES_OF_PRIVATEMOB_ALL_DISTANCES;
set MODELS_OF_TECHNOLOGIES_OF_PRIVATEMOB_ALL_DISTANCES {TECHNOLOGIES_OF_PRIVATEMOB_ALL_DISTANCES}; # Makes the link between a given private mobility tech and its corresponding local/longd model  

## SECONDARY SETS: a secondary set is defined by operations on MAIN SETS
set LAYERS := (RESOURCES diff EXPORT) union END_USES_TYPES; # Layers are used to balance resources/products in the system
set TECHNOLOGIES := (setof {i in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE [i]} j) union STORAGE_TECH union INFRASTRUCTURE union TECHNOLOGIES_OF_CCUS union TECHNOLOGIES_OF_PRIVATEMOB_ALL_DISTANCES; 
set TECHNOLOGIES_OF_END_USES_CATEGORY {i in END_USES_CATEGORIES} within TECHNOLOGIES := setof {j in END_USES_TYPES_OF_CATEGORY[i], k in TECHNOLOGIES_OF_END_USES_TYPE [j]} k; 

## Grid infrastructure sets
set ELECTRICITY_LAYERS within LAYERS;
set NG_LAYERS within LAYERS;
set H2_LAYERS within LAYERS;
set GRIDS_OF_LAYERS{ELECTRICITY_LAYERS union NG_LAYERS union H2_LAYERS};
set GRIDS;
# Printing sets
set INFRASTRUCTURE_ELEC_GRID;
set INFRASTRUCTURE_GAS_GRID;
set INFRASTRUCTURE_ELEC_STORAGE;
set INFRASTRUCTURE_GAS_STORAGE;


## Additional SETS: only needed for printing out results
set COGEN within TECHNOLOGIES; # cogeneration tech
set BOILERS within TECHNOLOGIES; # boiler tech

## Mobility sets
set BUSES within TECHNOLOGIES;
# For NG storage

set INTERMITTENT_TECHNOLOGIES;

### PARAMETERS [Table 1.1] ###
param end_uses_demand_year {END_USES_INPUT, SECTORS} >= 0 default 0; # end_uses_year: table end-uses demand vs sectors (input to the model). Yearly values.
param end_uses_input {i in END_USES_INPUT} := sum {s in SECTORS} (end_uses_demand_year [i,s]); # Figure 1.4: total demand for each type of end-uses across sectors (yearly energy) as input from the demand-side model
param i_rate > 0; # discount rate (real discount rate)

# Share public vs private mobility
param share_mobility_public_min >= 0, <= 1; # % min limit for penetration of public mobility over total mobility 
param share_mobility_public_max >= 0, <= 1; # % max limit for penetration of public mobility over total mobility 

# Share train vs truck in freight transportation
param share_freight_train_min >= 0, <= 1; # % min limit for penetration of train in freight transportation
param share_freight_train_max >= 0, <= 1; # % max limit for penetration of train in freight transportation

# Share dhn vs decentralized for low-T heating
param share_heat_dhn_min >= 0, <= 1; # % min limit for penetration of dhn in low-T heating
param share_heat_dhn_max >= 0, <= 1; # % max limit for penetration of dhn in low-T heating

param t_op {PERIODS}; # duration of each time period [h]
param total_time := sum {t in PERIODS} (t_op [t]); # added just to simplify equations
param lighting_month {PERIODS} >= 0, <= 1; # %_lighting: factor for sharing lighting across months (adding up to 1)
param heating_month {PERIODS} >= 0, <= 1; # %_sh: factor for sharing space heating across months (adding up to 1), hot water (HW) not included which is considered to be constant over months

# f: input/output Resources/Technologies to Layers. Reference is one unit ([GW] or [Mpkm/h] or [Mtkm/h]) of (main) output of the resource/technology. input to layer (output of technology) > 0.
param layers_in_out {RESOURCES union TECHNOLOGIES diff STORAGE_TECH, LAYERS union CO2_CATEGORY union {"HEAT_WASTE"}} default 0;

# Attributes of TECHNOLOGIES
param ref_size {TECHNOLOGIES} >= 0 default 0.001; # f_ref: reference size of each technology, expressed in the same units as the layers_in_out table. Refers to main output (heat for cogen technologies). storage level [GWh] for STORAGE_TECH
param c_inv {TECHNOLOGIES} >= 0 default 0.000001; # Specific investment cost [MCHF/GW].[MCHF/GWh] for STORAGE_TECH
param c_maint {TECHNOLOGIES} >= 0 default 0; # O&M cost [MCHF/GW/year]: O&M cost does not include resource (fuel) cost. [MCHF/GWh] for STORAGE_TECH
param lifetime {TECHNOLOGIES} >= 0 default 20; # n: lifetime [years]
param f_max {TECHNOLOGIES} >= 0 default 300000; # Maximum feasible installed capacity [GW], refers to main output. storage level [GWh] for STORAGE_TECH
param f_min {TECHNOLOGIES} >= 0 default 0; # Minimum feasible installed capacity [GW], refers to main output. storage level [GWh] for STORAGE_TECH
param fmax_perc {TECHNOLOGIES} >= 0, <= 1 default 1; # value in [0,1]: this is to fix that a technology can at max produce a certain % of the total output of its sector over the entire year
param fmin_perc {TECHNOLOGIES} >= 0, <= 1 default 0; # value in [0,1]: this is to fix that a technology can at min produce a certain % of the total output of its sector over the entire year
param c_p_t {TECHNOLOGIES, PERIODS} >= 0, <= 1 default 1; # capacity factor of each technology and resource, defined on monthly basis. Different than 1 if F_Mult_t (t) <= c_p_t (t) * F_Mult
param c_p {TECHNOLOGIES} >= 0, <= 1 default 1; # capacity factor of each technology, defined on annual basis. Different than 1 if sum {t in PERIODS} F_Mult_t (t) * t_op (t) <= c_p * F_Mult
param tau {i in TECHNOLOGIES} := i_rate * (1 + i_rate)^lifetime [i] / (((1 + i_rate)^lifetime [i]) - 1); # Annualisation factor for each different technology
param gwp_constr {TECHNOLOGIES} >= 0 default 0; # GWP emissions associated to the construction of technologies [ktCO2-eq./GW]. Refers to [GW] of main output
param trl {TECHNOLOGIES} >=0 default 9; # Specific investment cost [MCHF/GW].[MCHF/GWh] for STORAGE_TECH

# Attributes of RESOURCES
param c_op {RESOURCES,PERIODS} >= 0 default 0.000001; # cost of resources in the different periods [MCHF/GWh]
param avail {RESOURCES} >= 0 default 0; # Yearly availability of resources [GWh/y]
#param gwp_op {RESOURCES} >= 0 default 0; # GWP emissions associated to the use of resources [ktCO2-eq./GWh]. Includes extraction/production/transportation and combustion => modification: excluding the combustion 
param carbon_content {RESOURCES union CO2_CATEGORY} >= 0 default 0.07; #kt-C/GWh
param gwp_e{RESOURCES,PERIODS} >=0 default 0; # [ktCO2-eq/GWh] GWP due to minning, transportation in resource importation

param f_grid_ext {GRIDS} default 0; # existing grid size [GW]
param l_grid_ext {GRIDS} default 0; # existing grid length [km]
param n_stations {GRIDS} default 1; # number of transformation stations [-]
param l_grid_ref {g in GRIDS} := l_grid_ext [g]/ n_stations [g] ; # average grid transition length per energytron [km]
param k_security {GRIDS} default 0; # Conversion factor from model-observation-security [-]

# Attributes of STORAGE_TECH
param storage_eff_in {STORAGE_TECH, LAYERS} >= 0, <= 1 default 0; # eta_sto_in: efficiency of input to storage from layers.  If 0 storage_tech/layer are incompatible
param storage_eff_out {STORAGE_TECH, LAYERS} >= 0, <= 1 default 0; # eta_sto_out: efficiency of output from storage to layers. If 0 storage_tech/layer are incompatible

# Losses in the networks
param loss_coeff {END_USES_TYPES} >= 0 default 0; # 0 in all cases apart from electricity grid and DHN
param peak_dhn_factor >= 0;

# Control pamameters
param co2_limit default 100000000;
param co2_limit_max default 0;

param sng_min default 0;
param renew default 0;
param trl_min default 1;
param trl_max default 9;
param bio_ratio default 0;


## VARIABLES [Tables 1.2, 1.3] ###
var End_Uses {LAYERS, PERIODS} >= 0; # total demand for each type of end-uses (monthly power). Defined for all layers (0 if not demand)

#var Number_Of_Units {TECHNOLOGIES} integer; # N: number of units of size ref_size which are installed.
var F_Mult {TECHNOLOGIES} >= 0; # F: installed size, multiplication factor with respect to the values in layers_in_out table
var F_Mult_t {RESOURCES union TECHNOLOGIES, PERIODS} >= 0; # F_t: Operation in each period. multiplication factor with respect to the values in layers_in_out table. Takes into account c_p
var C_inv {TECHNOLOGIES} >= 0; # Total investment cost of each technology
var C_maint {TECHNOLOGIES} >= 0; # Total O&M cost of each technology (excluding resource cost)
var C_op {RESOURCES} >= 0; # Total O&M cost of each resource
var Storage_In {i in STORAGE_TECH, LAYERS, PERIODS} >= 0; # Sto_in: Power [GW] input to the storage in a certain period
var Storage_Out {i in STORAGE_TECH, LAYERS, PERIODS} >= 0; # Sto_out: Power [GW] output from the storage in a certain period
var Share_Mobility_Public >= share_mobility_public_min, <= share_mobility_public_max; # %_Public: % of passenger mobility attributed to public transportation
var Share_Freight_Train, >= share_freight_train_min, <= share_freight_train_max; # %_Rail: % of freight mobility attributed to train
var Share_Heat_Dhn, >= share_heat_dhn_min, <= share_heat_dhn_max; # %_Dhn: % of low-T heat demand attributed to DHN
var Y_Solar_Backup {TECHNOLOGIES} binary; # Y_Solar: binary variable. if 1, identifies the decentralized technology (only 1) which is backup for solar. 0 for all other technologies
var Losses {END_USES_TYPES, PERIODS} >= 0; # Loss: Losses in the networks (normally electricity grid and DHN)
var GWP_constr {TECHNOLOGIES} >= 0; # Total emissions of the technologies [ktCO2-eq.]
var TotalGWP; # GWP_tot: Total global warming potential (GWP) emissions in the system [ktCO2-eq./y]
var TotalCost >= 0; # C_tot: Total GWP emissions in the system [ktCO2-eq./y]

# variables added for recording the output results 
var Monthly_Prod{TECHNOLOGIES,PERIODS}; #[GWh] the production in each time period except storage technologies
var Annual_Prod{TECHNOLOGIES diff STORAGE_TECH};
var STO{STORAGE_TECH,PERIODS};   #[GWh], real stored energy in a certain technology, with efficiency considered
var GWP{CO2_CATEGORY,PERIODS}; # for CO2_A CO2_C CO2_S CO2_E CO2_CS at each time period, unit: kt/h
var Total_emission{PERIODS};

# variables for ng storage
var STO_NG_LEVEL{PERIODS} >= 0; 
var STO_CO2_LEVEL{PERIODS} >=0;
var STO_H2_LEVEL{PERIODS} >=0;

# variables of INFRASTRUCTURE
var C_inv_grid_help{GRIDS} >= 0;
### CONSTRAINTS ###

## End-uses demand calculation constraints 

# [Figure 1.4] From annual energy demand to monthly power demand. End_Uses is non-zero only for demand layers.
subject to end_uses_t {l in LAYERS, t in PERIODS}:
	End_Uses [l,t] = (if l == "ELECTRICITY_LV" then
			(end_uses_input[l] / total_time + end_uses_input["LIGHTING"] * lighting_month [t] / t_op [t] + Losses [l,t])
		else (if l == "ELECTRICITY_MV" then
			end_uses_input[l] / total_time  + Losses [l,t]
		else (if l == "ELECTRICITY_HV" then
			end_uses_input[l] / total_time  + Losses [l,t]
		else (if l == "ELECTRICITY_EHV" then
			end_uses_input[l] / total_time  + Losses [l,t]
		else (if l == "HEAT_LOW_T_DHN" then
			(end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_month [t] / t_op [t]) * Share_Heat_Dhn + Losses [l,t]
		else (if l == "HEAT_LOW_T_DECEN" then
			(end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_month [t] / t_op [t]) * (1 - Share_Heat_Dhn)
		else (if l == "MOB_PUBLIC_LOCAL" then
			(end_uses_input["MOBILITY_PASSENGER_LOCAL"] / total_time) * Share_Mobility_Public
		else (if l == "MOB_PUBLIC_LONGD" then
			(end_uses_input["MOBILITY_PASSENGER_LONGD"] / total_time) * Share_Mobility_Public
		else (if l == "MOB_PRIVATE_LOCAL" then
			(end_uses_input["MOBILITY_PASSENGER_LOCAL"] / total_time) * (1 - Share_Mobility_Public)
		else (if l == "MOB_PRIVATE_LONGD" then
			(end_uses_input["MOBILITY_PASSENGER_LONGD"] / total_time) * (1 - Share_Mobility_Public)
		else (if l == "MOB_FREIGHT_RAIL" then
			(end_uses_input["MOBILITY_FREIGHT"] / total_time) * Share_Freight_Train
		else (if l == "MOB_FREIGHT_ROAD" then
			(end_uses_input["MOBILITY_FREIGHT"] / total_time) * (1 - Share_Freight_Train)
		else (if l == "HEAT_HIGH_T" then
			end_uses_input[l] / total_time
		else (if l == "MOB_AVIATION" then
			end_uses_input["MOBILITY_AVIATION"] / total_time
		else 
			0 )))))))))))))); # For all layers which don't have an end-use demand

## Layers

# [Eq. 1.13] Layer balance equation with storage. Layers: input > 0, output < 0. Demand > 0. Storage: in > 0, out > 0;
# output from technologies/resources/storage - input to technologies/storage = demand. Demand has default value of 0 for layers which are not end_uses
subject to layer_balance {l in LAYERS union CO2_CATEGORY diff {"H2_S","NG_S","CO2_CS","HEAT_WASTE","ELEC_S","DIESEL_S","GASOLINE_S"}, t in PERIODS}:
	0 = (if (l=="CO2_A" or l=="CO2_S") then
	   #unit for ccus technology: kt/h, operational net emission
		sum {i in RESOURCES union TECHNOLOGIES diff STORAGE_TECH} (layers_in_out[i, l] * F_Mult_t [i, t]) - GWP [l, t]
	else (if l=="CO2_E" then
		sum {i in RESOURCES union TECHNOLOGIES diff STORAGE_TECH} (layers_in_out[i, l] * F_Mult_t [i, t]) - GWP [l, t] 
		+ 1/total_time * sum {k in TECHNOLOGIES} GWP_constr[k] # the construction emission goes to CO2_E which can only be captured by DAC
	else (if l=="CO2_EE" then
		sum {i in RESOURCES} (F_Mult_t [i, t] * gwp_e[i,t]) - GWP [l, t]
	else (if l=="CO2_C" then
		sum {i in RESOURCES union TECHNOLOGIES diff STORAGE_TECH} (layers_in_out[i, l] * F_Mult_t [i, t]) 
	else
		(sum {i in RESOURCES union TECHNOLOGIES diff STORAGE_TECH} (layers_in_out[i, l] * F_Mult_t [i, t]) 
		+ sum {j in STORAGE_TECH} (Storage_Out [j, l, t] - Storage_In [j, l, t])
		- End_Uses [l, t]
		))))); 


# only the CO2_A emission from carbon-intensive fields that could be captured	
subject to co2_caputrable{t in PERIODS}:
	GWP["CO2_A",t]>=0;
subject to co2_imp{t in PERIODS}:
	GWP["CO2_EE",t]>=0;

# For avoiding F_Mult[i] tends to be a large number while all F_Mult_t[i,t] = 0
subject to f_mult_prevention{i in TECHNOLOGIES}:
	F_Mult[i]<=1000000 * sum{t in PERIODS} F_Mult_t[i,t];

## Multiplication factor

# [Eq. 1.6] min & max limit to the size of each technology
subject to size_limit {i in TECHNOLOGIES}:
	f_min [i] <= F_Mult [i] <= f_max [i];
	
# [Eq. 1.8] relation between mult_t and mult via period capacity factor. This forces max monthly output (e.g. renewables)
subject to capacity_factor_t {i in TECHNOLOGIES diff {"H2_STO","NG_STO","CO2_STO","ELEC_STO","GASO_STO","DIE_STO"}, t in PERIODS}:
	F_Mult_t [i, t] <= F_Mult [i] * c_p_t [i, t];

# X.Li
subject to capacity_factor_Sto_ng{i in {"NG_STO"}, t in PERIODS}:
	STO_NG_LEVEL[t] <= F_Mult[i];
subject to capacity_factor_Sto_co2{i in {"CO2_STO"}, t in PERIODS}:
	STO_CO2_LEVEL[t] <= F_Mult[i];
subject to capacity_factor_Sto_h2{i in {"H2_STO"}, t in PERIODS}:
	STO_H2_LEVEL[t] <= F_Mult[i];

# [Eq. 1.9] relation between mult_t and mult via yearly capacity factor. This one forces total annual output
subject to capacity_factor {i in TECHNOLOGIES}: #for ccus technology, unit: F_Mult_t: t/h
	sum {t in PERIODS} (F_Mult_t [i, t] * t_op [t]) <= F_Mult [i] * c_p [i] * total_time;	
	
# [Eq. 1.19] Operating strategy in the for decentralized heat supply: output heat in each month proportional to installed capacity (more realistic).
# Note that in Moret (2017), page 20, Eq. 1.19 is not correctly reported. In fact, if there are losses in the DHN, the concise formulation using the EndUses variable cannot be used, and should be replaced by the extended version here below.
# When solar thermal is installed, it replaces one technology which is chosen as backup. The sum of the % production of solar + backup must respect the minimum share of the backup technology
# Here written in a compact non linear form, below it is linearized  
# Linearization of Eq. 1.19
# Auxiliary variable 
var X_Solar_Backup_Aux {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, t in PERIODS} >= 0;

subject to op_strategy_decen_1_linear {i in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, t in PERIODS}:
	F_Mult_t [i, t] + X_Solar_Backup_Aux [i, t] >= sum {t2 in PERIODS} (F_Mult_t [i, t2] * t_op [t2]) * ((end_uses_input["HEAT_LOW_T_HW"] / total_time + end_uses_input["HEAT_LOW_T_SH"] * heating_month [t] / t_op [t]) / (end_uses_input["HEAT_LOW_T_HW"] + end_uses_input["HEAT_LOW_T_SH"]));

# These three constraints impose that: X_solar_backup_aux [i, t] = F_Mult_t ["DEC_SOLAR", t] * y_solar_backup [i]
# from: http://www.leandro-coelho.com/linearization-product-variables/
subject to op_strategy_decen_1_linear_1 {i in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, t in PERIODS}:
	X_Solar_Backup_Aux [i, t] <= f_max ["DEC_SOLAR"] * Y_Solar_Backup [i];

subject to op_strategy_decen_1_linear_2 {i in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, t in PERIODS}:
	X_Solar_Backup_Aux [i, t] <= F_Mult_t ["DEC_SOLAR", t];

subject to op_strategy_decen_1_linear_3 {i in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, t in PERIODS}:
	X_Solar_Backup_Aux [i, t] >= F_Mult_t ["DEC_SOLAR", t] - (1 - Y_Solar_Backup [i]) * f_max ["DEC_SOLAR"];

# [Eq. 1.20] Only one technology can be backup of solar
subject to op_strategy_decen_2:
	sum {i in TECHNOLOGIES} Y_Solar_Backup [i] <= 1;


## Resources

# [Eq. 1.12] Resources availability equation
subject to resource_availability {i in RESOURCES}:
	sum {t in PERIODS} (F_Mult_t [i, t] * t_op [t]) <= avail [i];

## Storage

# [Eq. 1.15-1.16] Each storage technology can have input/output only to certain layers. If incompatible then the variable is set to 0
# ceil (x) operator rounds a number to the highest nearest integer. 
subject to storage_layer_in {i in STORAGE_TECH, l in LAYERS, t in PERIODS}:
	Storage_In [i, l, t] * (ceil (storage_eff_in [i, l]) - 1) = 0;

subject to storage_layer_out {i in STORAGE_TECH, l in LAYERS, t in PERIODS}:
	Storage_Out [i, l, t] * (ceil (storage_eff_out [i, l]) - 1) = 0;

# [Eq. 1.17] Storage can't be a transfer unit in a given period: either output or input.
# Note that in Moret (2017), page 20, Eq. 1.17 is not correctly reported (the "<= 1" term is missing)

# Linearization of Eq. 1.17
var Y_Sto_In {STORAGE_TECH, PERIODS} binary;
var Y_Sto_Out {STORAGE_TECH, PERIODS} binary;

subject to storage_no_transfer_1 {i in STORAGE_TECH, t in PERIODS}:
	(sum {l in LAYERS: storage_eff_in [i,l] > 0} (Storage_In [i, l, t] * storage_eff_in [i, l])) * t_op [t] / f_max [i] <= Y_Sto_In [i, t];
	
subject to storage_no_transfer_2 {i in STORAGE_TECH, t in PERIODS}:
	(sum {l in LAYERS: storage_eff_out [i,l] > 0} (Storage_Out [i, l, t] / storage_eff_out [i, l])) * t_op [t] / f_max [i] <= Y_Sto_Out [i, t];

subject to storage_no_transfer_3 {i in STORAGE_TECH, t in PERIODS}:
	Y_Sto_In [i,t] + Y_Sto_Out [i,t] <= 1;

# [Eq. 1.14] The level of the storage represents the amount of energy stored at a certain time.
subject to storage_level {i in STORAGE_TECH, t in PERIODS}:
	F_Mult_t [i, t] = (if t == 1 then
	 			F_Mult_t [i, card(PERIODS)] + ((sum {l in LAYERS: storage_eff_in [i,l] > 0} (Storage_In [i, l, t] * storage_eff_in [i, l])) 
					- (sum {l in LAYERS: storage_eff_out [i,l] > 0} (Storage_Out [i, l, t] / storage_eff_out [i, l]))) * t_op [t]
	else
	 			F_Mult_t [i, t-1] + ((sum {l in LAYERS: storage_eff_in [i,l] > 0} (Storage_In [i, l, t] * storage_eff_in [i, l])) 
					- (sum {l in LAYERS: storage_eff_out [i,l] > 0} (Storage_Out [i, l, t] / storage_eff_out [i, l]))) * t_op [t]);
								
## [Eq. 1.18] Calculation of losses for each end-use demand type (normally for electricity and DHN)
subject to network_losses {i in END_USES_TYPES, t in PERIODS}:
	Losses [i,t] = (sum {j in RESOURCES union TECHNOLOGIES diff STORAGE_TECH diff (INFRASTRUCTURE_ELEC_GRID union INFRASTRUCTURE_GAS_GRID): layers_in_out [j, i] > 0} ((layers_in_out[j, i]) * F_Mult_t [j, t])) * loss_coeff [i];

## Additional constraints: Constraints needed for the application to Switzerland (not needed in standard MILP formulation)

# [Eq 1.22] Definition of min/max output of each technology as % of total output in a given layer. 
# Normally for a tech should use either f_max/f_min or f_max_%/f_min_%
subject to f_max_perc {i in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE[i]}:
	sum {t in PERIODS} (F_Mult_t [j, t] * t_op[t]) <= fmax_perc [j] * sum {j2 in TECHNOLOGIES_OF_END_USES_TYPE[i], t2 in PERIODS} (F_Mult_t [j2, t2] * t_op [t2]);

subject to f_min_perc {i in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE[i]}:
	sum {t in PERIODS} (F_Mult_t [j, t] * t_op[t])  >= fmin_perc [j] * sum {j2 in TECHNOLOGIES_OF_END_USES_TYPE[i], t2 in PERIODS} (F_Mult_t [j2, t2] * t_op [t2]);

## [Eq. 1.24] Seasonal storage in hydro dams.
# When installed power of new dams 0 -> 0.44, maximum storage capacity changes linearly 0 -> 2400 GWh/y
subject to storage_level_hydro_dams: 
	F_Mult ["HYDRO_STORAGE"]*(f_max ["NEW_HYDRO_DAM"] - f_min ["NEW_HYDRO_DAM"]) <= f_min ["HYDRO_STORAGE"] + (f_max ["HYDRO_STORAGE"] - f_min ["HYDRO_STORAGE"]) * (F_Mult ["NEW_HYDRO_DAM"] - f_min ["NEW_HYDRO_DAM"]);

# [Eq. 1.25] Hydro dams can only shift production. Efficiency is 1, "storage" is actually only avoided production shifted to different months
subject to hydro_dams_shift {t in PERIODS}: 
	Storage_In ["HYDRO_STORAGE", "ELECTRICITY_HV", t] <= (F_Mult_t ["HYDRO_DAM", t] + F_Mult_t ["NEW_HYDRO_DAM", t]);

## [Eq. 1.26] DHN: assigning a cost to the network
# Note that in Moret (2017), page 26, there is a ">=" sign instead of an "=". The two formulations are equivalent as long as the problem minimises cost and the DHN has a cost > 0
subject to extra_dhn:
	F_Mult ["DHN"] = sum {j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DHN"] diff {"DHN_RENOVATION"}} (F_Mult [j]);

# [Eq. 1.27] Calculation of max heat demand in DHN 
var Max_Heat_Demand_DHN >= 0;

subject to max_dhn_heat_demand {t in PERIODS}:
	Max_Heat_Demand_DHN >= End_Uses ["HEAT_LOW_T_DHN", t];

# Peak in DHN
subject to peak_dhn:
	sum {j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DHN"]} (F_Mult [j]) >= peak_dhn_factor * Max_Heat_Demand_DHN;


# [Eq. 1.23] Operating strategy in private mobility (to make model more realistic)
# Mobility share is fixed as constant in the different months. This constraint is needed only if c_inv = 0 for mobility.
subject to op_strategy_mob_private {i in TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_PASSENGER_LONGD"] union TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_PASSENGER_LOCAL"] union TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_FREIGHT"], t in PERIODS}:
	F_Mult_t [i, t]  >= sum {t2 in PERIODS} (F_Mult_t [i, t2] * t_op [t2] / total_time);

subject to privatemob_use_pertech1 {j in TECHNOLOGIES_OF_PRIVATEMOB_ALL_DISTANCES, t in PERIODS}: # connexion local/longd
	F_Mult_t [j,t] = sum {i in MODELS_OF_TECHNOLOGIES_OF_PRIVATEMOB_ALL_DISTANCES [j]} F_Mult_t [i,t];	
	
# Grid constraints
subject to grid_power1 {t in PERIODS, g in GRIDS}:
	F_Mult [g] >= F_Mult_t [g,t];
subject to grid_power2  {t in PERIODS, l in (ELECTRICITY_LAYERS union H2_LAYERS union NG_LAYERS), g in GRIDS_OF_LAYERS[l]}:
	F_Mult_t [g,t] >= sum {j in TECHNOLOGIES diff STORAGE_TECH: layers_in_out[j,l]>0} (F_Mult_t [j,t]*layers_in_out[j,l]) + F_Mult_t [l,t];

# Renewable penetration
subject to renw_penetratino:
	sum{i in RENEW, t in PERIODS} F_Mult_t[i,t] * t_op[t] >= renew * sum{ii in RESOURCES diff BIO_PRODUCT, tt in PERIODS} F_Mult_t[ii,tt] * t_op[tt];


## Cost

# [Eq. 1.3] Investment cost of each technology
subject to investment_cost_calc_1 {i in TECHNOLOGIES diff TECHNOLOGIES_OF_CCUS diff {"DHN_RENOVATION","DEC_RENOVATION"} diff GRIDS}:
	C_inv [i] = c_inv [i] * F_Mult [i];
subject to investment_cost_calc_2 {i in TECHNOLOGIES_OF_CCUS}:
	C_inv [i] = c_inv [i] * sum{t in PERIODS} F_Mult_t [i,t]*t_op[t];
subject to investment_cost_calc_3:
	C_inv["DHN_RENOVATION"] = c_inv["DHN_RENOVATION"] * sum{t in PERIODS} (F_Mult_t["DHN_RENOVATION",t]*t_op[t]); #MCHF/GWh
subject to investment_cost_calc_4 {i in GRIDS}:
	C_inv [i] = (F_Mult[i] - f_grid_ext[i]) * c_inv [i] * l_grid_ext[i] * k_security[i] / n_stations[i] + C_inv_grid_help [i];	
subject to op_strategy_renovation {t in PERIODS}:
	F_Mult_t ["DHN_RENOVATION", t]  >= sum {t2 in PERIODS} (F_Mult_t ["DHN_RENOVATION", t2] * t_op [t2] / total_time);
subject to investment_cost_calc_5:
	C_inv["DEC_RENOVATION"] = c_inv["DEC_RENOVATION"] * sum{t in PERIODS} (F_Mult_t["DEC_RENOVATION",t]*t_op[t]); #MCHF/GWh
subject to op_strategy_renovation_2 {t in PERIODS}:
	F_Mult_t ["DEC_RENOVATION", t]  >= sum {t2 in PERIODS} (F_Mult_t ["DEC_RENOVATION", t2] * t_op [t2] / total_time);
	
# [Eq. 1.4] O&M cost of each technology
subject to main_cost_calc {i in TECHNOLOGIES}: # add storage investment
	C_maint [i] = c_maint [i] * F_Mult [i];		

# [Eq. 1.10] Total cost of each resource
subject to op_cost_calc {i in RESOURCES}:
	C_op [i] = sum {t in PERIODS} (c_op [i,t] * F_Mult_t [i, t] * t_op [t]);


# [Eq. 1.1]	
subject to totalcost_cal:
	TotalCost = sum {i in TECHNOLOGIES union {"HYDRO_STORAGE"} diff TECHNOLOGIES_OF_CCUS} (tau [i] * C_inv [i] + C_maint [i]) 
	+ sum {k in TECHNOLOGIES_OF_CCUS} C_inv [k] + sum {j in RESOURCES} C_op [j] 
	;

## Emissions
# [Eq. 1.5]
subject to gwp_constr_calc {i in TECHNOLOGIES}:
	GWP_constr [i] = gwp_constr [i] * F_Mult [i]/lifetime[i];

# Only for saving data
subject to production{i in TECHNOLOGIES diff STORAGE_TECH, t in PERIODS}:
	Monthly_Prod[i,t]=F_Mult_t[i,t]*t_op[t];

subject to production2{i in TECHNOLOGIES diff STORAGE_TECH}:
	Annual_Prod[i]=sum{t in PERIODS} Monthly_Prod[i,t];
	
# [Eq.xl.1] in fact a storage technology corresponds to only one layer, and efficiency considered 
subject to storage{i in STORAGE_TECH, t in PERIODS}: 
	Monthly_Prod[i,t]=sum{l in LAYERS: storage_eff_out [i,l] > 0} (Storage_In[i,l,t] * storage_eff_in[i,l] - Storage_Out[i,l,t]/storage_eff_out[i,l]) * t_op[t];

subject to total_emission{t in PERIODS}:#kt
	Total_emission[t]=(GWP["CO2_A",t]+GWP["CO2_E",t]+GWP["CO2_EE",t])*t_op[t]; # Consider gwp from: CO2_A - carbon intensive sources (capturable on-site, eg: CCGT) + CO2_E - nonconcentrated sources (eg: CAR) + CO2_EE - scope 2 gwp related to imported energy carrier (eg: H2)


subject to co2_emission:
	sum{t in PERIODS} Total_emission[t] <= co2_limit;
subject to co2_emission2:
	sum{t in PERIODS} Total_emission[t] >= co2_limit_max;

subject to co2:
	TotalGWP = sum{t in PERIODS} Total_emission[t];

subject to sng_max:
	sum{i in TECHNOLOGIES diff STORAGE_TECH, t in PERIODS: layers_in_out[i,"SNG"]>0} Monthly_Prod[i,t]*layers_in_out[i,"SNG"]>=sng_min; 

### enforcing full utilization of technology based on intermittent resources once installed
subject to tech_intermittent_full_utilization{t in PERIODS, tech_inter in INTERMITTENT_TECHNOLOGIES}:
	F_Mult_t[tech_inter,t] = F_Mult[tech_inter]*c_p_t[tech_inter,t];

# TRL choice
subject to trl_choice{i in TECHNOLOGIES: trl[i]>trl_max or trl[i]<trl_min}:
	F_Mult[i]=0;

subject to bio_peneration:
	sum{t in PERIODS} (F_Mult_t["WOOD",t]+F_Mult_t["WET_BIOMASS",t])*t_op[t] >= bio_ratio*(avail["WOOD"]+avail["WET_BIOMASS"]);

# STORAGE
## NG_S level
subject to ng_storage{t in PERIODS: t > 1}:
	STO_NG_LEVEL[t]=STO_NG_LEVEL[t-1] + layers_in_out["NG_STO","NG_S"]*F_Mult_t["NG_STO",t]*t_op[t] + layers_in_out["STO_NG","NG_S"]*F_Mult_t["STO_NG",t]*t_op[t];
subject to ng_balance:
	STO_NG_LEVEL[1]=STO_NG_LEVEL[12] + layers_in_out["NG_STO","NG_S"]*F_Mult_t["NG_STO",1]*t_op[1] + layers_in_out["STO_NG","NG_S"]*F_Mult_t["STO_NG",1]*t_op[1];


var STO_IN{PERIODS} binary;
var STO_OUT{PERIODS} binary;

var HELP_STO{PERIODS}>=0;
var HELP_STO_OUT{PERIODS}>=0;

subject to bi_choice{t in PERIODS}:
	STO_IN[t]+STO_OUT[t]<=1;

## linerization
subject to in_chocie{t in PERIODS}:
	F_Mult_t["NG_STO",t]<=HELP_STO[t];
subject to aux_1{t in PERIODS}:
	HELP_STO [t] <= f_max ["NG_STO"] * STO_IN[t];
subject to aux_2{t in PERIODS}:
	HELP_STO [t] <= F_Mult_t ["NG_STO", t];
subject to aux_3{t in PERIODS}:
	HELP_STO [t] >= F_Mult_t ["NG_STO", t] - (1 - STO_IN [t]) * f_max ["NG_STO"];

subject to out_chocie{t in PERIODS}:
	F_Mult_t["STO_NG",t]<=HELP_STO_OUT[t];
subject to aux_1_out{t in PERIODS}:
	HELP_STO_OUT [t] <= f_max ["STO_NG"] * STO_OUT[t];
subject to aux_2_out{t in PERIODS}:
	HELP_STO_OUT [t] <= F_Mult_t ["STO_NG", t];
subject to aux_3_out{t in PERIODS}:
	HELP_STO_OUT [t] >= F_Mult_t ["STO_NG", t] - (1 - STO_OUT [t]) * f_max ["STO_NG"];

## CO2 Storage
subject to co2_storage{t in PERIODS: t > 1}:
	STO_CO2_LEVEL[t]=STO_CO2_LEVEL[t-1] + layers_in_out["CO2_STO","CO2_CS"]*F_Mult_t["CO2_STO",t]*t_op[t] + layers_in_out["STO_CO2","CO2_CS"]*F_Mult_t["STO_CO2",t]*t_op[t];
subject to co2_balance:
	STO_CO2_LEVEL[1]=STO_CO2_LEVEL[12] + layers_in_out["CO2_STO","CO2_CS"]*F_Mult_t["CO2_STO",1]*t_op[1] + layers_in_out["STO_CO2","CO2_CS"]*F_Mult_t["STO_CO2",1]*t_op[1];


var STO_IN_CO2{PERIODS} binary;
var STO_OUT_CO2{PERIODS} binary;

var HELP_STO_CO2{PERIODS}>=0;
var HELP_STO_OUT_CO2{PERIODS}>=0;

subject to bi_choice_co2{t in PERIODS}:
	STO_IN_CO2[t]+STO_OUT_CO2[t]<=1;

## linerization
subject to in_chocie_co2{t in PERIODS}:
	F_Mult_t["CO2_STO",t]<=HELP_STO_CO2[t];
subject to aux_1_co2{t in PERIODS}:
	HELP_STO_CO2 [t] <= f_max ["CO2_STO"] * STO_IN_CO2[t];
subject to aux_2_co2{t in PERIODS}:
	HELP_STO_CO2 [t] <= F_Mult_t ["CO2_STO", t];
subject to aux_3_co2{t in PERIODS}:
	HELP_STO_CO2 [t] >= F_Mult_t ["CO2_STO", t] - (1 - STO_IN_CO2 [t]) * f_max ["CO2_STO"];

subject to out_chocie_co2{t in PERIODS}:
	F_Mult_t["STO_CO2",t]<=HELP_STO_OUT_CO2[t];
subject to aux_1_out_co2{t in PERIODS}:
	HELP_STO_OUT_CO2[t] <= f_max ["STO_CO2"] * STO_OUT_CO2[t];
subject to aux_2_out_co2{t in PERIODS}:
	HELP_STO_OUT_CO2[t] <= F_Mult_t ["STO_CO2", t];
subject to aux_3_out_co2{t in PERIODS}:
	HELP_STO_OUT_CO2 [t] >= F_Mult_t ["STO_CO2", t] - (1 - STO_OUT_CO2 [t]) * f_max ["STO_CO2"];

## H2 Storage
subject to h2_storage{t in PERIODS: t > 1}:
	STO_H2_LEVEL[t]=STO_H2_LEVEL[t-1] + layers_in_out["H2_STO","H2_S"]*F_Mult_t["H2_STO",t]*t_op[t] + layers_in_out["STO_H2","H2_S"]*F_Mult_t["STO_H2",t]*t_op[t];
subject to h2_balance:
	STO_H2_LEVEL[1]=STO_H2_LEVEL[12] + layers_in_out["H2_STO","H2_S"]*F_Mult_t["H2_STO",1]*t_op[1] + layers_in_out["STO_H2","H2_S"]*F_Mult_t["STO_H2",1]*t_op[1];


var STO_IN_H2{PERIODS} binary;
var STO_OUT_H2{PERIODS} binary;

var HELP_STO_H2{PERIODS}>=0;
var HELP_STO_OUT_H2{PERIODS}>=0;

subject to bi_choice_h2{t in PERIODS}:
	STO_IN_H2[t]+STO_OUT_H2[t]<=1;

## linerization
subject to in_chocie_h2{t in PERIODS}:
	F_Mult_t["H2_STO",t]<=HELP_STO_H2[t];
subject to aux_1_h2{t in PERIODS}:
	HELP_STO_H2 [t] <= f_max ["H2_STO"] * STO_IN_H2[t];
subject to aux_2_h2{t in PERIODS}:
	HELP_STO_H2 [t] <= F_Mult_t ["H2_STO", t];
subject to aux_3_h2{t in PERIODS}:
	HELP_STO_H2 [t] >= F_Mult_t ["H2_STO", t] - (1 - STO_IN_H2 [t]) * f_max ["H2_STO"];

subject to out_chocie_h2{t in PERIODS}:
	F_Mult_t["STO_H2",t]<=HELP_STO_OUT_H2[t];
subject to aux_1_out_h2{t in PERIODS}:
	HELP_STO_OUT_H2[t] <= f_max ["STO_H2"] * STO_OUT_H2[t];
subject to aux_2_out_h2{t in PERIODS}:
	HELP_STO_OUT_H2[t] <= F_Mult_t ["STO_H2", t];
subject to aux_3_out_h2{t in PERIODS}:
	HELP_STO_OUT_H2 [t] >= F_Mult_t ["STO_H2", t] - (1 - STO_OUT_H2 [t]) * f_max ["STO_H2"];


## ELEC Storage

var STO_ELEC_LEVEL{PERIODS} >=0, <=0; # seasonal hydro storage

subject to capacity_factor_Sto_elec{i in {"ELEC_STO"}, t in PERIODS}:
	STO_ELEC_LEVEL[t] <= F_Mult[i];
subject to elec_storage{t in PERIODS: t > 1}:
	STO_ELEC_LEVEL[t]=STO_ELEC_LEVEL[t-1] + layers_in_out["ELEC_STO","ELEC_S"]*F_Mult_t["ELEC_STO",t]*t_op[t] + layers_in_out["STO_ELEC","ELEC_S"]*F_Mult_t["STO_ELEC",t]*t_op[t];
subject to elec_balance:
	STO_ELEC_LEVEL[1]=STO_ELEC_LEVEL[12] + layers_in_out["ELEC_STO","ELEC_S"]*F_Mult_t["ELEC_STO",1]*t_op[1] + layers_in_out["STO_ELEC","ELEC_S"]*F_Mult_t["STO_ELEC",1]*t_op[1];


var STO_IN_ELEC{PERIODS} binary;
var STO_OUT_ELEC{PERIODS} binary;

var HELP_STO_ELEC{PERIODS}>=0;
var HELP_STO_OUT_ELEC{PERIODS}>=0;

subject to bi_choice_elec{t in PERIODS}:
	STO_IN_ELEC[t]+STO_OUT_ELEC[t]<=1;

## linerization
subject to in_chocie_elec{t in PERIODS}:
	F_Mult_t["ELEC_STO",t]<=HELP_STO_ELEC[t];
subject to aux_1_elec{t in PERIODS}:
	HELP_STO_ELEC [t] <= f_max ["ELEC_STO"] * STO_IN_ELEC[t];
subject to aux_2_elec{t in PERIODS}:
	HELP_STO_ELEC [t] <= F_Mult_t ["ELEC_STO", t];
subject to aux_3_elec{t in PERIODS}:
	HELP_STO_ELEC [t] >= F_Mult_t ["ELEC_STO", t] - (1 - STO_IN_ELEC [t]) * f_max ["ELEC_STO"];

subject to out_chocie_elec{t in PERIODS}:
	F_Mult_t["STO_ELEC",t]<=HELP_STO_OUT_ELEC[t];
subject to aux_1_out_elec{t in PERIODS}:
	HELP_STO_OUT_ELEC[t] <= f_max ["STO_ELEC"] * STO_OUT_ELEC[t];
subject to aux_2_out_elec{t in PERIODS}:
	HELP_STO_OUT_ELEC[t] <= F_Mult_t ["STO_ELEC", t];
subject to aux_3_out_elec{t in PERIODS}:
	HELP_STO_OUT_ELEC [t] >= F_Mult_t ["STO_ELEC", t] - (1 - STO_OUT_ELEC [t]) * f_max ["STO_ELEC"];

# [Eq. 1.25] Hydro dams can only shift production. Efficiency is 1, "storage" is actually only avoided production shifted to different months
subject to hydro_dams_shift3 {t in PERIODS}: 
	F_Mult_t ["ELEC_STO", t] <= (F_Mult_t ["HYDRO_DAM", t] + F_Mult_t ["NEW_HYDRO_DAM", t]);



## DIE Storage

var STO_DIE_LEVEL{PERIODS} >=0, <=1000000; 

subject to capacity_factor_Sto_DIE{i in {"DIE_STO"}, t in PERIODS}:
	STO_DIE_LEVEL[t] <= F_Mult[i];
subject to DIE_storage{t in PERIODS: t > 1}:
	STO_DIE_LEVEL[t]=STO_DIE_LEVEL[t-1] + layers_in_out["DIE_STO","DIESEL_S"]*F_Mult_t["DIE_STO",t]*t_op[t] + layers_in_out["STO_DIE","DIESEL_S"]*F_Mult_t["STO_DIE",t]*t_op[t];
subject to DIE_balance:
	STO_DIE_LEVEL[1]=STO_DIE_LEVEL[12] + layers_in_out["DIE_STO","DIESEL_S"]*F_Mult_t["DIE_STO",1]*t_op[1] + layers_in_out["STO_DIE","DIESEL_S"]*F_Mult_t["STO_DIE",1]*t_op[1];


var STO_IN_DIE{PERIODS} binary;
var STO_OUT_DIE{PERIODS} binary;

var HELP_STO_DIE{PERIODS}>=0;
var HELP_STO_OUT_DIE{PERIODS}>=0;

subject to bi_choice_DIE{t in PERIODS}:
	STO_IN_DIE[t]+STO_OUT_DIE[t]<=1;

## linerization
subject to in_chocie_DIE{t in PERIODS}:
	F_Mult_t["DIE_STO",t]<=HELP_STO_DIE[t];
subject to aux_1_DIE{t in PERIODS}:
	HELP_STO_DIE [t] <= f_max ["DIE_STO"] * STO_IN_DIE[t];
subject to aux_2_DIE{t in PERIODS}:
	HELP_STO_DIE [t] <= F_Mult_t ["DIE_STO", t];
subject to aux_3_DIE{t in PERIODS}:
	HELP_STO_DIE [t] >= F_Mult_t ["DIE_STO", t] - (1 - STO_IN_DIE [t]) * f_max ["DIE_STO"];

subject to out_chocie_DIE{t in PERIODS}:
	F_Mult_t["STO_DIE",t]<=HELP_STO_OUT_DIE[t];
subject to aux_1_out_DIE{t in PERIODS}:
	HELP_STO_OUT_DIE[t] <= f_max ["STO_DIE"] * STO_OUT_DIE[t];
subject to aux_2_out_DIE{t in PERIODS}:
	HELP_STO_OUT_DIE[t] <= F_Mult_t ["STO_DIE", t];
subject to aux_3_out_DIE{t in PERIODS}:
	HELP_STO_OUT_DIE [t] >= F_Mult_t ["STO_DIE", t] - (1 - STO_OUT_DIE [t]) * f_max ["STO_DIE"];


## GASO Storage

var STO_GASO_LEVEL{PERIODS} >=0, <=100000;

subject to capacity_factor_Sto_GASO{i in {"GASO_STO"}, t in PERIODS}:
	STO_GASO_LEVEL[t] <= F_Mult[i];
subject to GASO_storage{t in PERIODS: t > 1}:
	STO_GASO_LEVEL[t]=STO_GASO_LEVEL[t-1] + layers_in_out["GASO_STO","GASOLINE_S"]*F_Mult_t["GASO_STO",t]*t_op[t] + layers_in_out["STO_GASO","GASOLINE_S"]*F_Mult_t["STO_GASO",t]*t_op[t];
subject to GASO_balance:
	STO_GASO_LEVEL[1]=STO_GASO_LEVEL[12] + layers_in_out["GASO_STO","GASOLINE_S"]*F_Mult_t["GASO_STO",1]*t_op[1] + layers_in_out["STO_GASO","GASOLINE_S"]*F_Mult_t["STO_GASO",1]*t_op[1];


var STO_IN_GASO{PERIODS} binary;
var STO_OUT_GASO{PERIODS} binary;

var HELP_STO_GASO{PERIODS}>=0;
var HELP_STO_OUT_GASO{PERIODS}>=0;

subject to bi_choice_GASO{t in PERIODS}:
	STO_IN_GASO[t]+STO_OUT_GASO[t]<=1;

## linerization
subject to in_chocie_GASO{t in PERIODS}:
	F_Mult_t["GASO_STO",t]<=HELP_STO_GASO[t];
subject to aux_1_GASO{t in PERIODS}:
	HELP_STO_GASO [t] <= f_max ["GASO_STO"] * STO_IN_GASO[t];
subject to aux_2_GASO{t in PERIODS}:
	HELP_STO_GASO [t] <= F_Mult_t ["GASO_STO", t];
subject to aux_3_GASO{t in PERIODS}:
	HELP_STO_GASO [t] >= F_Mult_t ["GASO_STO", t] - (1 - STO_IN_GASO [t]) * f_max ["GASO_STO"];

subject to out_chocie_GASO{t in PERIODS}:
	F_Mult_t["STO_GASO",t]<=HELP_STO_OUT_GASO[t];
subject to aux_1_out_GASO{t in PERIODS}:
	HELP_STO_OUT_GASO[t] <= f_max ["STO_GASO"] * STO_OUT_GASO[t];
subject to aux_2_out_GASO{t in PERIODS}:
	HELP_STO_OUT_GASO[t] <= F_Mult_t ["STO_GASO", t];
subject to aux_3_out_GASO{t in PERIODS}:
	HELP_STO_OUT_GASO [t] >= F_Mult_t ["STO_GASO", t] - (1 - STO_OUT_GASO [t]) * f_max ["STO_GASO"];


param out_max {TECHNOLOGIES} >= 0 default 10000000000; # Maximum feasible output [GWh], refers to main output. storage level [GWh] for STORAGE_TECH
param out_min {TECHNOLOGIES} >= 0 default 0; # Maximum feasible installed capacity [GWh], refers to main output. storage level [GWh] for STORAGE_TECH
subject to prod_max{i in TECHNOLOGIES diff STORAGE_TECH}:
	Annual_Prod[i]<=out_max[i];
subject to prod_min{i in TECHNOLOGIES diff STORAGE_TECH}:
	Annual_Prod[i]>=out_min[i];


# ccu constraint
subject to ccu{t in PERIODS}:
	sum{i in TECHNOLOGIES diff STORAGE_TECH diff TECHNOLOGIES_OF_CCS diff {"CO2_STO"}: layers_in_out[i,"CO2_C"]<0} -Annual_Prod[i]*layers_in_out[i,"CO2_C"] >= STO_CO2_LEVEL[t];

## Renovation limit
param reno_share_max >=0, <=1, default 0.5;
param reno_share_min >=0, <=1, default 0;
param reno_max >=0, default 30000;
param reno_min >=0, default 10000; #0

subject to renovation_max:
	Annual_Prod["DHN_RENOVATION"] + Annual_Prod["DEC_RENOVATION"]<=reno_max;
subject to renovation_min:
	Annual_Prod["DHN_RENOVATION"] + Annual_Prod["DEC_RENOVATION"]>=reno_min;


param fossil_vec_share_min default 0; # in private passenger mobility
param fossil_vec_share_max default 1;

subject to fuel_vehicle_min:
	sum{i in {"CAR_GASOLINE","CAR_DIESEL"}}Annual_Prod[i] >= fossil_vec_share_min * sum{ii in TECHNOLOGIES_OF_END_USES_TYPE["MOB_PRIVATE_LOCAL"] union TECHNOLOGIES_OF_END_USES_TYPE["MOB_PRIVATE_LONGD"]}Annual_Prod[ii];
subject to fuel_vehicle_max:
	sum{i in {"CAR_GASOLINE","CAR_DIESEL"}}Annual_Prod[i] <= fossil_vec_share_max * sum{ii in TECHNOLOGIES_OF_END_USES_TYPE["MOB_PRIVATE_LOCAL"] union TECHNOLOGIES_OF_END_USES_TYPE["MOB_PRIVATE_LONGD"]}Annual_Prod[ii];

param bus_share_min default 0; # in mobility passenger (including private and public) currently 3.3% https://www.bfs.admin.ch/bfs/en/home/statistics/mobility-transport/passenger-transport/performance.html
param bus_share_max default 1;
subject to bus1:
	sum{i in BUSES}Annual_Prod[i] >= bus_share_min * end_uses_demand_year['MOBILITY_PASSENGER_LOCAL','TRANSPORTATION'];
subject to bus2:
	sum{i in BUSES}Annual_Prod[i] <= bus_share_max * end_uses_demand_year['MOBILITY_PASSENGER_LOCAL','TRANSPORTATION'];

	
### OBJECTIVE FUNCTION ###

# Can choose between TotalGWP and TotalCost
minimize obj: TotalCost;

