# motor-insurance-lakehouse
GOal - A UK motor insurance lakehouse built on Azure and Databricks using medallion architecture

Source table - Policy, Policy Holder, Product , Broker and claims and Bourdeaux

Dim Table - Dim_Policy, dim_Policy Holder, dim_Product, dim_Broker and dim_date

Fact Table - 
Fact_premium_transaction - Grain -One row per Bourdeaux line  
Fact_Policy_month - Periodic snapshot - Grain - One row per policy per month 
Fact_Claim - Accumulated snapshot - Grain - One row per claim 

Raw data count - 
{
"days": 30,
"policyholders": 20000,
"policies": 30000,
"bordereau_lines_incl_duplicates": 31924,
"distinct_bordereau_lines": 31623,
"written_premium_excl_duplicates": "22819136.94",
"claims": 853,
"claim_events": 1811,
"skewed_broker": "00007",
"unknown_broker": "00999",
"new_column_from_day": 10,
"late_file_day": 15
}
