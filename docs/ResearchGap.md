# Research Gap

Existing cloud cost optimization systems mainly focus on monitoring historical cloud usage or optimizing individual cloud services. Very few solutions combine AI-powered prediction, anomaly detection, optimization recommendations, and FinOps practices into a unified framework specifically designed for MSMEs. Furthermore, many existing solutions lack proactive cost forecasting and early detection of unusual spending patterns, making it difficult for small businesses to prevent unexpected cloud expenses.

## Consolidated gap from the 15 reviewed papers

Across the 15 papers, forecasting, workload prediction, anomaly detection and optimisation are each studied in depth, but separately and mostly on simulators, traces or pricing data rather than on a customer's own billing records. None of the reviewed papers delivers forecasting, spend-anomaly detection and explained saving recommendations together in one product that a small team can deploy with managed AWS services, and none tests the anomaly detector against a simple baseline on bill data.

CloudWiseAI addresses this gap with a single deployable system built on resource-level daily billing data, an evaluation against explicit baselines (a seasonal-naive forecaster and a rolling 3-sigma detector), and recommendations whose savings assumptions are written down so they can be checked.

The per-paper gap tables are in the project report (Section 2.2).
