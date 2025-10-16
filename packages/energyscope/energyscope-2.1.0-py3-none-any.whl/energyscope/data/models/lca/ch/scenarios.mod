# scenarios

#let co2_limit:= 0;

#let f_min['NUCLEAR'] :=1 ;
#let f_max['DIE_STO'] := 0;
let f_max['NUCLEAR'] := 0;
#let f_max['DAC_LT'] := 0;

let avail['NG_EHP'] := 0;
let avail['ELECTRICITY_EHV'] := 0;
let avail['GASOLINE'] := 0;
let avail['DIESEL'] := 0;
let avail['LFO'] := 0;
let avail['COAL'] := 0;

let avail['ACETIC_ACID'] := 0;
let avail['ACETONE'] := 0;
let avail['BENZENE'] := 0;
let avail['ETHANE'] := 0;
let avail['ETHYLBENZENE'] := 0;
let avail['ETHYLENE'] := 0;
let avail['JETFUEL'] := 0;
let avail['METHANOL'] := 0;
let avail['ETHYLBENZENE'] := 0;

let f_max['DEC_RENOVATION'] := 0;
let f_max['DHN_RENOVATION'] := 0;
/*
param ng_limit >= 0 default 0;


subject to ng_utilization:
	 ng_limit = sum {t in PERIODS, l in {"NG_EHP","NG_HP","NG_MP","NG_LP"}, j in TECHNOLOGIES diff STORAGE_TECH: layers_in_out[j,l]>0} (F_Mult_t [j,t]*layers_in_out[j,l]*t_op[t]);
*/
/*
param hydro_potential >= 0 default 0;
subject to hydro_penetration:
	F_Mult['NEW_HYDRO_DAM'] + F_Mult['NEW_HYDRO_RIVER'] = hydro_potential;
*/
/*
param biomass_potential >= 0 default 0;
subject to biomass_penetration:
	sum {t in PERIODS, b in BIOMASS} F_Mult_t[b,t]*t_op[t] = biomass_potential;
*/