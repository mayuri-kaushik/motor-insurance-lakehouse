Table dim_date {
  date_sk int [pk, note: 'yyyymmdd']
  full_date date
  month_sk int
  month_name varchar
  year int
  is_month_end boolean
  is_bank_holiday boolean
}
Table dim_policy {
  policy_sk bigint [pk]
  policy_number varchar
  product_code varchar
  vehicle varchar
  annual_premium decimal(18,2)
  status varchar
  start_date date
  end_date date
  effective_from timestamp
  effective_to timestamp
  is_current boolean
}
Table dim_policyholder {
  policyholder_sk bigint [pk]
  policyholder_id varchar
  full_name varchar [note: 'masked']
  date_of_birth date [note: 'masked']
  postcode varchar [note: 'masked']
  effective_from timestamp
  effective_to timestamp
  is_current boolean
}
Table dim_product {
  product_sk bigint [pk]
  product_code varchar
  product_name varchar
}
Table dim_broker {
  broker_sk bigint [pk]
  broker_code varchar
  broker_name varchar
  region varchar
  is_inferred boolean
}
Table fact_premium_transaction {
  bordereau_line_id varchar [pk]
  policy_sk bigint [ref: > dim_policy.policy_sk]
  policyholder_sk bigint [ref: > dim_policyholder.policyholder_sk]
  product_sk bigint [ref: > dim_product.product_sk]
  broker_sk bigint [ref: > dim_broker.broker_sk]
  transaction_date_sk int [ref: > dim_date.date_sk]
  transaction_type varchar
  written_premium decimal(18,2)
  ipt decimal(18,2)
  commission decimal(18,2)
}
Table fact_policy_month {
  policy_number varchar
  month_sk int
  policy_sk bigint [ref: > dim_policy.policy_sk]
  policyholder_sk bigint [ref: > dim_policyholder.policyholder_sk]
  product_sk bigint [ref: > dim_product.product_sk]
  broker_sk bigint [ref: > dim_broker.broker_sk]
  in_force_flag boolean
  exposure_days int
  earned_premium decimal(18,2)
  annual_premium_month_end decimal(18,2)
  status_month_end varchar
  indexes { (policy_number, month_sk) [pk] }
}
Table fact_claim {
  claim_number varchar [pk]
  policy_sk bigint [ref: > dim_policy.policy_sk]
  policyholder_sk bigint [ref: > dim_policyholder.policyholder_sk]
  product_sk bigint [ref: > dim_product.product_sk]
  broker_sk bigint [ref: > dim_broker.broker_sk]
  reported_date_sk int [ref: > dim_date.date_sk]
  assessed_date_sk int [ref: > dim_date.date_sk]
  first_paid_date_sk int [ref: > dim_date.date_sk]
  closed_date_sk int [ref: > dim_date.date_sk]
  claim_status varchar
  is_open boolean
  total_paid decimal(18,2)
  case_reserve decimal(18,2)
  outstanding_reserve decimal(18,2)
  incurred decimal(18,2)
  days_to_assess int
  days_to_close int
  reserve_change_count int
  last_event_ts timestamp
}
