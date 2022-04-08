# Data Files

Our  data  set  was  built  by  collecting  and  anonymizing  the  requests  (from  both  donors and  recipients)  received  on  the  GetUsPPE.org  platform  during  the  first  few  months  of the Covid-19 pandemic (Apr-July 2020). It includes requests by prospective donors and recipients interested in respectively donating and receiving certain types of PPEs. The data is anonymized to ensure that donors and recipients cannot be identified. The data set and the anonymization procedure are described in the research article.

## anon_donors.csv:
This is the anonymized donors' file. Each row represents a request received by GetUsPPE.org made by a donor interested in donating PPE. The columns are:
- don_id - Unique ID for Donor *(type:str)*
- date - Datetime of Request *(type:datetime)*
- ppe - Type of PPE *(type:str)*
- qty - Number of PPEs Supplied *(type:int/float)*


#### First few rows of anon_donors.csv:
don_id|date|ppe|qty
|--|--|--|--
don0|2020-03-27 11:47:00+00:00|respirators|20.0
don238|2020-04-09 13:08:00+00:00|printedFaceShields|10.0
don250|2020-04-09 13:36:00+00:00|printedFaceShields|1.0
don157|2020-04-09 13:53:00+00:00|printedFaceShields|3000.0
don156|2020-04-09 14:24:00+00:00|printedFaceShields|5.0

## anon_recipients.csv:
This is the anonymized recipients' file. Each row represents a request received by GetUsPPE.org made by a recipient interested in receiving PPE. The columns are:
- rec_id - Unique ID for Donor *(type:str)*
- date - Datetime of Request *(type:datetime)*
- ppe - Type of PPE *(type:str)*
- qty - Number of PPEs Needed *(type:int/float)*


#### First few rows of anon_recipients.csv:
rec_id|date|ppe|qty
|--|--|--|--
rec0|2020-04-02 16:27:00+00:00|faceShields|5000.0
rec0|2020-04-02 16:27:00+00:00|nitrileGloves|10000.0
rec0|2020-04-02 16:27:00+00:00|respirators|10000.0
rec0|2020-04-02 16:27:00+00:00|gowns|1000.0
rec1|2020-04-02 16:35:00+00:00|faceShields|9.0

## anon_distance_matrix.csv
Distance, in miles, between pairs of donor and recipients. (donor, recipient) pairs with no PPE type in common are excluded.

#### First few rows of anon_distance_matrix.csv:
don_id|rec_id|distance
|--|--|--
don1092|rec5230|333.2700
don1331|rec3373|2460.7800
don1331|rec3217|2388.4240
don1331|rec6036|2116.7925
don1331|rec897|2503.2615
