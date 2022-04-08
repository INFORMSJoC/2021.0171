
import pandas as pd
import ppe_match as pp
import os

# TODO: set the data_directory variable as the directory containing the tables (Table1.csv, Table2.csv, etc)
data_directory = os.path.join(os.getcwd(), 'test_data')
 
try:
	test_rec = f'{data_directory}/Table1.csv'
	test_don = f'{data_directory}/Table2.csv'
	test_distance = f'{data_directory}/Table3.csv'
	table4 = pd.read_csv(f'{data_directory}/Table4.csv',parse_dates=['date'])
except:
	print(f'===========================\nERROR:\nError reading the content of directory {data_directory}. Make sure that this directory exists and contains files Table1.csv, Table2.csv, Table3.csv, and Table4.csv\n==========================')
	exit(1)

# This matching strategy makes the decisions contained in Table4.csv  
def test_strategy(date,curdon,currec,curdistance_mat):
	decisions_to_make = table4[(table4.date - date).astype('timedelta64[m]').abs() < 10]
	return decisions_to_make[['don_id','rec_id','ppe','qty']].copy()

# check every day if there is a matching decision to make
delta = 1

s = pp.TestingFramework(test_don,test_rec,test_distance,strategy=test_strategy,interval=1)

# Set debug as True to monitor logs
s.debug(True)

# Run the simulation on the Section 3 data set
s.run()


print('\n\n============================================\nThe following metrics should be the same as those in the yellow cells in \"tests solved manually.xlsx\"\n============================================\n')


# Check outputs
result = s.get_metrics()
print(result)

try:
	result.to_csv('..\\results\\section3_test_results.csv')
except:
	print(f'===========================\nError saving the metrics above to file. Please verify path in the code\n==========================')

