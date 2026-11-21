-- County view (core sample), counties with at least {min_county_apps} applications.
SELECT a.county_fips,
       c.county_name || ', ' || c.state_code AS county,
       c.state_code,
       COUNT(*) AS applications,
       AVG(denied) AS denial_rate,
       AVG(denied) FILTER (WHERE applicant_group = 'White') AS denial_rate_white,
       AVG(denied) FILTER (WHERE applicant_group = 'Black') AS denial_rate_black,
       AVG(denied) FILTER (WHERE applicant_group = 'Hispanic') AS denial_rate_hispanic,
       COUNT(*) FILTER (WHERE applicant_group = 'Black') AS apps_black,
       COUNT(*) FILTER (WHERE applicant_group = 'Hispanic') AS apps_hispanic,
       MEDIAN(income_k) AS median_income_k,
       AVG(tract_minority_pct) AS mean_tract_minority_pct
FROM core a JOIN counties c USING (county_fips)
GROUP BY a.county_fips, c.county_name, c.state_code
HAVING COUNT(*) >= {min_county_apps}
ORDER BY applications DESC
