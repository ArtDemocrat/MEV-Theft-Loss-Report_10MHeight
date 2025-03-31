# MEV-Theft-Loss-Report_10MHeight
Authored by: @ArtDemocrat @ramana a.k.a. xrchz

--> This report has been produced as a result of this [Rocket Pool Grant Round 15 Request](https://dao.rocketpool.net/t/round-15-gmc-call-for-grant-applications-deadline-is-august-7/3103/2#p-9565-rocket-pool-mev-theft-and-loss-report-grant-application-1), [approved by the GMC](https://discord.com/channels/1109303903767507016/1273700317673820292/1301176881864900619) on the 30th of Octobober, 2024. 

--> It serves as a continuation of Bounty BA032304, where @ramana and @Valdorff produced the first iteration of an MEV Theft analysis for the Rocket Pool protocol in July 2023.

This repository holds all the revised documentation, scripts, and results which serve as a follow-up to the initial Rocket Pool ["MEV-Theft-Loss-Report"](https://github.com/ArtDemocrat/MEV-Theft-Loss-Report/tree/main) covering slots up to height 8.5M, conducted in March 2024. 

## Introduction & Goals
This analysis investigates the prevalence and patterns of MEV (Maximal Extractable Value) reward misappropriation within the Rocket Pool staking protocol. Specifically, it identifies and classifies block proposals where MEV rewards were potentially withheld from the intended smoothing pool recipients or diverted away from the protocol-defined fee recipients in the case of non-opted-in validator setups. The dataset covers all Ethereum slots from slot 5,203,000 to 9,899,999, applying systematic data quality checks, slot classification, and theft detection logic. The goal is to quantify and structure evidence of MEV theft behavior and its financial impact across different validator types.

During the [first research phase](https://github.com/ArtDemocrat/MEV-Theft-Loss-Report/blob/main/README.md) which @ramana and @ArtDemocrat conducted in March 2024 we were able to generate the findings which emphasized the relevance to look closer at the topic of MEV theft and loss within the Rocket Pool Protocol. However, we realized that we needed a more detailed investigation of MEV fee recipients and value by cross-referencing additional data sources and methods. For example, some of the theft findings presented in the initial report were contradictory between the sources of information we used. Therefore, upon the funding of this grant application we expand our methodology to include raw data from:
- each block’s slot (i.e. data from the chain)
- data obtained directly from relays
- beaconcha.in data (provided as a one-off pull by the beaconcha.in team at a cost of €476.00)
- @NonFungibleYokem’s mevmonitor database

As stated in the grant request, the benefits we look to generate out of this report are as follows:

- **Potential rETH holders:** rETH’s APR can be proactively protected by shedding light on this matter and acting on time. A competitive rETH EPR is essential to drive demand towards rETH.
- **rETH holders:** Same as above.
- **Potential Node Operators (NOs):** Higher staking APR by enforcing MEV relayer usage (either individually or for the entire smoothing pool NO cohort).
- **Community:** Sensitize the Rocket Pool community to the relevance of honest acting (as we observe and report misbehaviour) and to the maximization of MEV rewards for protocol competitiveness.
- **RPL holders:** See points above → demand to mint/create rETH and Rocket Pool validators → direct buying pressure (to spin-up validators) and indirect RPL buying pressure (secondary market premium = incentives to spin-up validators).

The analysis starts right after the MEV grace period ended at slot 5203679 (2022-11-24 05:35:39Z UTC; see https://discord.com/channels/405159462932971535/405163979141545995/1044108182513012796), and ends at slot 9,899,999 (2024-09-06 12:00:11Z UTC). We will name this set of datapoints "the entire distribution" in this analysis.

## Workstreams, Resources and Results
To produce this report we split the activities required between @ramana, who take are of all the data mining effort (see scripts in this repository: XXX) and @ArtDemocrat, who focused on the data analysis and insights generation (all scripts are found in this reporsitory).

### Dataset Preparation
We followed 3 data treatment steps in order to prepare the dataset for the full analysis:

📁 **CSV data extraction** from the .gz.csv compressed folders produced by @ramana as a result of the data mining effort, which were downloaded locally for processing. Script: YYY

📄 **Slot Dataset Processing & MEV Theft Flagging**: Clean, standardize, and enrich Ethereum slot-level CSV data as part of the Rocketpool MEV theft analysis project. It processes raw slot data files and produces cleaned, standardized CSV files that can be used for further analysis and visualization. Script: YYY

**What the Script Does**
- Reads raw CSV files from the SOURCE_PATH directory.
- Curates, classifies, and expands the slot information available in our datasources (see definitions in the section below).
- Exports processed data to the PROCESSED_PATH folder as new CSV files.

**Definitions Created in the Data Classification and Curation Process**
The dataset used in this analysis underwent a structured preparation and classification process to enable reliable downstream analysis. Specifically, the following data curation steps were applied:
- **Normalization of Ethereum Addresses**: All Ethereum addresses were standardized to lowercase to ensure consistency and avoid mismatches.
- **Relay Name Standardization**: Relay names were cleaned and mapped to standardized identifiers to consolidate different naming conventions used across our data sources.
- **Conversion of Values to ETH**: Key numerical fields, including transaction values, MEV rewards, and bids, originally recorded in wei units, were converted to ETH and rounded to eight decimal places.
- **Identification of Vanilla Blocks**: A classification column vanilla_block was added to flag slots without any recorded MEV rewards or fee recipients across our data sources.
- **MEV Theft Detection**: Two additional columns were created to flag slots that potentially exhibit MEV theft behavior:
  - sp_high-confidence_theft marks slots where the block proposer was part of the Rocketpool Smoothing Pool but no portion of the MEV reward was distributed to the smoothing pool contract address.
  - reg_high-confidence_theft marks slots outside the smoothing pool where the distributor address differs from all recorded MEV recipients across our data sources.
- Slot-level MEV Averaging: For contextual analysis, the average MEV bid for each slot was calculated based on two separate data sources (max_bid and mevmonitor_max_bid).
- All processed files were saved in a structured output folder and used as the standardized input for subsequent analyses (see sections below).

✅ **Slot Dataset Integrity & Quality Check**: Validate the completeness and data quality of the Ethereum slot-level dataset used in the Rocketpool MEV theft analysis project. It performs structural and continuity checks on all raw .csv files to ensure slot coverage, data quality, and integrity across millions of slot entries.

**What the Script Does**
- File Integrity: Identifies broken or unreadable files and flags files smaller than expected size.
- Slot Format Validation: Checks that all slot entries are numeric and valid, and detects non-numeric or malformed slot entries.
- Slot Range Checks: Verifies that the slot ranges in the dataset are continuous across all files, detects missing slot ranges, and detects duplicate slot entries across files.
- Detailed File Report (for each input file): Checks row count, file size, flags size anomaly, states minimum and maximum slot numbers, and counts number of non-numeric slot entries.
- Summary Report: Lists total files checked, total unique slots found, total expected slots, total missing slots, total duplicate slots, and list of broken/unreadable files (if any).

**Integrity and Data Quality Results**

📄 **Per File Report:**
| File                            | Row Count   | Size     | Size Anomaly   |   Min Slot |   Max Slot |   Non-Numeric Slots |
|---------------------------------|-------------|----------|----------------|------------|------------|---------------------|
| rt2_slot-5203000-to-5299999.csv | 97,000      | 40.83 MB | ✅ No           |    5203000 |    5299999 |                   0 |
| rt2_slot-5300000-to-5399999.csv | 100,000     | 41.84 MB | ✅ No           |    5300000 |    5399999 |                   0 |
| rt2_slot-5400000-to-5499999.csv | 100,000     | 42.22 MB | ✅ No           |    5400000 |    5499999 |                   0 |
| rt2_slot-5500000-to-5599999.csv | 100,000     | 42.24 MB | ✅ No           |    5500000 |    5599999 |                   0 |
| rt2_slot-5600000-to-5699999.csv | 100,000     | 42.36 MB | ✅ No           |    5600000 |    5699999 |                   0 |
| rt2_slot-5700000-to-5799999.csv | 100,000     | 42.99 MB | ✅ No           |    5700000 |    5799999 |                   0 |
| rt2_slot-5800000-to-5899999.csv | 100,000     | 42.65 MB | ✅ No           |    5800000 |    5899999 |                   0 |
| rt2_slot-5900000-to-5999999.csv | 100,000     | 43.37 MB | ✅ No           |    5900000 |    5999999 |                   0 |
| rt2_slot-6000000-to-6099999.csv | 100,000     | 44.41 MB | ✅ No           |    6000000 |    6099999 |                   0 |
| rt2_slot-6200000-to-6299999.csv | 100,000     | 41.61 MB | ✅ No           |    6200000 |    6299999 |                   0 |
| rt2_slot-6300000-to-6399999.csv | 100,000     | 42.77 MB | ✅ No           |    6300000 |    6399999 |                   0 |
| rt2_slot-6400000-to-6499999.csv | 100,000     | 43.06 MB | ✅ No           |    6400000 |    6499999 |                   0 |
| rt2_slot-6500000-to-6599999.csv | 100,000     | 44.13 MB | ✅ No           |    6500000 |    6599999 |                   0 |
| rt2_slot-6600000-to-6699999.csv | 100,000     | 45.62 MB | ✅ No           |    6600000 |    6699999 |                   0 |
| rt2_slot-6700000-to-6799999.csv | 100,000     | 46.25 MB | ✅ No           |    6700000 |    6799999 |                   0 |
| rt2_slot-6800000-to-6899999.csv | 100,000     | 46.94 MB | ✅ No           |    6800000 |    6899999 |                   0 |
| rt2_slot-6900000-to-6999999.csv | 100,000     | 48.28 MB | ✅ No           |    6900000 |    6999999 |                   0 |
| rt2_slot-7000000-to-7099999.csv | 100,000     | 51.88 MB | ✅ No           |    7000000 |    7099999 |                   0 |
| rt2_slot-7100000-to-7199999.csv | 100,000     | 52.54 MB | ✅ No           |    7100000 |    7199999 |                   0 |
| rt2_slot-7200000-to-7299999.csv | 100,000     | 52.68 MB | ✅ No           |    7200000 |    7299999 |                   0 |
| rt2_slot-7300000-to-7399999.csv | 100,000     | 51.27 MB | ✅ No           |    7300000 |    7399999 |                   0 |
| rt2_slot-7400000-to-7499999.csv | 100,000     | 51.25 MB | ✅ No           |    7400000 |    7499999 |                   0 |
| rt2_slot-7500000-to-7599999.csv | 100,000     | 51.10 MB | ✅ No           |    7500000 |    7599999 |                   0 |
| rt2_slot-7600000-to-7699999.csv | 100,000     | 49.63 MB | ✅ No           |    7600000 |    7699999 |                   0 |
| rt2_slot-7700000-to-7799999.csv | 100,000     | 51.91 MB | ✅ No           |    7700000 |    7799999 |                   0 |
| rt2_slot-7800000-to-7900000.csv | 100,000     | 47.70 MB | ✅ No           |    7800000 |    7899999 |                   0 |
| rt2_slot-7900000-to-8000000.csv | 100,000     | 46.36 MB | ✅ No           |    7900000 |    7999999 |                   0 |
| rt2_slot-8000000-to-8100000.csv | 100,000     | 46.13 MB | ✅ No           |    8000000 |    8099999 |                   0 |
| rt2_slot-8100000-to-8200000.csv | 100,000     | 45.91 MB | ✅ No           |    8100000 |    8199999 |                   0 |
| rt2_slot-8200000-to-8299999.csv | 100,000     | 50.01 MB | ✅ No           |    8200000 |    8299999 |                   0 |
| rt2_slot-8300000-to-8399999.csv | 100,000     | 49.97 MB | ✅ No           |    8300000 |    8399999 |                   0 |
| rt2_slot-8400000-to-8499999.csv | 100,000     | 50.00 MB | ✅ No           |    8400000 |    8499999 |                   0 |
| rt2_slot-8500000-to-8599999.csv | 100,000     | 51.65 MB | ✅ No           |    8500000 |    8599999 |                   0 |
| rt2_slot-8600000-to-8699999.csv | 100,000     | 48.46 MB | ✅ No           |    8600000 |    8699999 |                   0 |
| rt2_slot-8700000-to-8799999.csv | 100,000     | 49.85 MB | ✅ No           |    8700000 |    8799999 |                   0 |
| rt2_slot-8800000-to-8899999.csv | 100,000     | 50.54 MB | ✅ No           |    8800000 |    8899999 |                   0 |
| rt2_slot-8900000-to-8999999.csv | 100,000     | 51.60 MB | ✅ No           |    8900000 |    8999999 |                   0 |
| rt2_slot-9000000-to-9099999.csv | 100,000     | 51.07 MB | ✅ No           |    9000000 |    9099999 |                   0 |
| rt2_slot-9100000-to-9199999.csv | 100,000     | 50.63 MB | ✅ No           |    9100000 |    9199999 |                   0 |
| rt2_slot-9200000-to-9299999.csv | 100,000     | 50.10 MB | ✅ No           |    9200000 |    9299999 |                   0 |
| rt2_slot-9300000-to-9399999.csv | 100,000     | 47.49 MB | ✅ No           |    9300000 |    9399999 |                   0 |
| rt2_slot-9400000-to-9499999.csv | 100,000     | 49.81 MB | ✅ No           |    9400000 |    9499999 |                   0 |
| rt2_slot-9500000-to-9599999.csv | 100,000     | 49.86 MB | ✅ No           |    9500000 |    9599999 |                   0 |
| rt2_slot-9600000-to-9699999.csv | 100,000     | 50.99 MB | ✅ No           |    9600000 |    9699999 |                   0 |
| rt2_slot-9700000-to-9799999.csv | 100,000     | 50.94 MB | ✅ No           |    9700000 |    9799999 |                   0 |
| rt2_slot-9800000-to-9899999.csv | 100,000     | 51.00 MB | ✅ No           |    9800000 |    9899999 |                   0 |
```
📌 **Summary Report:**

🔸 Total Files Checked: 46
🔸 Broken / unreadable files: 0
🔸 Total unique slots: 4,597,000
🔸 Expected slots: 5203000 to 9899999 (4,697,000 slots)
🔸 Missing slots: 100,000
🔸 Duplicate slots across files: 0

⚠️ Missing slot range examples: [6100000, 6100001, 6100002, 6100003, 6100004] ... [6199995, 6199996, 6199997, 6199998, 6199999]
```
### Results analysis: Rocketpool vs Non-Rocketpool Maximum Bid (Ξ) Consistency Check
The first thing that we analyze is whether Rocketpool ("RP") is consistently lucky or unlucky against the non-RP Ethereum validators when it comes to the maximum bids received by ethereum relayers. The conclusion: No. As expected, RP validator's "luck" in terms of bids received (and accepted) is aligned with the non-RP validator cohort.

We confirmed this by plotting a cumulative distribution function ("CDF") for the maximum bids on all Ethereum slots (blue dots/line) and another one for RP blocks (orange dots/line). See CDF charts below. Besides doing a visual evaluation for each of the cohorts, we apply the Kolmogorov-Smirnov (K-S) statistical evaluation on the entire distribution, and on subsets of the entire distribution, in order to compare RP vs non-RP maximum bids distribution (see table below).

The Kolmogorov-Smirnov (K-S) test is a non-parametric test that compares two samples to see if they come from the same distribution. It's useful in this case because it doesn't assume any specific distribution of the data and is sensitive to differences in both location and shape of the empirical cumulative distribution functions of the two samples analyzed. The K-S test returns a D statistic and a p-value. The D statistic represents the maximum difference between the two cumulative distributions, and the p-value tells us the probability of observing the data assuming the null hypothesis (i.e. that the samples are from the same distribution) is true.

- **K-S statistic (D)**: The greater this value (closer to 1.0), the larger the maximum difference between the CDFs, suggesting a greater discrepancy between the two groups. The lower this value (closer to 0.0), the more the distributions of the two samples are similar or the same.
- **p-value**: A small p-value (typically ≤ 0.05) suggests that the samples come from different distributions. If this value is less than or equal to 0.05, the difference in distributions is considered statistically significant, meaning it's unlikely the difference is due to random chance.

#### Consistency Check - Global Conclusion (Analysis Script: YYY)
If we take a look at the entire distribution of slots which had max_bid, **we see no evidence that RP gets better or worse bids vs non-RP validators**.

Analysis for slots with MEV rewards between 10**-5 ETH and 10**5 ETH (exhaustive range):
```
Step 1: Full dataset created: 4597000 rows, 28 columns
Step 2: Dropped rows due to missed blocks (validator index empty): 42297 rows
Step 3: Dropped rows due to missing max_bid values: 154008 rows
Step 4: Dropped rows due to invalid `is_rocketpool` values: 0 rows
Step 5: Final dataset size: 4400695 rows, 29 columns
Total number of rows being plotted between 1.00e-05 ETH and 1.00e+05 ETH: 4400695
Number of 'Is RocketPool: TRUE' datapoints: 116336
Number of 'Is RocketPool: FALSE' datapoints: 4284359
✅ K-S statistic: 0.0044
✅ p-value: 2.6695e-02
```
![CDF 10^-5 - 10^5](https://github.com/user-attachments/assets/1f4d5355-0981-4f93-834f-c3443fdd7570)

#### Consistency Check - Cohort Breakdown Conclusion (Analysis Script: YYY)
If we break this analysis down to specific maximum bid ranges, we do see discrepancies between the RP and non-RP cohorts, specifically in very low and very high maximum bid ranges (where RP data becomes scarce). For the purpose of this document we will treat both datasets as similar (i.e. both RP and non-RP cohorts have the same "luck" when it comes to receiving maximum bids from Rocketpool-approved relays).

```
Step 1: Full dataset created: 4597000 rows, 28 columns
Step 2: Dropped rows with no max bid or missed blocks: 196305 rows
Step 3: Dropped rows due to invalid `is_rocketpool` values: 0 rows
Step 4: Final dataset size: 4400695 rows, 29 columns
```
| Range        |   # of Slots |   # of RP Slots |   # of non-RP Slots | K-S statistic                   | p-value                         |
|--------------|--------------|-----------------|---------------------|---------------------------------|---------------------------------|
| 0-0.01 ETH   |        15345 |             440 |               14905 | :white_check_mark: 0.0261405569 | :white_check_mark: 0.9248525964 |
| 0.01-0.1 ETH |      3263516 |           86002 |             3177514 | :white_check_mark: 0.0040425225 | :white_check_mark: 0.1291674574 |
| 0.1-1 ETH    |      1072767 |           28609 |             1044158 | :white_check_mark: 0.0042381293 | :white_check_mark: 0.6975153355 |
| 1-10 ETH     |        46765 |            1223 |               45542 | :white_check_mark: 0.0213307993 | :white_check_mark: 0.6424829761 |
| >10 ETH      |         2302 |              62 |                2240 | :warning: 0.0888680876          | :white_check_mark: 0.6930415397 |
| Total        |      4400695 |          116336 |             4284359 | :white_check_mark: 0.0043637520 | :warning: 0.0266949435          |

It is worth mentioning that the p-value test on the total dataset yields a p-value below the conventional ≤ 0.05 threshold. However, the corresponding K-S statistic is extremely small (~0.004), indicating that the difference, while statistically significant due to the large dataset size, is negligible in practical terms. Range-wise analysis shows no significant differences in most ranges.

### Results Analysis: Systematic MEV Loss
Once that we confirmed that RP validators stand on a level playing field with non-RP validators, we proceed to analyze cases of revenue loss within the RP protocol. In order to analyze MEV loss cases we define 2 types of revenue losses for the RP protocol (red arrows in the image below):

1. **MEV Theft**: the fee recipient for a block (according to either the relay's payload if mev_reward is present, or the Beacon chain otherwise) was incorrect. This happens when the fee recipient is not set to either the smoothing pool ("SP") if a node is opted-in the SP, or the node's fee recipient otherwise.

2. **Neglected Revenue**: the node proposes a vanilla block, losing profits against a scenario where an MEV-boost-optimized block (with traditionally higher MEV rewards) could have been proposed.

![RP MEV Flows](https://github.com/user-attachments/assets/dda404ad-ed26-42f9-9fd0-1ba51f607086)

#### MEV Theft Analysis Results (Analysis Script: YYY)
As explained in the "Consinstency Check - Global Conclusion" section of this report, in the time between the grace period ended, and until slot 8,499,999, 116,336 blocks were proposed by RP validators. In this section we analyze whether a RP validator behaved honestly by sending MEV rewards to the correct fee recipients defined by the protocol.

First we begin by plotting the MEV rewards of each slot where we deemed the fee recepient for a proposed block as incorrect. During the analyzed timeframe, 92 cases of MEV Theft ocurred (vs. 17 such cases identified by @ramana and @Valdorff in their [initial MEV Theft report](https://github.com/xrchz/rockettheft/blob/main/README.md#current-losses) from July 2023). If we analyze these cases we can see that the smoothing pool is slightly more affected (73 theft cases) vs non-opt-in validators (19 theft cases). This derived in a total loss of 8.37 ETH for the rocketpool protocol (vs. 2.11 ETH identified in the initial report), split as shown below:

📄 **Theft Summary:**

| Theft Type           | Total Flagged   | Reward = 0     | Reward > 0   |   Sum of MEV Reward (ETH) |   Estimated Missed Revenue (ETH) |
|----------------------|-----------------|----------------|--------------|---------------------------|----------------------------------|
| Smoothing Pool Theft | 4,222           | 4,149 (98.27%) | 73 (1.73%)   |                    6.0876 |                          364.113 |
| Regular Theft        | 3,642           | 3,623 (99.48%) | 19 (0.52%)   |                    2.2777 |                          347.465 |

As seen from the nubmers above, we identified 92 cases (73 in the smoothing pool and 19 among non-opt-in validators) where a mev_reward amount was observed in the slot and was sent to an incorrect fee recipient. Additionally, there are 4,149 cases within the smoothing pool and 3,623 cases among non-opt-in validators where even if an mev_reward was not registered for the slot (i.e. mev = 0), an incorrect usage of the fee recipient is observed. These cases sum-up to a loss/theft of 711,58 ETH if we take the max_bid data available for these slots as a proxy for the ETH which could have been stolen (i.e. a worst case scenario estimation). The MEV loss related to these slots is covered in the following section of this report ("Neglected Revenue"), since they fall under the category of "vanilla blocks" due to the absence of an MEV relayer and mev_reward for the proposed block. 

In the chart below we plot the 92 cases of theft split between smoothing pool vs the non-opt-in cases. The Y axis shows the magnitude of the 93 stolen MEV rewards (Y axis) and the slot where these took place is shown in the X axis). Theft has clearly become more prevalent towards recent slots.

![MEV Theft by SP or NonSP - timeseries](https://github.com/user-attachments/assets/72867827-c393-485c-bf12-3c1e9c9f359d)

🔍 The tables below show the entire 92 cases with slot information and theft amount (we only show theft cases with MEV Reward > 0):

🧾 Smoothing Pool Theft Events (Count: 73):
|    |    slot |   average_mev_reward |
|----|---------|----------------------|
|  0 | 6376024 |               1.6559 |
|  1 | 6394833 |               0.1999 |
|  2 | 6398416 |               0.3539 |
|  3 | 6491248 |               0.2048 |
|  4 | 6537730 |               0.0582 |
|  5 | 6639556 |               0.3182 |
|  6 | 6920241 |               0.0502 |
|  7 | 7134747 |               0.0234 |
|  8 | 7140573 |               0.0214 |
|  9 | 7227917 |               0.0196 |
| 10 | 7275407 |               0.0596 |
| 11 | 7295853 |               0.053  |
| 12 | 7472852 |               0.0166 |
| 13 | 7532202 |               0.0349 |
| 14 | 7641543 |               0.0216 |
| 15 | 7739429 |               0.0901 |
| 16 | 7839085 |               0.0302 |
| 17 | 7932761 |               0.0181 |
| 18 | 7958044 |               0.0599 |
| 19 | 8019788 |               0.0714 |
| 20 | 8041945 |               0.0322 |
| 21 | 8047532 |               0.0375 |
| 22 | 8059179 |               0.0558 |
| 23 | 8069598 |               0.0212 |
| 24 | 8082136 |               0.2121 |
| 25 | 8103837 |               0.0447 |
| 26 | 8113483 |               0.0197 |
| 27 | 8160683 |               0.0389 |
| 28 | 8165800 |               0.0408 |
| 29 | 8229595 |               0.075  |
| 30 | 8303159 |               0.0208 |
| 31 | 8312200 |               0.0896 |
| 32 | 8380987 |               0.0556 |
| 33 | 8428494 |               0.0505 |
| 34 | 8439700 |               0.0257 |
| 35 | 8449863 |               0.0563 |
| 36 | 8481111 |               0.0213 |
| 37 | 8486863 |               0.011  |
| 38 | 8490945 |               0.1304 |
| 39 | 8499982 |               0.0518 |
| 40 | 8551400 |               0.034  |
| 41 | 8563243 |               0.0962 |
| 42 | 8647603 |               0.0338 |
| 43 | 8692544 |               0.0895 |
| 44 | 8701567 |               0.0216 |
| 45 | 8716499 |               0.0583 |
| 46 | 8975549 |               0.1048 |
| 47 | 8991546 |               0.0478 |
| 48 | 9041897 |               0.0214 |
| 49 | 9093871 |               0.0395 |
| 50 | 9109741 |               0.0444 |
| 51 | 9136021 |               0.0277 |
| 52 | 9142911 |               0.0399 |
| 53 | 9153469 |               0.0677 |
| 54 | 9161679 |               0.174  |
| 55 | 9236048 |               0.1077 |
| 56 | 9251260 |               0.0678 |
| 57 | 9258038 |               0.1027 |
| 58 | 9267070 |               0.0297 |
| 59 | 9307179 |               0.0349 |
| 60 | 9317335 |               0.0185 |
| 61 | 9321100 |               0.0605 |
| 62 | 9397756 |               0.0234 |
| 63 | 9462733 |               0.0485 |
| 64 | 9506064 |               0.0107 |
| 65 | 9597084 |               0.042  |
| 66 | 9606836 |               0.0124 |
| 67 | 9685893 |               0.0253 |
| 68 | 9700692 |               0.0585 |
| 69 | 9729712 |               0.0406 |
| 70 | 9781920 |               0.0117 |
| 71 | 9850087 |               0.0112 |
| 72 | 9882372 |               0.0288 |

🧾 Regular Theft Events (Count: 19):
|    |    slot |   average_mev_reward |
|----|---------|----------------------|
|  0 | 5891799 |               0.0659 |
|  1 | 5902394 |               0.0294 |
|  2 | 5902679 |               0.5644 |
|  3 | 5907158 |               0.0516 |
|  4 | 6209610 |               0.1961 |
|  5 | 6478783 |               0.0428 |
|  6 | 6688123 |               0.0479 |
|  7 | 6821942 |               0.123  |
|  8 | 7709630 |               0.0626 |
|  9 | 7824496 |               0.2751 |
| 10 | 7961119 |               0.0239 |
| 11 | 8164529 |               0.0193 |
| 12 | 8229213 |               0.0322 |
| 13 | 8239072 |               0.0443 |
| 14 | 8475766 |               0.4655 |
| 15 | 8927672 |               0.1653 |
| 16 | 9326758 |               0.0385 |
| 17 | 9378154 |               0.0167 |
| 18 | 9845150 |               0.0133 |

📄 **Node Address Summary (MEV Reward > 0, RocketPool Slots, All Theft Types):**

|    | node_address                               |   theft_events |   total_mev_reward | % of total theft   |
|----|--------------------------------------------|----------------|--------------------|--------------------|
|  1 | 0x1A7d31ceC3EDF4b1CA4641fD66FB54f2ff5e64cA |             28 |             1.3397 | 30.43%             |
| 11 | 0x7027CEc9845E51537a73cAef3a9a3A3dbA1f531F |             16 |             0.7073 | 17.39%             |
| 20 | 0xa0AC59Fa1dFbAdA43f48454D889BE04efCADdb4B |              9 |             0.5164 | 9.78%              |
| 10 | 0x5AED3d3382993e893491D8085f2AAB00Fc8A55ae |              9 |             0.4    | 9.78%              |
| 14 | 0x8B2Efc253ece18e2d51d68771a085C14DDa26a5a |              4 |             0.7113 | 4.35%              |
|  6 | 0x4892E52502CFdD675BeE1C26F5E4b76e2Aca84ba |              3 |             0.2137 | 3.26%              |
|  8 | 0x5945459c5201e21Ff409C9608600D0c0d5f91635 |              2 |             0.119  | 2.17%              |
|  0 | 0x03d2634F6b03B24F835bE14F8807B58E6acD14cB |              2 |             0.0765 | 2.17%              |
|  5 | 0x45beA5Da5d62FB0C9E761f330E244C9C1553EB78 |              2 |             0.5181 | 2.17%              |
|  4 | 0x3badd6D42C75DE56693e8b91890755ecA52c4Efb |              2 |             0.0551 | 2.17%              |
|  3 | 0x24a9db8f232948c2f64A4BBD68AC52A2694efa9F |              2 |             0.4121 | 2.17%              |
| 22 | 0xd19400Ea9a0154193B3Fff45D8Faf45A3A516598 |              2 |             0.6308 | 2.17%              |
|  7 | 0x5008724186728Bbd5CDddafb00C08B83Be57961B |              1 |             0.0216 | 1.09%              |
|  9 | 0x5A8b39Df6f1231B5d68036c090a2C5d126eb72D2 |              1 |             0.0302 | 1.09%              |
| 12 | 0x824A06eC521aAebC057baC4e0fA205B09688Ab9D |              1 |             0.2751 | 1.09%              |
| 13 | 0x84cC6c4211D842B152f61C3929B725577c3Dc721 |              1 |             0.0558 | 1.09%              |
| 15 | 0xAAF39a9D51B27d8160FBBE24999Cc501caFa8754 |              1 |             1.6559 | 1.09%*             |
| 16 | 0xB498446d6B701407fed1F34a1A7328df3Aa32308 |              1 |             0.2048 | 1.09%              |
| 17 | 0xBfC76C6eDC762d0E2885371A8FF32776DF05B8E1 |              1 |             0.0626 | 1.09%              |
| 18 | 0xC67701C62A02D257Cb3E97FE1a76bC0090adDD1E |              1 |             0.0133 | 1.09%              |
| 19 | 0xEda174818b4Ef8E3749b5e5235141fe370F4821b |              1 |             0.1304 | 1.09%              |
|  2 | 0x1De3626d6fc2d7c14AF8020B5E8A0c3371D9195D |              1 |             0.1961 | 1.09%              |
| 21 | 0xbD5E856afFAb8BB4E3e93A69a82C97792eDE2eF0 |              1 |             0.0193 | 1.09%              |

*The largest MEV reward channeled to an incorrect fee recipient happened in slot 6376024 and was due a configuration error after a solo migration took place. The Node Operator immediately sent the correct amount to the smoothing pool (see https://etherscan.io/tx/0x18a28f9bba987a05bc87515faa6490cef3fe61b02dc45d68cffcf3a4e6f791a0).

It is worth mentioning that even though sending MEV rewards to the [rETH contract](https://etherscan.io/address/0x33894ea0C25295cB48068019d999A9E190540BF7) is not entirely according to the protocol defined rules, in 2 of the 7,864 incorrect fee recipient cases (i.e. the equivalent of 0.119 ETH) the MEV reward was sent to the rETH contract, which would technically mean that no theft happened.

#### Conclusion:
- While 92 theft cases out of 116,336 Rocketpool block proposals analyzed in this time series represent a low incidence of 0.07%, it seems that theft is a phenomenon which is happening continuously within the protocol.
- Secondly, MEV theft incidence seems to have become more prevalent in recent slots.
- Finally, if we consider not only the 92 slots where an mev_reward was observerd for the block, but rather the total (4,222+3,642)= 7,864 cases where an incorrect fee recipient was used, the theft incidence within RP climbs to 6.7%.

#### MEV Loss Analysis Results - Neglected Revenue (Script: YYY)

#### Notes on Neglected Revenue Data

#### Conclusions and Recommendations


**Authored by:**
<p align="left">
  <img width="70" height="70" src="https://github.com/ArtDemocrat/MEVLossTracker/assets/137831205/da012a89-2ec8-4e2f-bd8d-6f4b7fec0a72">
</p>

**@ArtDemocrat**

</p>
  <img width="70" height="70" src="https://github.com/ArtDemocrat/MEVLossTracker/assets/137831205/5254358c-efca-482c-b9ff-67484da15be0">
</p>
