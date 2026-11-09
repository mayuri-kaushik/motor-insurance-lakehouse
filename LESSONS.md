Expected: editing the file on GitHub would update Databricks. Happened: no change. Learned: a Git folder is a clone. You pull changes in and push changes out; nothing syncs automatically. And code stored in Git does nothing until it’s executed

Schema Drift with broker code: Broker code with inferSchema = True, taking code as integer however its string. With integer in broker file so joins to the broker reference data (stored as the string "00007") silently fail, and the data is corrupted without any error.

-- -- Premium bordereaux: how many lines, how many distinct, how much premium?
select count(*) as lines, 
        count(distinct bordereau_line_id) as distinct_lines,
        sum(written_premium) as premium_incl_dupes
from read_files('/Volumes/dev_insurance/landing/raw/bordereaux/premium/', format => 'csv', header => true);

lines	distinct_lines	premium_incl_dupes
30835	30544	22251247.28000015

-- Which lines are duplicated?
SELECT bordereau_line_id, count(*) AS n
from read_files('/Volumes/dev_insurance/landing/raw/bordereaux/premium/',format => 'csv', header => true)
GROUP BY bordereau_line_id HAVING count(*) > 1
ORDER BY n DESC LIMIT 20;
bordereau_line_id	n
BL000021254	2
BL000019573	2
BL000024051	2
BL000005237	2
BL000012467	2
BL000030425	2
BL000030507	2
BL000022807	2
BL000004662	2
BL000018073	2
BL000024264	2
BL000001184	2
BL000024555	2
BL000028353	2
BL000012869	2
BL000008200	2
BL000013102	2
BL000027833	2
BL000020127	2
BL000023411	2


-- Broker skew
SELECT broker_code, count(*) AS policies,
       round(100 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM read_files('/Volumes/dev_insurance/landing/raw/policy_admin/policy/',
                format => 'csv', header => true)
GROUP BY broker_code ORDER BY policies DESC LIMIT 5;

broker_code	policies	pct
7	12724	40.3
18	891	2.8
20	838	2.7
3	829	2.6
15	808	2.6


-- Brokers in bordereaux that are NOT in reference data
SELECT DISTINCT b.broker_code
FROM read_files('/Volumes/dev_insurance/landing/raw/bordereaux/premium/',
                format => 'csv', header => true) b
LEFT ANTI JOIN read_files('/Volumes/dev_insurance/landing/raw/reference/ref_broker.csv',
                          format => 'csv', header => true) r
  ON b.broker_code = r.broker_code;

999


-- Claims events per type
SELECT event_type, count(*) AS events
FROM read_files('/Volumes/dev_insurance/landing/raw/claims/', format => 'json')
GROUP BY event_type;

event_type	events
RESERVE_CHANGE	119
PAID	142
ASSESSED	660
REPORTED	853
CLOSED	37
