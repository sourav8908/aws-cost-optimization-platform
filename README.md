# AWS Cost Analyzer with Real-time Slack Alerts 💰🔔

A Python-based tool to analyze AWS infrastructure and identify cost optimization opportunities.

## 🎯 Features

- **EBS Analysis**: Find unattached volumes and old snapshots
- **EC2 Analysis**: Identify idle instances with low CPU utilization
- **Elastic IP Analysis**: Detect unused Elastic IPs
- **Cost Calculation**: Estimate potential monthly and yearly savings
- **Beautiful Reports**: Generate interactive HTML dashboards
- **Slack Alerts**: Real-time Slack notifications for cost spikes, high savings opportunities, and summary reports

## 📊 What It Detects

| Resource Type | What It Finds | Potential Savings |
|--------------|---------------|-------------------|
| EBS Volumes | Unattached volumes costing money | $0.10/GB/month |
| EBS Snapshots | Old snapshots (>90 days) | $0.05/GB/month |
| EC2 Instances | Idle instances (CPU <5%) | Varies by instance type |
| Elastic IPs | Unused IPs not attached to instances | $3.60/month each |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- AWS Account with appropriate IAM permissions
- AWS CLI configured (`aws configure`)

### Installation

```bash
# Clone the repository
git clone https://github.com/sourav8908/aws-cost-analyzer.git
cd aws-cost-analyzer

# Install dependencies
pip install -r requirements.txt

# Configure your AWS credentials
aws configure
IAM Permissions Required

The tool requires read-only permissions. Attach this policy to your IAM user:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}

Usage
# Run analysis with default settings
python main.py

# Specify AWS region
python main.py --region us-west-2

# Use specific AWS profile
python main.py --profile production

# Custom output file
python main.py --output my_report.html

Configuration

Edit config/config.yaml to customize:

aws:
  region: us-east-1  # Your AWS region
  profile: default   # AWS profile name

analysis:
  ebs:
    snapshot_age_days: 90  # Threshold for old snapshots
  ec2:
    cpu_threshold: 5       # CPU % below which instance is considered idle
    analysis_days: 7       # Days to analyze metrics

🔔 Slack Alerts (NEW)

The tool can send real-time alerts to Slack using Incoming Webhooks.

Alerts Supported

📈 Cost Spike Alerts: Triggered when daily AWS cost increases beyond a configurable threshold (default: 30%)

💰 High Savings Alerts: Triggered when potential monthly savings exceed a defined limit (default: $500)

📊 Summary Reports: Optional summary of total issues and savings after analysis

Configuration

Update config/config.yaml:

slack:
  enabled: true
  webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

  triggers:
    cost_spike_threshold: 30
    high_savings_threshold: 500

  send_summary: true

📈 Sample Output
🔍 AWS COST ANALYZER
============================================================
📍 Region: us-east-1
👤 Profile: default
📅 Analysis Date: 2025-12-29 15:30:45
============================================================

📊 Analyzing EBS volumes...
   Found 5 unattached volumes

📊 Analyzing EBS snapshots...
   Found 12 old snapshots (>90 days)

📊 Analyzing EC2 instances...
   Found 3 idle instances (CPU < 5%)

📊 Analyzing Elastic IPs...
   Found 2 unused Elastic IPs

💰 Calculating potential savings...

============================================================
✅ ANALYSIS COMPLETE!
============================================================
💵 Potential Monthly Savings: $127.50
💵 Potential Yearly Savings:  $1,530.00
📋 Total Issues Found: 22

   - Unattached EBS Volumes: 5
   - Old EBS Snapshots: 12
   - Idle EC2 Instances: 3
   - Unused Elastic IPs: 2
============================================================

📄 Open cost_analysis_report.html in your browser to view detailed report

🖼️ Screenshots
📊 Cost Optimization Dashboard

Executive summary showing total monthly & yearly savings.

📈 Cost Trend & Forecast

30-day historical cost trend with forecasting.

🔔 Slack Cost Spike Alert

Automatic Slack alert triggered on abnormal cost spikes.

🛠️ Tech Stack

Python 3.8+: Core language

boto3: AWS SDK for Python

PyYAML: Configuration management

Chart.js: Interactive visualizations

HTML/CSS/JS: Report generation

📦 Project Structure
🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

📝 License

MIT License - feel free to use this for personal or commercial projects

👤 Author

Sourav Mohanty

GitHub: @sourav8908

LinkedIn: Sourav Mohanty

Portfolio: sourav8908-portfolio.vercel.app

🌟 Acknowledgments

Built as part of my DevOps learning journey at IIT Patna.
Special thanks to the open-source community for the amazing tools and libraries.

⚠️ Disclaimer: This tool provides cost estimates based on AWS pricing at the time of analysis.
Actual costs may vary. Always review recommendations before taking action on production resources.


---



