-- Premium bordereaux: how many lines, how many distinct, how much premium?
select count(*) as lines, 
        count(distinct bordereau_line_id) as distinct_lines,
-- sum(CAST(written_premium AS DECIMAL(18,2))) AS premium_incl_dupes

        sum(cast(written_premium as decimal(18,2))) as premium_incl_dupes 
from read_files('/Volumes/dev_insurance/landing/raw/bordereaux/premium/', format => 'csv', header => true);

--Which lines are duplicated?
SELECT bordereau_line_id, count(*) AS n
from read_files('/Volumes/dev_insurance/landing/raw/bordereaux/premium/',format => 'csv', header => true)
GROUP BY bordereau_line_id HAVING count(*) > 1
ORDER BY n DESC LIMIT 20;

-- Broker skew
SELECT broker_code, count(*) AS policies,
       round(100 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM read_files('/Volumes/dev_insurance/landing/raw/policy_admin/policy/',
                format => 'csv', header => true)
GROUP BY broker_code ORDER BY policies DESC LIMIT 5;

-- Brokers in bordereaux that are NOT in reference data
SELECT DISTINCT b.broker_code
FROM read_files('/Volumes/dev_insurance/landing/raw/bordereaux/premium/',
                format => 'csv', header => true) b
LEFT ANTI JOIN read_files('/Volumes/dev_insurance/landing/raw/reference/ref_broker.csv',
                          format => 'csv', header => true) r
  ON b.broker_code = r.broker_code;

-- Claims events per type
SELECT event_type, count(*) AS events
FROM read_files('/Volumes/dev_insurance/landing/raw/claims/', format => 'json')
GROUP BY event_type;
