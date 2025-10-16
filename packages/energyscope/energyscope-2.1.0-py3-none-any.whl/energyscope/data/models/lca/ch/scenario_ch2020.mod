###################################
# Switzerland 2020
###################################
let co2_limit := 1e9;
let avail['GASOLINE'] := 1e9;
let avail['DIESEL'] := 1e9;
let avail['NG_EHP'] := 1e9;
let avail['ELECTRICITY_EHV'] := 1e9;
let avail['COAL'] := 1e9;
let avail['WASTE'] := 1e12;
let avail['LFO'] := 1e9;
let avail['WOOD'] := 1e9;
let f_max['H2_COMP_LM'] := 0;
let co2_limit:= 1e6;
let f_max['NUCLEAR'] := 20;

let f_max['DEC_RENOVATION'] := 0;
let f_max['DHN_RENOVATION'] := 0;

let share_heat_dhn_min := 0;

let f_max['DEC_THHP_GAS'] := 0 ; # 

subject to ch2020_gasoline:
	sum {t in PERIODS} F_Mult_t['GASOLINE',t]*t_op[t] >= 23910;

subject to ch2020_diesel:	
	sum {t in PERIODS} F_Mult_t['DIESEL',t]*t_op[t] >= 30550;

subject to ch2020_NG:	
	sum {t in PERIODS} F_Mult_t['NG_EHP',t]*t_op[t] >= 31350;

subject to ch2020_elec:	
	sum {t in PERIODS} F_Mult_t['ELECTRICITY_EHV',t]*t_op[t] >= 26990;

subject to ch2020_coal:	
	sum {t in PERIODS} F_Mult_t['COAL',t]*t_op[t] >= 1020;

#subject to ch2020_Solar:	
#	sum {t in PERIODS} F_Mult_t['PV',t]*t_op[t] = 2599;

#subject to ch2020_Wind:	
#	sum {t in PERIODS} F_Mult_t['WIND',t]*t_op[t] = 140;

#subject to ch2020_geothermal:	
#	sum {t in PERIODS} F_Mult_t['RES_GEO',t]*t_op[t] = 5;

#subject to ch2020_waste:	
#	sum {t in PERIODS} F_Mult_t['WASTE',t]*t_op[t] >= 1840;

#subject to ch2020_lfo:	
#	sum {t in PERIODS} F_Mult_t['LFO',t]*t_op[t] >= 28090;

#subject to ch2020_wood:	
#	sum {t in PERIODS} F_Mult_t['WOOD',t]*t_op[t] >= 10970;

#subject to ch2020_nuclear:	
#	sum {t in PERIODS} F_Mult_t['NUCLEAR',t]*t_op[t] >= 22990;

#let {g in {"EHV_GRID","HV_GRID","MV_GRID","LV_GRID"}} f_grid_ext[g] := 6;
#let {g in {"EHP_NG_GRID","HP_NG_GRID","MP_NG_GRID","LP_NG_GRID"}} f_grid_ext[g] := 8;
#let {g in {"EHP_H2_GRID","HP_H2_GRID","MP_H2_GRID","LP_H2_GRID"}} f_grid_ext[g] := 0;

let f_min['CAR_DIESEL'] := 5.11381;
let f_min['CAR_GASOLINE'] := 5.52793;

let f_max['DHN_BOILER_WOOD'] := 0.000393082;
let f_max['DHN_HP_ELEC'] := 0.00408556;
let f_max['DHN_BOILER_OIL'] := 0.008;
let f_max['AN_DIG'] := 0.0376712;
let f_max['SNG_NG'] := 0.0376712;
let f_max['DEC_COGEN_GAS'] := 0.0400545;
let f_max['DHN_COGEN_WOOD'] := 0.045;
let f_max['WIND'] := 0.0752;
let f_max['IND_BOILER_COAL'] := 0.123;
let f_max['CAR_HEV'] := 0.147687;
let f_max['CAR_BEV_LOWRANGE'] := 0.150789*0.4;
let f_max['CAR_BEV_MEDRANGE'] := 0.150789*0.6;
let f_max['DHN_COGEN_GAS'] := 0.16;
let f_max['DHN_BOILER_GAS'] := 0.19;

let f_max['TRAMWAY'] := 0.192031;
let f_max['IND_COGEN_WASTE'] := 0.271287;
#let f_max['ELEC_STO'] := 0.294322;
let f_max['IND_BOILER_WASTE'] := 0.315;
let f_max['IND_BOILER_OIL'] := 0.32;
let f_max['COACH_DIESEL'] := 0.352057;
let f_max['CAR_NG'] := 0.420341;

#let f_max['TRAIN_FREIGHT'] := 0.542021;
let f_max['DHN_COGEN_WASTE'] := 0.547945;
let f_max['IND_DIRECT_ELEC'] := 0.900053;
let f_max['DHN'] := 0.955424;
let f_max['EFFICIENCY'] := 0.970874;
#let f_max['CEMENT'] := 1;
#let f_max['GRID'] := 1.14089;
let f_max['DEC_SOLAR'] := 1.2;
let f_max['IND_BOILER_GAS'] := 1.3;
let f_max['PV'] := 2.1;

#let f_max['TRUCK'] := 2.64634;
let f_max['TRAIN_ELEC'] := 2.65643;
let f_max['DEC_BOILER_WOOD'] := 2.83986;
let f_max['DEC_DIRECT_ELEC'] := 3.3;
let f_max['NUCLEAR'] := 3.333;
#let f_max['HYDRO_RIVER'] := 4.16;
let f_max['DEC_HP_ELEC'] := 4.4;
/*
let f_max['CAR_DIESEL'] := 5.11381;
let f_max['CAR_GASOLINE'] := 5.52793;
*/
let f_max['DEC_BOILER_GAS'] := 7.24185;
#let f_max['HYDRO_DAM'] := 8.223;
let f_max['DEC_BOILER_OIL'] := 10.7586;

let f_min['DHN_BOILER_WOOD'] := 0.000393082;
let f_min['DHN_HP_ELEC'] := 0.00408556;
let f_min['DHN_BOILER_OIL'] := 0.008;
let f_min['AN_DIG'] := 0.0376712;
let f_min['SNG_NG'] := 0.0376712;
let f_min['DEC_COGEN_GAS'] := 0.0400545;
let f_min['DHN_COGEN_WOOD'] := 0.045;
let f_min['WIND'] := 0.0752;
let f_min['IND_BOILER_COAL'] := 0.123;
let f_min['CAR_HEV'] := 0.147687;
let f_min['CAR_BEV_LOWRANGE'] := 0.150789*0.4;
let f_min['CAR_BEV_MEDRANGE'] := 0.150789*0.6;
let f_min['DHN_COGEN_GAS'] := 0.16;
let f_min['DHN_BOILER_GAS'] := 0.19;

let f_min['TRAMWAY'] := 0.192031;
let f_min['IND_COGEN_WASTE'] := 0.271287;
#let f_min['ELEC_STO'] := 0.294322;
let f_min['IND_BOILER_WASTE'] := 0.315;
let f_min['IND_BOILER_OIL'] := 0.32;
let f_min['COACH_DIESEL'] := 0.352057;
let f_min['CAR_NG'] := 0.420341;

#let f_min['TRAIN_FREIGHT'] := 0.542021;
let f_min['DHN_COGEN_WASTE'] := 0.547945;
let f_min['IND_DIRECT_ELEC'] := 0.900053;
let f_min['DHN'] := 0.955424;
let f_min['EFFICIENCY'] := 0.970874;
#let f_min['CEMENT'] := 1;
#let f_min['GRID'] := 1.14089;
let f_min['DEC_SOLAR'] := 1.2;
let f_min['IND_BOILER_GAS'] := 1.3;
let f_min['PV'] := 2.1;

#let f_min['TRUCK'] := 2.64634;
let f_min['TRAIN_ELEC'] := 2.65643;
let f_min['DEC_BOILER_WOOD'] := 2.83986;
let f_min['DEC_DIRECT_ELEC'] := 3.3;
let f_min['NUCLEAR'] := 3.333;
#let f_min['HYDRO_RIVER'] := 4.16;
let f_min['DEC_HP_ELEC'] := 4.4;
/*l
let f_min['CAR_DIESEL'] := 5.11381;
let f_min['CAR_GASOLINE'] := 5.52793;
*/
let f_min['DEC_BOILER_GAS'] := 7.24185;
#let f_min['HYDRO_DAM'] := 8.223;
let f_min['DEC_BOILER_OIL'] := 10.7586;

let f_max['TRAIN_FREIGHT_DIESEL'] := 0;
let f_max['TRAIN_DIESEL'] := 0;
let f_max['TRAIN_NG'] := 0;
/*
let {g in GRIDS} f_grid_ext[g] := 0;
param f_mult_grid_elec {PERIODS} >= 0;

let f_mult_grid_elec[1] := 5890;
let f_mult_grid_elec[2] := 5257;
let f_mult_grid_elec[3] := 4922;
let f_mult_grid_elec[4] := 4241;
let f_mult_grid_elec[5] := 4117;
let f_mult_grid_elec[6] := 4074;
let f_mult_grid_elec[7] := 3787;
let f_mult_grid_elec[8] := 4193;
let f_mult_grid_elec[9] := 4465;
let f_mult_grid_elec[10] := 4864;
let f_mult_grid_elec[11] := 5410;
let f_mult_grid_elec[12] := 5915;

subject to F_Mult_grid_constraint {t in PERIODS}:
	F_Mult_t['EHV_GRID',t]*n_stations['EHV_GRID'] + F_Mult_t['HV_GRID',t]*n_stations['HV_GRID'] = f_mult_grid_elec[t]/1000;

subject to F_Mult_grid_constraint2 {t in PERIODS}:
	F_Mult_t['MV_GRID',t]*n_stations['MV_GRID'] + F_Mult_t['LV_GRID',t]*n_stations['LV_GRID'] >= f_mult_grid_elec[t]/1000;

param  f_mult_grid_ng {PERIODS} >= 0;

let f_mult_grid_ng[1] := 7891;
let f_mult_grid_ng[2] := 6510;
let f_mult_grid_ng[3] := 5179;
let f_mult_grid_ng[4] := 4046;
let f_mult_grid_ng[5] := 3573;
let f_mult_grid_ng[6] := 1653;
let f_mult_grid_ng[7] := 1344;
let f_mult_grid_ng[8] := 1497;
let f_mult_grid_ng[9] := 2140;
let f_mult_grid_ng[10] := 3554;
let f_mult_grid_ng[11] := 5954;
let f_mult_grid_ng[12] := 6647;

subject to F_Mult_grid_constraint_ng {t in PERIODS}:
	F_Mult_t['EHP_NG_GRID',t]*n_stations['EHP_NG_GRID']  = f_mult_grid_ng[t]/1000;

subject to F_Mult_grid_constraint_ng2 {t in PERIODS}:
	F_Mult_t['MP_NG_GRID',t]*n_stations['MP_NG_GRID'] + F_Mult_t['LP_NG_GRID',t]*n_stations['LP_NG_GRID'] + F_Mult_t['HP_NG_GRID',t]*n_stations['HP_NG_GRID'] <= f_mult_grid_ng[t]/1000;
	*/


minimize obj: TotalCost;