// Placeholder data used only until the backend endpoints are live.
// Each context tries the real API first and falls back to this shape on failure,
// so the UI keeps working while the FastAPI backend is being built.

export const mockCostSummary = {
  totalCost: 18420.55,
  forecastedCost: 21100.0,
  potentialSavings: 3240.8,
  anomalyCount: 4,
  monthOverMonthChange: 8.4,
};

export const mockCostTrend = [
  { date: '2026-08-20', cost: 540 },
  { date: '2026-08-21', cost: 610 },
  { date: '2026-08-22', cost: 585 },
  { date: '2026-08-23', cost: 640 },
  { date: '2026-08-24', cost: 720 },
  { date: '2026-08-25', cost: 690 },
  { date: '2026-08-26', cost: 710 },
  { date: '2026-08-27', cost: 655 },
  { date: '2026-08-28', cost: 780 },
  { date: '2026-08-29', cost: 820 },
  { date: '2026-08-30', cost: 795 },
  { date: '2026-08-31', cost: 860 },
  { date: '2026-09-01', cost: 910 },
  { date: '2026-09-02', cost: 875 },
];

export const mockServiceBreakdown = [
  { service: 'EC2', cost: 6820.4, percent: 37, color: '#22d3ee' },
  { service: 'S3', cost: 3120.1, percent: 17, color: '#3b82f6' },
  { service: 'RDS', cost: 2760.9, percent: 15, color: '#8b5cf6' },
  { service: 'Lambda', cost: 1940.2, percent: 11, color: '#10b981' },
  { service: 'CloudFront', cost: 1580.0, percent: 9, color: '#f59e0b' },
  { service: 'Other', cost: 2198.95, percent: 11, color: '#4b5768' },
];

export const mockPredictions = {
  historical: [
    { month: 'Apr', cost: 14200 },
    { month: 'May', cost: 15100 },
    { month: 'Jun', cost: 15800 },
    { month: 'Jul', cost: 16950 },
    { month: 'Aug', cost: 18420 },
  ],
  forecast: [
    { month: 'Sep', cost: 19800, confidence: 0.86 },
    { month: 'Oct', cost: 21100, confidence: 0.81 },
    { month: 'Nov', cost: 22400, confidence: 0.74 },
  ],
};

export const mockAnomalies = [
  {
    id: 'an-1',
    service: 'EC2',
    date: '2026-09-14',
    expectedCost: 240,
    actualCost: 610,
    deviation: 154,
    severity: 'Critical',
    note: 'Sustained spike in on-demand instance hours in us-east-1.',
  },
  {
    id: 'an-2',
    service: 'Data Transfer',
    date: '2026-09-12',
    expectedCost: 90,
    actualCost: 205,
    deviation: 128,
    severity: 'High',
    note: 'Cross-region transfer volume more than doubled overnight.',
  },
  {
    id: 'an-3',
    service: 'RDS',
    date: '2026-09-09',
    expectedCost: 180,
    actualCost: 310,
    deviation: 72,
    severity: 'Medium',
    note: 'Storage auto-scaling triggered twice in one day.',
  },
  {
    id: 'an-4',
    service: 'Lambda',
    date: '2026-09-06',
    expectedCost: 60,
    actualCost: 98,
    deviation: 63,
    severity: 'Low',
    note: 'Invocation count above rolling 30-day baseline.',
  },
];

export const mockRecommendations = [
  {
    id: 'rec-1',
    title: 'Right-size 6 over-provisioned EC2 instances',
    service: 'EC2',
    description: 'Average CPU utilization under 12% for the past 14 days across 6 m5.2xlarge instances.',
    potentialSavings: 1180.0,
    effort: 'Low',
    category: 'Right-sizing',
  },
  {
    id: 'rec-2',
    title: 'Purchase Savings Plan for steady-state compute',
    service: 'EC2',
    description: 'Baseline usage has stayed flat for 60+ days — a 1-year Compute Savings Plan would cut this spend.',
    potentialSavings: 1420.5,
    effort: 'Medium',
    category: 'Commitment',
  },
  {
    id: 'rec-3',
    title: 'Move 3 infrequently accessed S3 buckets to Glacier',
    service: 'S3',
    description: 'Access logs show under 2 reads/month for these buckets over the last quarter.',
    potentialSavings: 340.3,
    effort: 'Low',
    category: 'Storage tiering',
  },
  {
    id: 'rec-4',
    title: 'Delete 9 unattached EBS volumes',
    service: 'EBS',
    description: 'Volumes have had no attached instance for over 30 days.',
    potentialSavings: 300.0,
    effort: 'Low',
    category: 'Cleanup',
  },
];

export const mockUtilization = [
  { resource: 'i-0a2f...e12b', type: 'EC2 · m5.2xlarge', utilization: 11, status: 'Underutilized', cost: 280.4 },
  { resource: 'i-0b91...c447', type: 'EC2 · c5.xlarge', utilization: 78, status: 'Healthy', cost: 190.2 },
  { resource: 'prod-orders-db', type: 'RDS · db.r5.large', utilization: 64, status: 'Healthy', cost: 410.8 },
  { resource: 'vol-0c88...9a2d', type: 'EBS · gp3 500GB', utilization: 0, status: 'Unattached', cost: 40.0 },
  { resource: 'analytics-cache', type: 'ElastiCache · r6g.large', utilization: 22, status: 'Underutilized', cost: 165.6 },
];
