import onix.nax as nax
import pathlib

path1 = pathlib.Path(__file__).parent.absolute() /'5MWe-reactor-simulation_output-folder'

NAX_cell = 'Sample'

burnup_list_low = [0.6, 0.23, 0.22, 0.22, 0.23]
burnup_list_high = [0.699, 0.33, 0.31, 0.31, 0.32]
burnup_mid = [(i+j)/2 for i,j in zip(burnup_list_low, burnup_list_high)]

pow_unit_cell = 6.00000E-05 #in MW)
ihm = 118.75970682995882*1E-3
 
day_list = []
for bu in burnup_mid:
	day = bu*ihm/pow_unit_cell
	day_list.append(day)

batch1 = nax.Batch(path1)

operation_history = []
for day in day_list:
	batch = (batch1, day)
	operation_history.append(batch)

nax.review_all_ratio_candidates(NAX_cell, operation_history, path1, 1E-3)