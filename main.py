import sys
import io
import os
import argparse
import yaml
import boto3
import json
from datetime import datetime, timedelta
from analyzer.ebs_analyzer import EBSAnalyzer
from analyzer.ec2_analyzer import EC2Analyzer
from analyzer.report_generator import ReportGenerator
from analyzer.slack_notifier import SlackNotifier


# ================= CONFIG LOADER =================
def load_config():
    """Load configuration from YAML file"""
    try:
        with open('config/config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config/config.yaml not found!")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}")
        sys.exit(1)

# ================= COST TREND =================
def get_cost_trend(days=30):
    """Fetch AWS cost trend using Cost Explorer"""
    ce = boto3.client('ce', region_name='us-east-1')
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')},
        Granularity='DAILY',
        Metrics=['UnblendedCost']
    )

    daily_costs = []
    total_cost = 0.0
    for day in response['ResultsByTime']:
        cost = float(day['Total']['UnblendedCost']['Amount'])
        total_cost += cost
        daily_costs.append({
            "date": day['TimePeriod']['Start'],
            "cost": round(cost, 2)
        })

    return {"total_cost": round(total_cost, 2), "daily_costs": daily_costs}

# ================= ADVANCED FEATURES =================
def detect_cost_spikes(cost_trend, threshold=30):
    """Detect daily cost spikes above threshold (%)"""
    spikes = []
    data = cost_trend['daily_costs']
    for i in range(1, len(data)):
        prev = data[i-1]['cost']
        curr = data[i]['cost']
        if prev > 0:
            change = ((curr - prev) / prev) * 100
            if change >= threshold:
                spikes.append({"date": data[i]['date'],
                               "increase_percent": round(change, 2),
                               "cost": curr})
    return spikes

def forecast_30_days(cost_trend):
    """Forecast next 30 days cost based on average"""
    daily = [d['cost'] for d in cost_trend['daily_costs']]
    avg = sum(daily) / len(daily) if daily else 0
    return round(avg * 30, 2)

def service_cost_breakdown(profile):
    """Return cost breakdown per AWS service"""
    session = boto3.Session(profile_name=profile)
    ce = session.client('ce', region_name='us-east-1')
    end = datetime.utcnow().date()
    start = end - timedelta(days=30)

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    services = []
    for g in response['ResultsByTime'][0]['Groups']:
        services.append({
            "service": g['Keys'][0],
            "cost": round(float(g['Metrics']['UnblendedCost']['Amount']), 2)
        })
    return services

def recommendation_severity(monthly_savings):
    """Return HIGH/MEDIUM/LOW severity"""
    if monthly_savings >= 500:
        return "HIGH"
    elif monthly_savings >= 100:
        return "MEDIUM"
    return "LOW"

# ================= MAIN =================
def main():
    parser = argparse.ArgumentParser(description='AWS Cost Analyzer')
    parser.add_argument('--region', default=None, help='AWS region')
    parser.add_argument('--profile', default=None, help='AWS profile')
    parser.add_argument('--output', default='outputs/cost_analysis_report.html', help='Output HTML file')
    args = parser.parse_args()

    # Ensure outputs folder exists
    os.makedirs('outputs', exist_ok=True)

    config = load_config()
    region = args.region or config['aws']['region']
    profile = args.profile or config['aws']['profile']

    print("="*60)
    print("AWS COST ANALYZER")
    print("="*60)

    try:
        # Initialize analyzers
        ebs = EBSAnalyzer(region=region, profile=profile)
        ec2 = EC2Analyzer(region=region, profile=profile)

        # EBS Analysis
        unattached_volumes = ebs.find_unattached_volumes()
        old_snapshots = ebs.find_old_snapshots(days_old=config['analysis']['ebs']['snapshot_age_days'])

        # EC2 Analysis
        idle_instances = ec2.find_idle_instances(
            cpu_threshold=config['analysis']['ec2']['cpu_threshold'],
            days=config['analysis']['ec2']['analysis_days']
        )

        # Elastic IPs
        unused_eips = ec2.find_unused_elastic_ips() if config['analysis']['elastic_ip']['check_unused'] else []

        # Cost Trend & Advanced Features
        cost_trend = get_cost_trend(30)
        cost_spikes = detect_cost_spikes(cost_trend)
        forecast = forecast_30_days(cost_trend)
        service_breakdown = service_cost_breakdown(profile)

        # Savings
        ebs_savings = ebs.calculate_total_savings()
        ec2_savings = sum(i['MonthlyCost'] for i in idle_instances)
        eip_savings = len(unused_eips) * config['pricing']['elastic_ip_unused']
        total_monthly = round(ebs_savings['monthly_savings'] + ec2_savings + eip_savings, 2)
        total_yearly = round(total_monthly * 12, 2)
        severity = recommendation_severity(total_monthly)

        # Analysis data
        analysis_data = {
            'unattached_volumes': unattached_volumes,
            'old_snapshots': old_snapshots,
            'idle_instances': idle_instances,
            'unused_eips': unused_eips,
            'cost_trend': cost_trend,
            'cost_spikes': cost_spikes,
            'service_breakdown': service_breakdown,
            'forecast_30_days': forecast,
            'recommendation_severity': severity,
            'total_savings': {
                'monthly_savings': total_monthly,
                'yearly_savings': total_yearly
            },
            'total_issues': len(unattached_volumes) + len(old_snapshots) + len(idle_instances) + len(unused_eips),
            'metadata': {
                'region': region,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'cpu_threshold': config['analysis']['ec2']['cpu_threshold']
            }
        }
        # Slack Notifications (add before report generation)
        if config.get('slack', {}).get('enabled'):
            print(f"\n{Fore.CYAN}📢 Sending Slack notifications...{Style.RESET_ALL}")
            
            webhook_url = config['slack'].get('webhook_url')
            if not webhook_url:
                print(f"{Fore.YELLOW}⚠️  Slack webhook URL not configured{Style.RESET_ALL}")
            else:
                slack = SlackNotifier(webhook_url, config['slack'])
                
                # Check for cost spikes
                if 'cost_trends' in analysis_data and analysis_data['cost_trends']:
                    trends = analysis_data['cost_trends']
                    if len(trends) >= 2:
                        latest = trends[-1]
                        previous = trends[-2]
                        
                        if previous['cost'] > 0:
                            spike_percentage = ((latest['cost'] - previous['cost']) / previous['cost']) * 100
                            
                            threshold = config['slack']['triggers'].get('cost_spike_threshold', 30)
                            if spike_percentage > threshold:
                                result = slack.send_cost_spike_alert({
                                    'date': latest['date'],
                                    'percentage': spike_percentage,
                                    'current_cost': latest['cost'],
                                    'previous_cost': previous['cost']
                                })
                                
                                if result['success']:
                                    print(f"{Fore.GREEN}✅ Cost spike alert sent to Slack{Style.RESET_ALL}")
                                else:
                                    print(f"{Fore.YELLOW}⚠️  {result['error']}{Style.RESET_ALL}")
                
                # Check for high savings
                total_monthly = analysis_data['total_savings']['monthly_savings']
                savings_threshold = config['slack']['triggers'].get('high_savings_threshold', 500)
                
                if total_monthly > savings_threshold:
                    # Prepare top issues
                    top_issues = []
                    
                    if analysis_data.get('unattached_volumes'):
                        total = sum(v['CostPerMonth'] for v in analysis_data['unattached_volumes'])
                        top_issues.append({
                            'type': 'Unattached EBS Volumes',
                            'savings': total
                        })
                    
                    if analysis_data.get('old_snapshots'):
                        total = sum(s['CostPerMonth'] for s in analysis_data['old_snapshots'])
                        top_issues.append({
                            'type': 'Old EBS Snapshots',
                            'savings': total
                        })
                    
                    if analysis_data.get('idle_instances'):
                        total = sum(i['MonthlyCost'] for i in analysis_data['idle_instances'])
                        top_issues.append({
                            'type': 'Idle EC2 Instances',
                            'savings': total
                        })
                    
                    # Sort by savings
                    top_issues.sort(key=lambda x: x['savings'], reverse=True)
                    
                    result = slack.send_high_savings_alert({
                        'monthly_savings': total_monthly,
                        'yearly_savings': analysis_data['total_savings']['yearly_savings'],
                        'total_issues': analysis_data['total_issues'],
                        'top_issues': top_issues
                    })
                    
                    if result['success']:
                        print(f"{Fore.GREEN}✅ High savings alert sent to Slack{Style.RESET_ALL}")
                
                # Send summary report if configured
                if config['slack'].get('send_summary'):
                    # Prepare issue summary
                    issue_summary = {}
                    if analysis_data.get('unattached_volumes'):
                        issue_summary['Unattached Volumes'] = len(analysis_data['unattached_volumes'])
                    if analysis_data.get('old_snapshots'):
                        issue_summary['Old Snapshots'] = len(analysis_data['old_snapshots'])
                    if analysis_data.get('idle_instances'):
                        issue_summary['Idle Instances'] = len(analysis_data['idle_instances'])
                    if analysis_data.get('unused_eips'):
                        issue_summary['Unused EIPs'] = len(analysis_data['unused_eips'])
                    
                    result = slack.send_summary_report({
                        'total_issues': analysis_data['total_issues'],
                        'total_savings': analysis_data['total_savings'],
                        'issue_summary': issue_summary
                    })
                    
                    if result['success']:
                        print(f"{Fore.GREEN}✅ Summary report sent to Slack{Style.RESET_ALL}")

        # Export JSON & CSV
        with open("outputs/aws_cost_report.json", "w", encoding='utf-8') as jf:
            json.dump(analysis_data, jf, indent=4)

        with open("outputs/aws_cost_report.csv", "w", encoding='utf-8') as cf:
            cf.write("Metric,Value\n")
            cf.write(f"Monthly Savings,{total_monthly}\n")
            cf.write(f"Forecast 30 Days,{forecast}\n")
            cf.write(f"Severity,{severity}\n")

        # Generate HTML Report
        report = ReportGenerator(analysis_data)
        report.generate_html_report(args.output)

        print("Analysis Complete. Reports generated in outputs/ folder.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
