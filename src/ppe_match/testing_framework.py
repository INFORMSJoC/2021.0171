"""Module defining the class responsible for implementing the testing framework
for the PPE matching problem.
Copyright 2021 M Samorani, R Bala, R Jacob, S He
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
"""


import pandas as pd
import numpy as np
import datetime
import os

from . import strategies

import logging
logger = logging.getLogger(__name__)
stream_hdlr = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream_hdlr.setFormatter(formatter)
logger.addHandler(stream_hdlr)
logger.setLevel(logging.INFO)


class TestingFramework:
	""" Class to run the testing procedure on a given data set
	"""
	def __init__(self,
				donor_path= 'data/anon_donors.csv',
				recipient_path= 'data/anon_recipients.csv',
				distance_matrix_path= "data/anon_distance_matrix.csv",
				strategy=strategies.proximity_match_strategy,
				interval=7, max_donation_qty=1000,
				writeFiles=False, output_directory = 'output/'):
		"""Initialize the framework. 

		:param donor_path: the file name (csv) of the table D of donor requests, defaults to 'data/anon_donors.csv'
		:type donor_path: str, optional
		:param recipient_path: the file name (csv) of the table R of recipient requests, defaults to 'data/anon_recipients.csv'
		:type recipient_path: str, optional
		:param distance_matrix_path: the file name (csv) of the distance matrix M, defaults to "data/anon_distance_matrix.csv"
		:type distance_matrix_path: str, optional
		:param strategy: a function that solves the matching problem given the current donor and recipient requests, defaults to strategies.proximity_match_strategy
		:type strategy: a function with 4 inputs: current date, D^t, R^t, M, optional
		:param interval: days between subsequent solutions of the PPE matching problem, defaults to 7
		:type interval: int, optional
		:param max_donation_qty: donation requests with more than this number of units will be considered erroneous and removed, defaults to 1000
		:type max_donation_qty: int, optional
		:param writeFiles: whether to write the files of each execution, defaults to False
		:type writeFiles: bool, optional
		:param output_directory: the output directory, defaults to 'output/'
		:type output_directory: str, optional
		"""
		# Data
		dirname = os.path.dirname(__file__)
		self.all_donors = pd.read_csv(os.path.join(dirname, donor_path),parse_dates=['date'],index_col=0)
		self.all_recipients = pd.read_csv(os.path.join(dirname, recipient_path),parse_dates=['date'],index_col=0)
		self.distance_mat = pd.read_csv(os.path.join(dirname, distance_matrix_path))
		# Initialize dataframes
		self.all_granular_decisions = pd.DataFrame(columns=['don_id', 'rec_id', 'ppe','date', 'qty', 'distance', 'holding_time'])
		self.metrics = None

		# Strategy
		self.strategy = strategy
		self.interval = interval
		self.max_donation_qty = max_donation_qty
		# Misc
		self.writeFiles = writeFiles
		self.output_directory = output_directory

	# ----------------
	# Getter Functions
	# ----------------

	def get_interval(self):
		return self.interval

	def get_strategy(self):
		return self.strategy.__name__

	def get_max_donation_qty(self):
		return self.max_donation_qty


	# ----------------
	# Setter Functions
	# ----------------

	def set_interval(self, interval):
		self.interval = interval

	def set_strategy(self, strategy):
		self.strategy = strategy

	def set_max_donation_qty(self, max_donation_qty):
		self.max_donation_qty = max_donation_qty

	# -------------
	# Class Methods
	# -------------

	def get_decisions(self):
		return self.all_granular_decisions

	def get_metrics(self):
		return self.metrics

	def debug(self, bool_flag):
		if bool_flag:
			logger.setLevel(logging.DEBUG)
		else:
			logger.setLevel(logging.INFO)

	def run(self):
		if self.debug:
			logger.setLevel(10)

	# computes the metrics and return a DataFrame
	def compute_metrics(self):
		# fill rate
		donors = self.all_donors.copy()
		decisions = self.all_granular_decisions.copy()
		recipients = self.all_recipients.copy()
		recipients = recipients[recipients['qty']>0]

		all_ppes = set(donors.ppe.unique()) ##--## So we need this?
		all_ppes = all_ppes.union(set(recipients.ppe.unique()))

		# set up result DataFrame
		result = pd.DataFrame(columns=['metric_name','description','value','overall'])
		# Note: the overall column is used to sort the metrics, it will be dropped at the end

		############ FILL RATE for rec_id, ppe ############
		total_request = recipients.groupby(['rec_id','ppe'])['qty'].agg(['sum'])
		total_request =total_request.reset_index()
		total_request.columns=['rec_id','ppe','qty']
		fr = total_request.merge(decisions,how='left',on=['rec_id','ppe'],suffixes=['_rec','_dec'])\
						.groupby(['rec_id','ppe'])\
						.agg({'qty_rec':['mean'],'qty_dec':['sum','size']})
		fr = fr.reset_index()
		fr.columns = ['rec_id','ppe','requested','received','fill_rate']
		fr['fill_rate'] = fr['received'] / fr['requested']
		fr.loc[fr['fill_rate'] > 1,'fill_rate'] = 1
		fr['fill_rate'] = fr['fill_rate'].fillna(0)

		result['metric_name'] = "fill rate (" + fr['rec_id'] + "," + fr['ppe'] + ")"
		result['description'] = "fill rate of recipient " + fr['rec_id'] + " limited to " + fr['ppe']
		result['value'] = fr['fill_rate']
		result['overall'] = 0

		############ FILL RATE FOR EACH PPE ############
		fr_p = fr.groupby('ppe')['fill_rate'].mean()

		for ppe, val in fr_p.items():
			result.loc[len(result)] = [f'fill rate ({ppe})', f'average fill rate among recipients who requested {ppe}',val,0]

		fr_p_zero = fr[fr.fill_rate > 0].groupby('ppe')['fill_rate'].mean()
		fr_p_zero

		for ppe, val in fr_p_zero.items():
			result.loc[len(result)] = [f'fill rate exc zeros ({ppe})',
				f'average fill rate among recipients who requested {ppe} and received at least one unit',val,0]

		############ OVERALL FILL RATE ############
		result.loc[len(result)] = [f'fill rate', f'overall fill rate, i.e., the average of the fill rates (ppe)',fr_p.mean(),1]
		result.loc[len(result)] = [f'fill rate exc zeros', f'overall fill rate among recipients who received something, i.e., the average of the fill rates (ppe) among recipients who received at least one unit',fr_p_zero.mean(),1]

		############ UNIT_MILES ############
		decisions['unit_miles'] = decisions['distance'] * decisions['qty']

		gb = decisions.groupby('ppe')
		rr = (gb['unit_miles'].sum() / gb['qty'].sum()).to_frame().reset_index()
		rr.columns=['ppe','avg_unit_miles']

		for _, row in rr.iterrows():
			ppe = row['ppe']
			result.loc[len(result)] = [f'avg unit-miles ({ppe})', f'average miles travelled by each unit of {ppe}',row['avg_unit_miles'],0]

		overall_unit_miles = decisions.unit_miles.sum() / decisions.qty.sum()
		result.loc[len(result)] = [f'avg unit-miles', f'average miles travelled by each unit of ppe',overall_unit_miles,1]

		############ HOLDING TIME ############
		decisions['unit_holding_time'] = decisions['holding_time'] * decisions['qty']

		gb = decisions.groupby('ppe')
		rr = (gb['unit_holding_time'].sum() / gb['qty'].sum()).to_frame().reset_index()
		rr.columns=['ppe','avg_unit_days']

		for _,row in rr.iterrows():
			ppe = row['ppe']
			result.loc[len(result)] = [f'avg unit-days ({ppe})', f'average days that each unit of {ppe} stayed idle',row['avg_unit_days'],0]

		overall_holding_time = decisions.unit_holding_time.sum() / decisions.qty.sum()
		result.loc[len(result)] = [f'avg holding time', f'average days that each unit of ppe stayed idle',overall_holding_time,1]

		########## NUMBER OF SHIPMENTS ############
		total_shipments = len(decisions.groupby(['don_id','rec_id','date']).size())
		donors = decisions['don_id'].nunique()
		result.loc[len(result)] = [f'avg number of shipments', f'average number of shipments among donors',total_shipments/donors,1]

		result = result.sort_values(['overall','metric_name'])
		result.drop(columns=['overall'],inplace=True)

		self.metrics = result
		return

	def run(self):
		self.all_donors = self.all_donors[self.all_donors.qty <= self.max_donation_qty]

		cur_donors = self.all_donors.drop(index=self.all_donors.index)
		cur_recipients = self.all_recipients.drop(index=self.all_recipients.index)

		# Fetch date ranges
		cur_date = min(self.all_recipients.date.min(),
					   self.all_donors.date.min()) - datetime.timedelta(minutes=1)
		max_date = max(self.all_recipients.date.max(),
					   self.all_donors.date.max()) + datetime.timedelta(minutes=1)

		# Intialize dates
		d1 = cur_date
		d2 = cur_date + datetime.timedelta(days=self.interval)

		last_iteration = False
		while not last_iteration:
			if d2 > max_date:
				d2 = max_date + datetime.timedelta(minutes=2) ##--## Is this needed?
				last_iteration = True
			logger.info(f'===== From {d1} to {d2} ======')
			cur_recipients = pd.concat([
										cur_recipients,
										self.all_recipients.loc[(self.all_recipients.date > d1) & (self.all_recipients.date < d2)].copy()
										])
			cur_donors = pd.concat([
									cur_donors,
									self.all_donors.loc[(self.all_donors.date > d1) & (self.all_donors.date < d2)].copy()
									])

			'''
			Aggregate cur_donors and cur_recipients:
			These tables could have multiple rows for each donor (or recipient)
			for the same ppe. We need to create new dataframes with one row for
			each donor_id (or recipient_id) and ppe. We will pass these tables to
			the method strategy below
			'''
			agg_cur_donors = cur_donors.groupby(['don_id', 'ppe'])\
								.agg({'date': 'min', 'qty': 'sum'})\
								.reset_index()
			agg_cur_recipients = cur_recipients.groupby(['rec_id', 'ppe'])\
								.agg({'date': 'min', 'qty': 'sum'})\
								.reset_index()

			# for each date, write the current pending requests
			don_rec = pd.DataFrame(agg_cur_donors.merge(agg_cur_recipients, on=['ppe'])\
									.groupby(['don_id', 'rec_id']).groups.keys())
			# if there are no recipients, no donors, or no compatible pairs of donor-recipient, continue
			if len(agg_cur_recipients) == 0 or \
				len(agg_cur_donors) == 0 or \
				len(don_rec) == 0:
				d1 = d2
				d2 = d1 + datetime.timedelta(days=self.interval)
				continue

			don_rec.columns = ['don_id', 'rec_id']
			logger.debug("Donor_receipient pending requests")
			logger.debug('\n\t'+ don_rec.head().to_string().replace('\n', '\n\t'))
			logger.debug("Distance Matrix")
			logger.debug('\n\t'+ self.distance_mat.head().to_string().replace('\n', '\n\t'))
			cur_distance_mat = don_rec.merge(self.distance_mat, on=['don_id', 'rec_id'])

			if self.writeFiles:
				dir = os.path.join(self.output_directory, str(d2.date()))
				if not os.path.exists(dir):
					os.makedirs(dir)
				agg_cur_recipients.to_csv(dir + f'/recipients.csv')
				agg_cur_donors.to_csv(dir + f'/donors.csv')
				cur_distance_mat.to_csv(dir + f'/distance_matrix.csv')

			agg_decisions = self.strategy(d2, agg_cur_donors, agg_cur_recipients, cur_distance_mat)
			agg_decisions['date'] = d2
			agg_decisions = agg_decisions.merge(cur_distance_mat, on=['don_id', 'rec_id'])

			# The dataframe of agg_decisions contains the aggregated shipping decisions
			# example
			#    don_id rec_id          ppe   qty                      date     distance
			# 0   don0   rec0  faceShields  10.0 2020-04-09 16:26:00+00:00  2548.016134
			# 1   don1   rec1  faceShields   1.0 2020-04-09 16:26:00+00:00  2527.163615
			# 2   don3   rec2  faceShields   5.0 2020-04-09 16:26:00+00:00  2359.760082

			# turn it into granular decisions
			granular_decisions = pd.DataFrame(columns=[
					'don_id',
					'rec_id',
					'ppe',
					'date',
					'qty',
					'holding_time']
			)
			for _, cur_dec in agg_decisions.iterrows():
				don = cur_dec.don_id
				rec = cur_dec.rec_id
				ppe = cur_dec.ppe
				dd = cur_dec.date
				totremqty = cur_dec.qty
				don_df = cur_donors[(cur_donors.don_id == don) & \
									(cur_donors.ppe == ppe)]\
									.sort_values('date')  # just this ppe and don-rec
				rec_df = cur_recipients[(cur_recipients.rec_id == rec) & \
										(cur_recipients.ppe == ppe)]\
										.sort_values('date')

				dilocx = 0
				rilocx = 0
				while totremqty > 0:
					drow = don_df.iloc[dilocx]
					rrow = rec_df.iloc[rilocx]
					dix = drow.name
					rix = rrow.name
					shipped_qty = min(drow.qty, rrow.qty, totremqty)
					# make the granular decision of shipping
					granular_decisions.loc[len(granular_decisions)] = [
						drow.don_id, rrow.rec_id, ppe, dd, shipped_qty, np.round((dd - drow.date).total_seconds() / 24 / 3600)]

					# update quantities
					totremqty -= shipped_qty

					# update donors table
					cur_donors.loc[dix, 'qty'] -= shipped_qty
					don_df.loc[dix, 'qty'] -= shipped_qty

					# update recipient qty
					cur_recipients.loc[rix, 'qty'] -= shipped_qty
					rec_df.loc[rix, 'qty'] -= shipped_qty

					'''
					This shipping action has one of the following outcomes:
					(1) brings rrow.qty to 0,
					(2) brings drow.qty to 0,
					(3) brings neither to 0
					'''

					if rec_df.loc[rix, 'qty'] == 0:
						rilocx += 1
						if rilocx == len(rec_df) and totremqty > 0:
							# The decisions is infeasible because I am trying to
							# ship more than requested
							logger.error(
								'The decisions is infeasible because I am trying to ship more than requested')
					elif don_df.loc[dix, 'qty'] == 0:
						dilocx += 1
						if dilocx == len(don_df) and totremqty > 0:
							# The decisions is infeasible because I am trying to
							# ship more than supplied
							logger.error(
								'The decisions is infeasible because I am trying to ship more than supplied')
					else:
						# should be totremqty == 0
						if totremqty != 0:
							logger.error(
								'Weird error. If I am here, I should have totremqty == 0')

				# remove from tables those with qty == 0
				cur_donors = cur_donors.loc[cur_donors.qty > 0]
				cur_recipients = cur_recipients.loc[cur_recipients.qty > 0]

			granular_decisions = granular_decisions.merge(cur_distance_mat, on=['don_id', 'rec_id'])

			self.all_granular_decisions = pd.concat([self.all_granular_decisions, granular_decisions], ignore_index=True)
			# update decisions and save current decisions
			if self.writeFiles:
				granular_decisions.to_csv(dir + f'/decisions.csv')

			d1 = d2
			d2 = d1 + datetime.timedelta(days=self.interval)

		# save all decisions made
		if self.writeFiles:
			self.all_granular_decisions.to_csv('output/all_decisions.csv')

		# Run metrics for results
		self.compute_metrics()

		return {"status": "Success"}
