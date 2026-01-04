from datetime import datetime
import json


class ReportGenerator:
    def __init__(self, data):
        self.data = data

    def generate_html_report(self, output_file='cost_analysis_report.html'):
        """Generate beautiful HTML report with advanced analytics"""

        metadata = self.data.get('metadata', {})
        savings = self.data['total_savings']
        cost_trend = self.data.get('cost_trend', {})
        dates = [d['date'] for d in cost_trend.get('daily_costs', [])]
        costs = [d['cost'] for d in cost_trend.get('daily_costs', [])]

        # Advanced sections
        cost_spikes = self.data.get('cost_spikes', [])
        service_breakdown = self.data.get('service_breakdown', [])
        forecast_30_days = self.data.get('forecast_30_days', 0)
        severity = self.data.get('recommendation_severity', "LOW 🟢")

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AWS Cost Analysis Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
body {{
    font-family: Segoe UI, Arial;
    background: linear-gradient(135deg,#667eea,#764ba2);
    padding: 20px;
}}
.container {{
    max-width: 1400px;
    margin: auto;
    background: white;
    border-radius: 20px;
    overflow: hidden;
}}
.header {{
    background: linear-gradient(135deg,#FF9900,#FF6600);
    color: white;
    padding: 40px;
    text-align: center;
}}
.content {{ padding: 40px; }}
.summary {{
    display: grid;
    grid-template-columns: repeat(auto-fit,minmax(250px,1fr));
    gap: 25px;
}}
.card {{
    padding: 30px;
    color: white;
    border-radius: 15px;
    text-align: center;
}}
.green {{ background: linear-gradient(135deg,#11998e,#38ef7d); }}
.red {{ background: linear-gradient(135deg,#ee0979,#ff6a00); }}
.section {{ margin-top: 50px; }}
.table-container {{
    background: #f8f9fa;
    padding: 20px;
    border-radius: 12px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
}}
th {{
    background: #FF9900;
    color: white;
    padding: 14px;
}}
td {{
    padding: 14px;
    border-bottom: 1px solid #ddd;
}}
.no-issues {{
    padding: 30px;
    color: #11998e;
    font-weight: bold;
    text-align: center;
}}
.footer {{
    padding: 25px;
    text-align: center;
    background: #f4f5f7;
}}
ul {{
    line-height: 1.8;
    font-size: 16px;
}}
canvas {{
    max-width: 100%;
}}
</style>
</head>

<body>
<div class="container">

<div class="header">
<h1>☁️ AWS Cost Analysis Report</h1>
<p>
Region: {metadata.get('region')} |
Date: {metadata.get('analysis_date')}
</p>
</div>

<div class="content">

<!-- SUMMARY -->
<div class="summary">
    <div class="card green">
        <h2>${savings['monthly_savings']}</h2>
        <p>Monthly Savings</p>
    </div>
    <div class="card green">
        <h2>${savings['yearly_savings']}</h2>
        <p>Yearly Savings</p>
    </div>
    <div class="card red">
        <h2>{self.data['total_issues']}</h2>
        <p>Issues Found</p>
    </div>
    <div class="card red">
        <h2>{severity}</h2>
        <p>Recommendation Severity</p>
    </div>
</div>

<!-- COST TREND -->
<div class="section">
<h2>📈 AWS Cost Trend (Last 30 Days)</h2>
<div class="table-container">
<canvas id="costTrendChart"></canvas>
</div>
</div>

<!-- COST SPIKES -->
<div class="section">
<h2>⚡ Cost Spikes Detected</h2>
{self._generate_cost_spikes_table(cost_spikes)}
</div>

<!-- SERVICE BREAKDOWN -->
<div class="section">
<h2>🛠️ Service-wise Cost Breakdown</h2>
{self._generate_service_table(service_breakdown)}
</div>

<!-- FORECAST -->
<div class="section">
<h2>🔮 Forecast for Next 30 Days</h2>
<div class="table-container">
<p>Estimated Cost: <b>${forecast_30_days}</b></p>
</div>
</div>

<!-- DETAILS -->
<div class="section">
<h2>💾 Unattached EBS Volumes</h2>
{self._generate_ebs_table()}
</div>

<div class="section">
<h2>📸 Old Snapshots</h2>
{self._generate_snapshot_table()}
</div>

<div class="section">
<h2>🖥️ Idle EC2 Instances</h2>
{self._generate_ec2_table()}
</div>

<div class="section">
<h2>🌐 Unused Elastic IPs</h2>
{self._generate_eip_table()}
</div>

</div>

<div class="footer">
AWS Cost Analyzer | Sourav Mohanty
</div>

</div>

<script>
const ctx = document.getElementById('costTrendChart');
new Chart(ctx, {{
    type: 'line',
    data: {{
        labels: {json.dumps(dates)},
        datasets: [{{
            label: 'Daily AWS Cost ($)',
            data: {json.dumps(costs)},
            borderColor: '#FF9900',
            backgroundColor: 'rgba(255,153,0,0.2)',
            tension: 0.4,
            fill: true
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{
                display: true
            }}
        }},
        scales: {{
            y: {{
                beginAtZero: true
            }}
        }}
    }}
}});
</script>

</body>
</html>
"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ Report generated: {output_file}")

    # ================= TABLE HELPERS =================
    def _generate_ebs_table(self):
        if not self.data['unattached_volumes']:
            return '<div class="no-issues">✅ No unattached volumes found</div>'
        rows = ""
        for v in self.data['unattached_volumes']:
            rows += f"<tr><td>{v['VolumeId']}</td><td>{v['Size']} GB</td><td>${v['CostPerMonth']}</td></tr>"
        return f"<div class='table-container'><table><tr><th>Volume ID</th><th>Size</th><th>Monthly Cost</th></tr>{rows}</table></div>"

    def _generate_snapshot_table(self):
        if not self.data['old_snapshots']:
            return '<div class="no-issues">✅ No old snapshots found</div>'
        rows = ""
        for s in self.data['old_snapshots']:
            rows += f"<tr><td>{s['SnapshotId']}</td><td>{s['Age']} days</td><td>${s['CostPerMonth']}</td></tr>"
        return f"<div class='table-container'><table><tr><th>Snapshot ID</th><th>Age</th><th>Monthly Cost</th></tr>{rows}</table></div>"

    def _generate_ec2_table(self):
        if not self.data['idle_instances']:
            return '<div class="no-issues">✅ No idle instances found</div>'
        rows = ""
        for i in self.data['idle_instances']:
            rows += f"<tr><td>{i['InstanceId']}</td><td>{i['InstanceType']}</td><td>{i['AvgCPU']}%</td><td>${i['MonthlyCost']}</td></tr>"
        return f"<div class='table-container'><table><tr><th>ID</th><th>Type</th><th>CPU</th><th>Cost</th></tr>{rows}</table></div>"

    def _generate_eip_table(self):
        if not self.data['unused_eips']:
            return '<div class="no-issues">✅ No unused Elastic IPs found</div>'
        rows = ""
        for e in self.data['unused_eips']:
            rows += f"<tr><td>{e['PublicIp']}</td><td>${e['MonthlyCost']}</td></tr>"
        return f"<div class='table-container'><table><tr><th>Public IP</th><th>Monthly Cost</th></tr>{rows}</table></div>"

    def _generate_cost_spikes_table(self, spikes):
        if not spikes:
            return '<div class="no-issues">✅ No cost spikes detected</div>'
        rows = ""
        for s in spikes:
            rows += f"<tr><td>{s['date']}</td><td>{s['increase_percent']}%</td><td>${s['cost']}</td></tr>"
        return f"<div class='table-container'><table><tr><th>Date</th><th>Increase (%)</th><th>Cost</th></tr>{rows}</table></div>"

    def _generate_service_table(self, services):
        if not services:
            return '<div class="no-issues">✅ No services detected</div>'
        rows = ""
        for s in services:
            rows += f"<tr><td>{s['service']}</td><td>${s['cost']}</td></tr>"
        return f"<div class='table-container'><table><tr><th>Service</th><th>Cost</th></tr>{rows}</table></div>"
