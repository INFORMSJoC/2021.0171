"""Module defining some PPE matching strategies.
Copyright 2021 M Samorani, R Bala, R Jacob, S He
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
"""

import pandas as pd
import logging
logger = logging.getLogger(__name__)
stream_hdlr = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
stream_hdlr.setFormatter(formatter)
logger.addHandler(stream_hdlr)
logger.setLevel(logging.WARN)

def FCFM_strategy(date,Dt,Rt,M):
    """simple first-come-first-matched strategy that matches the i-th donor request with the i-th recipient request for the same PPE

    :param date: the current date
    :type date: date
    :param Dt: current donor requests (don_id,date,ppe,qty)
    :type Dt: pandas.DataFrame
    :param Rt: current recipient requests (rec_id,date,ppe,qty)
    :type Rt: pandas.DataFrame
    :param M: distance matrix M
    :type M: pandas.DataFrame
    :return: the list of decisions made
    :rtype: pandas.DataFrame (don_id,rec_id,ppe,qty)
    """
    # prepare the result DataFrame (X^t)
    result = pd.DataFrame(columns=['don_id','rec_id','ppe','qty'])

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
            result.loc[len(result)] = [don.don_id,rec.rec_id,ppe,qty]
    return result


def proximity_match_strategy(date,Dt,Rt,M):
    """Proximity-matching strategy. For each ppe, match each donor with the closest recipient

    :param date: the current date
    :type date: date
    :param Dt: current donor requests (don_id,date,ppe,qty)
    :type Dt: pandas.DataFrame
    :param Rt: current recipient requests (rec_id,date,ppe,qty)
    :type Rt: pandas.DataFrame
    :param M: distance matrix M
    :type M: pandas.DataFrame
    :return: the list of decisions made
    :rtype: pandas.DataFrame (don_id,rec_id,ppe,qty)
    """
    result = pd.DataFrame(columns=['don_id','rec_id','ppe','qty'])
    ppes_to_consider = set(Dt.ppe.unique())
    ppes_to_consider = ppes_to_consider.intersection(set(Rt.ppe.unique()))

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
            result.loc[len(result),:] = [dr.don_id, dr.rec_id,ppe,qty]

    return result
