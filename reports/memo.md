# Memo: fair-lending screen of 2025 home-purchase mortgage decisions

**To:** Chief Compliance Officer · **Data:** HMDA 2025, 3,139,327 decided home-purchase applications (core sample)

**What we found**

- **3,139,327 home-purchase applications reached a credit decision in 2025** in the core sample (first-lien, owner-occupied, site-built 1-4 unit homes; 72% of all 4,358,716 decided home-purchase applications reported under HMDA). 91.3% were approved and 8.7% denied; 2,787,322 loans closed for $1.13 trillion.
- **Black applicants were denied 2.8 times as often as White applicants** (16.9% against 6.1%); Hispanic applicants 12.8% (2.1x) and Asian applicants 9.0% (1.5x). Every group still passes the four-fifths screen on approval rates (lowest ratio 0.89, Black), because approval rates near 90% make large denial gaps look small as approval ratios. Denial-rate ratios are the better screen here.
- **Debt-to-income above 49% is close to an automatic denial for conventional loans.** The conventional denial rate is 4.6% at a reported DTI of 49% and 63.1% at 50-60% (90% above 60%), matching Fannie Mae's 50% maximum for automated underwriting; DTI is cited in 86% of those denials. FHA has no cliff at 50% (9.1% at 49%, 11.5% at 50-60%). 26% of Black and 22% of Hispanic applicants report DTI of 50% or more, against 10% of White applicants.
- **Underwriting factors explain about half of the Black-White gap.** Adding DTI, loan-to-value, income, loan size, loan type, age, sex and neighbourhood income cuts the Black-White gap from 10.4 pp to 5.8 pp (44% explained) and the Hispanic gap from 6.4 pp to 3.1 pp. Comparing applicants at the same lender in the same county leaves 4.5 pp for Black applicants (95% CI 3.9 to 5.1), 1.9 pp for Hispanic and 1.5 pp for Asian applicants. A logit model on 600,000 applications gives the same picture (Black marginal effect 5.0 pp, odds ratio 2.17).
- **The largest explained part is debt-to-income.** In the Oaxaca-Blinder decomposition it accounts for 3.8 pp of the 10.4 pp Black-White gap; debt-to-income accounts for 2.7 pp of the 6.4 pp Hispanic-White gap.
- **Credit history is the factor HMDA cannot control for.** It is cited in 28% of denials of Black applicants and 18% of denials of White applicants. The public data has no credit scores, so part of the unexplained gap may be credit differences; a lender can close this question with its own score data, the public file cannot.
- **Pricing: at the same lender in the same state, Hispanic borrowers pay 8.0 bps more (95% CI 6.1 to 9.8 bps)** than comparable White borrowers on 1,206,195 originated conventional 30-year fixed loans (rate spread over the average prime offer rate, controlling for points paid). Black borrowers pay about the same (+1.6 bps, 95% CI -1.4 to 4.6 bps); Asian borrowers pay 1.9 bps less (95% CI -3.6 to -0.1 bps).
- **Neighbourhood: applications in tracts that are 80%+ minority are denied at 13.8%** against 6.6% in tracts under 10% minority. After applicant controls and lender x state effects the difference is 0.5 pp (95% CI 0.1 to 0.9): most of the raw gap comes from who applies there, and a small part is tied to the location.
- **Lender screen: 64 of the 73 largest lenders show a Black-White denial gap whose 95% interval is above zero after controls and county effects**, and 48 show one for Hispanic applicants (median adjusted gaps 3.7 pp and 1.9 pp). These are screening results that point to files to review, not findings.
- **A 44% DTI cap would remove 769,229 approvals (33.2%) and $302.2 billion of loans,** falling on 46.7% of Black and 45.9% of Hispanic approvals against 28.5% of White approvals. The Black approval-rate ratio would fall from 0.885 to 0.660, and Black, Hispanic and Other minority applicants would fall below the four-fifths screen.

**What to do**

1. Track denial-rate ratios and adjusted gaps every quarter next to the four-fifths approval ratio, which passes for every group even though Black applicants are denied 2.8 times as often.
2. Before any guideline change, run the Excel simulator: a 44% DTI cap removes 46.7% of Black approvals and an LTV cap at 95% removes 61.8%, against 28.5% and 27.3% for White applicants. Document a business need and a less discriminatory alternative for any cap that lowers a group's ratio.
3. Offer debt-payoff and loan-size counselling at application to applicants whose DTI is just above 49%, where conventional denial rates jump; FHA is an alternative product for many of them.
4. Rerun the gap ladder on internal data with credit scores and full DTI detail. The remaining gap after scores is the figure regulators examine; the public data stops one step short of it.
5. Review pricing exceptions and lender credits for Hispanic borrowers, where the rate-spread gap remains within lender and state.
6. Use the lender screen as a peer benchmark: lenders with an interval above zero should sample denied files of comparable Black, Hispanic and White applicants for review.

**Caveats:** no credit scores in HMDA; adjusted gaps are screens, not findings; policy-cap losses are upper bounds; the revenue rate is an assumption.
