-- Load the raw HMDA records as text (the file mixes numbers with codes such as 'NA' and 'Exempt'),
-- plus the lender names and county names used for labels.
CREATE OR REPLACE TABLE lar_raw AS
SELECT * FROM read_csv('{lar_csv}', header = true, all_varchar = true);

CREATE OR REPLACE TABLE lenders AS
SELECT DISTINCT i.lei, i.name AS lender_name
FROM (SELECT unnest(institutions) AS i FROM read_json('{filers_json}', maximum_object_size = 100000000));

CREATE OR REPLACE TABLE counties AS
SELECT STATEFP || COUNTYFP AS county_fips, STATE AS state_code, COUNTYNAME AS county_name
FROM read_csv('{county_txt}', delim = '|', header = true, all_varchar = true);
