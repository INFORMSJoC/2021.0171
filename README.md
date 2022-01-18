# Framework for PPE Matching

## Table of Contents
  * [Overview](#overview)
    + [What is the PPE matching problem?](#what-is-the-ppe-matching-problem)
    + [Who needs to solve the PPE matching problem?](#who-needs-to-solve-the-ppe-matching-problem)
    + [What does this software package do?](#what-does-this-software-package-do)
  * [Installation](#installation)
  * [Advanced Use](#advanced-use)
  	+ [User-defined matching solution methods](#user-defined-matching-solution-methods)
	+ [Random generation of requests through bootstrapping](#random-generation-of-requests-through-bootstrapping)
* [TestingFramework Class](#testingframework-class)
    + [Parameters](#parameters)
    + [Methods](#methods)


## Overview
### What is the PPE matching problem?
The PPE Matching Problem consists of optimally matching a set of requests, D, made by donors interested in donating Personal Protective Equipment (or PPE, such as masks, gowns, gloves, etc) with a set of requests, R, made by recipients interested in receiving PPE. Requests are characterized by a timestamp (date), a type and quantity of PPE to donate or request, and a donor or recipient id. The input of the problem also includes a matrix M of distances between donors and recipients. The objectives are multiple, and include maximizing the recipients' fill rate, minimizing the total shipping distance, minimizing the holding time of PPE, and minimizing the number of shipments of each donor.   

### Who needs to solve the PPE matching problem?
During health crises like the Covid-19 pandemic, organizations such as GetUsPPE.org provide a platform that aims at connecting prospective donors of PPE to prospective recipients of PPE. Requests by donors and recipients are collected over time. Every _delta_ days, the organization solves the PPE Matching Problem, in order to direct each donor to ship a certain quantity of PPE to a given recipient.

### What does this software package do?
Our package provides an open-source framework for researchers interested in developing and testing methodologies to solve the PPE matching problem.

The user only needs to implement a function _ppestrategy(D,R,M)_, which solves the PPE matching problem. Our testing framework evaluates the performance of that user-defined solution method on real-world requests received by GetUsPPE.org in the early months of the Covid-19 pandemic (April-July 2020).

## Installation
In a virtual environment with Python 3.6+, ppe_match can be installed via pip

    pip install ppe_match

### Import the package using

    from ppe_match import TestingFramework

### Test the installation with the code snippet below

    from ppe_match import TestingFramework

	# Initialize the testing framework with default parameters
    s = TestingFramework()

    # Run the testing procedure
    s.run()

	# Retrieve the decisions made throughout the simulation
	s.get_decisions() # Pandas dataframe that can be stored

	# Retrieve the performance metrics
	s.get_metrics() # Pandas dataframe that can be stored

### Visualize the five summary metrics
The last five metrics are the average holding time, the average number of shipments per donor, the average unit-miles, the average fill rate, and the average fill rate excluding zeros.

	res = s.get_metrics()
	res.tail(5)

### Obtain a single metric
By defining a weight for each of the five summary metrics, the user can easily obtain a single metric.

	import numpy as np

	# set weights of different objectives
	avg_holding_time_weight = 1
	avg_shipments_weight = 10
	avg_unit_miles_weight = 1
	fill_rate_weight = 100
	fill_rate_0_weight = 100

	weights = np.array([avg_holding_time_weight,avg_shipments_weight,avg_unit_miles_weight,fill_rate_weight,fill_rate_0_weight])

	# retrieve the five metrics above
	metric_values = res['value'].tail(5).values

	# compute dot product
	metric_values.dot(weights)

## Advanced use
### User-defined matching solution methods

To test a new matching solution method, start by defining a function that takes as input the current date (date, a datetime object), the current donor and recipient requests (Dt and Rt), and the distance matrix between donors and recipients, M. Dt is a DataFrame with columns (don_id,date,ppe,qty), Rt is a DataFrame with columns (rec_id,date,ppe,qty), M is a DataFrame with columns (don_id,rec_id,distance). The function must return the DataFrame Xt of matching decisions (don_id, rec_id, ppe, qty).


For example, a proximity match strategy that matches each donor's request with the closest recipient's request is implemented as follows:

	import pandas as pd
	def proximity_match_strategy(date,Dt,Rt,M):
        # prepare the result DataFrame (X^t)
	    Xt = pd.DataFrame(columns=['don_id','rec_id','ppe','qty'])
	    ppes_to_consider = set(Dt.ppe.unique())
	    ppes_to_consider = ppes_to_consider.intersection(set(Rt.ppe.unique()))

	    # for each ppe to consider, match each donor request with the closest recipient request
	    for ppe in ppes_to_consider:
		donors_ppe = Dt[Dt.ppe == ppe].copy()
		recipients_ppe = Rt[Rt.ppe == ppe].copy()

		for _, drow in donors_ppe.iterrows():
		    if len(recipients_ppe) == 0:
			break # if we don't have any more recipient with this ppe, consider the next ppe

		    # find the closest recipient to drow.don_id
		    dr = M[(M.don_id == drow.don_id)].merge(recipients_ppe,on='rec_id').sort_values('distance').iloc[0]
		    dqty = drow.qty # donor's qty
		    rqty = recipients_ppe.loc[recipients_ppe.rec_id == dr.rec_id,'qty'].values[0] #recipient's qty
		    qty = min(dqty,rqty) #qty to ship
		    if qty == 0:
			logger.info('qty is zero')
		    if qty == rqty:
			recipients_ppe = recipients_ppe[recipients_ppe.rec_id !=  dr.rec_id] # remove recipient
		    else:
			recipients_ppe.loc[recipients_ppe.rec_id == dr.rec_id,'qty'] -= qty #update recipient's qty
		    Xt.loc[len(Xt),:] = [dr.don_id, dr.rec_id,ppe,qty]

	    return Xt

On the other hand, a first-come-first-matched (FCFM) strategy that matches the i-th donor's request with the i-th recipient's request is implemented as follows:

    import pandas as pd
    def FCFM_strategy(date,Dt,Rt,M):
        # prepare the result DataFrame (X^t)
        Xt = pd.DataFrame(columns=['don_id','rec_id','ppe','qty'])

        # the ppe to consider are the intersection of the PPEs in the table of current donors Dt (D^t) and the table of current recipients Rt (R^t)
        ppes_to_consider = set(Dt.ppe.unique())
        ppes_to_consider = ppes_to_consider.intersection(set(Rt.ppe.unique()))

        # for each ppe to consider, match the i-th donor request with the i-th recipient request
        for ppe in ppes_to_consider:
            donors_ppe = Dt[Dt.ppe == ppe]
            recipients_ppe = Rt[Rt.ppe == ppe]

            n = min(len(donors_ppe),len(recipients_ppe))
            for i in range(n):
                don = donors_ppe.iloc[i]
                rec = recipients_ppe.iloc[i]
                qty = min(don.qty,rec.qty)

                # add
                Xt.loc[len(Xt)] = [don.don_id,rec.rec_id,ppe,qty]
        return Xt



Once you have implemented your own matching strategy (let us call it _my_strategy_), run the test on the GetUsPPE.org data set by passing the function to the TestingFramework constructor:

    s = TestingFramework(strategy=my_strategy)

The ppe_match package contains the implementation of two strategies illustrated above: the first-come-first-matched strategy (strategies.FCFM_strategy) and the "proximity matching" strategy tested by Bala et al. (2021) (strategies.proximity_match_strategy).

### Random generation of requests through bootstrapping
Users interested in embedding our framework in a simulation procedure may be interested in generating random variations of our data set, in order to test their code on multiple data sets. To that end, the code below implements a "bootstrap" procedure that randomly reorders the actual donor (recipient) requests by reassigning to each donor (recipient) request the timestamp of another random donor (recipient) request. In other words, in each bootstrap execution, the same recipients (and donors) make exactly the same requests as in the original data, but they make them in a different order every time. The function <i>generate_data_for_bootstrap</i> takes as input the donor and recipient requests and two random seeds for the reordering. It returns two new donor and recipient requests as pandas DataFrames.

	import pandas as pd
	def generate_data_for_bootstrap(donor_path,recipient_path,random_seed_donors,random_seed_recipients):
		"""function that generates a donor table and a recipient table through resampling

		:param donor_path: the path of the original donor table
		:type date: str
		:param recipient_path: the path of the original recipient table
		:type date: str
		:param random_seed_donors: random seed for the resampling of donor requests
		:param random_seed_recipients: random seed for the resampling of recipient requests
		:return: two DataFrames D2 and R2: the new donor requests and the new recipient requests
		"""
		
		D = pd.read_csv(donor_path,index_col=0)
		R = pd.read_csv(recipient_path,index_col=0)
		
		# donors
		D = D.reset_index().drop(columns=['index'])
		date = D.date.copy()
		D2 = D.sample(frac=1,random_state=random_seed_donors).reset_index().drop(columns=['index'])
		D2['date'] = date
		
		# recipients
		R = R.reset_index().drop(columns=['index'])
		date = R.date.copy()
		R2 = R.sample(frac=1,random_state=random_seed_recipients).reset_index().drop(columns=['index'])
		R2['date'] = date
		
		return D2,R2

The next code shows how to use the function above to run the testing procedure on randomly generated data.

	import os
	from ppe_match import TestingFramework

	D2,R2 = generate_data_for_bootstrap('anon_donors.csv','anon_recipients.csv',1,2)
	D2.to_csv('anon_donors_2.csv')
	R2.to_csv('anon_recipients_2.csv')

	# Initiate the testing framework with default parameters
	s = TestingFramework(donor_path = os.path.join(os.getcwd(),'anon_donors_2.csv'),recipient_path=os.path.join(os.getcwd(),'anon_recipients_2.csv'))

	# Run the testing procedure
	s.run()

	# Retrieve the decisions made throughout the simulation
	s.get_decisions() # Pandas dataframe that can be stored

	# Retrieve the performance metrics
	s.get_metrics() # Pandas dataframe that can be stored


## TestingFramework Class

### Parameters
#### donor_path
Path to the data set containing the donors' requests. See expected format in the data folder.

Expected input type: csv

*Default: anon_donors.csv (which is the anonymized table of donors' requests from GetUsPPE.org)*

---
#### recipient_path
Path to the data set containing the recipients' requests. See expected format in the data folder.

Expected input type: csv

*Default: anon_recipients.csv (which is the anonymized table of recipients' requests from GetUsPPE.org)*


---
#### distance_matrix_path
Path to distance matrix between donors and recipients. See expected format in the data folder.

Expected input type: csv

*Default: anon_distance_matrix.csv (which is the anonymized distance matrix from GetUsPPE.org)*

---
#### strategy
User defined strategy to allocate PPE
The function must have the following arguments:

    ppestrategy(date, Dt,Rt,M)

where,

- `date` is a datetime with the current date
- `Dt` is a pandas.DataFrame object whose rows contain the current donor requests
- `Rt` is a pandas.DataFrame object whose rows contain the current recipient requests
- `M` is a pandas.DataFrameobject that reports the distance between each donor and each recipient.

*Default: proximity_match_strategy*

###### Returns:
pd.dataframe of decisions with columns (don_id, rec_id, ppe, qty). Each row represents the decision of shipping from donor _don_id_ to recipient _rec_id_ _qty_ units of PPE of type _ppe_.


---
#### interval
Day Interval set for framework to iterate over.
*Default: 7 (days)*

---
#### max_donation_qty
Maximum quantity limit for donor to donate (helps filter out dummy entries or test entries)
*Default: 1000 (ppe units)*

---
#### writeFiles
Boolean flag to save intermediate input objects (donors, recipients, and distances) and outputs (decisions) as csv
*Default: False*

If set to *True* intermediate data will be saved for every iteration as follows:
```
output
├── 2020-04-09
	 ├── decisions.csv
	 ├── distance_matrix.csv
	 ├── donors.csv
	 └── recipients.csv
├── 2020-04-16
	 ├── decisions.csv
	 ├── distance_matrix.csv
	 ├── donors.csv
	 └── recipients.csv
├── ...
```
---
#### output_directory
Sets the directory where the intermediate files and results will be saved
*Default: output/*

---


### Methods

#### run()
Tests a strategy function by simulating the arrival of the requests given in the input data

---
#### get_decisions()
Returns the list of all matching decisions made during the test.

---
#### get_metrics()
Returns the performance metrics described in Section 4 of the research article. The metrics are reported at the PPE level, the recipient level, and the "overall" level (see Section 4). The "overall" metrics are at the bottom of the DataFrame.

---
#### debug(bool_flag)
Sets the logging level to DEBUG if *True*
*Default: False (Loglevel sets to WARN)*

---
