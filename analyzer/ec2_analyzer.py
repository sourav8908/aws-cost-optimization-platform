# analyzer/ec2_analyzer.py
import boto3
from datetime import datetime, timedelta

class EC2Analyzer:
    def __init__(self, region='us-east-1', profile='default'):
        """
        Initialize EC2 Analyzer
        
        Args:
            region: AWS region to analyze
            profile: AWS credentials profile to use
        """
        # Create session with profile
        if profile and profile != 'default':
            session = boto3.Session(profile_name=profile, region_name=region)
            self.ec2 = session.client('ec2')
            self.cloudwatch = session.client('cloudwatch')
        else:
            self.ec2 = boto3.client('ec2', region_name=region)
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        self.region = region
    
    def find_idle_instances(self, cpu_threshold=5, days=7):
        """Find EC2 instances with low CPU usage"""
        instances = self.ec2.describe_instances()
        idle_instances = []
        
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['State']['Name'] != 'running':
                    continue
                
                instance_id = instance['InstanceId']
                
                # Get CloudWatch CPU metrics
                end_time = datetime.now()
                start_time = end_time - timedelta(days=days)
                
                metrics = self.cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # 1 day
                    Statistics=['Average']
                )
                
                if metrics['Datapoints']:
                    avg_cpu = sum(d['Average'] for d in metrics['Datapoints']) / len(metrics['Datapoints'])
                    
                    if avg_cpu < cpu_threshold:
                        # Calculate cost (rough estimate)
                        instance_type = instance['InstanceType']
                        cost = self.estimate_instance_cost(instance_type)
                        
                        idle_instances.append({
                            'InstanceId': instance_id,
                            'InstanceType': instance_type,
                            'AvgCPU': round(avg_cpu, 2),
                            'MonthlyCost': cost,
                            'Recommendation': 'Consider stopping or downsizing'
                        })
        
        return idle_instances
    
    def find_unused_elastic_ips(self):
        """Find Elastic IPs not associated with instances"""
        addresses = self.ec2.describe_addresses()['Addresses']
        unused = []
        
        for addr in addresses:
            if 'InstanceId' not in addr:  # Not associated
                unused.append({
                    'PublicIp': addr['PublicIp'],
                    'AllocationId': addr['AllocationId'],
                    'MonthlyCost': 3.60  # $3.60 per month per unused EIP
                })
        
        return unused
    
    def estimate_instance_cost(self, instance_type):
        """Rough cost estimates (you can make this more accurate)"""
        costs = {
            't2.micro': 8.35,
            't2.small': 16.79,
            't2.medium': 33.58,
            't3.micro': 7.59,
            't3.small': 15.18,
            't3.medium': 30.37
        }
        return costs.get(instance_type, 50)  # Default $50 if unknown