# analyzer/ebs_analyzer.py
import boto3
from datetime import datetime, timedelta

class EBSAnalyzer:
    def __init__(self, region='us-east-1', profile='default'):
        """
        Initialize EBS Analyzer
        
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
    
    def find_unattached_volumes(self):
        """Find EBS volumes not attached to any instance"""
        volumes = self.ec2.describe_volumes()['Volumes']
        unattached = []
        
        for vol in volumes:
            if vol['State'] == 'available':  # Not attached
                size = vol['Size']
                cost_per_month = size * 0.10  # $0.10 per GB per month
                
                unattached.append({
                    'VolumeId': vol['VolumeId'],
                    'Size': size,
                    'CostPerMonth': round(cost_per_month, 2),
                    'CreateTime': vol['CreateTime']
                })
        
        return unattached
    
    def find_old_snapshots(self, days_old=90):
        """Find snapshots older than X days"""
        snapshots = self.ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
        old_snapshots = []
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        for snap in snapshots:
            snap_date = snap['StartTime'].replace(tzinfo=None)
            if snap_date < cutoff_date:
                size = snap['VolumeSize']
                cost_per_month = size * 0.05  # $0.05 per GB per month
                
                old_snapshots.append({
                    'SnapshotId': snap['SnapshotId'],
                    'Size': size,
                    'Age': (datetime.now() - snap_date).days,
                    'CostPerMonth': round(cost_per_month, 2)
                })
        
        return old_snapshots
    
    def calculate_total_savings(self):
        """Calculate potential total savings"""
        unattached = self.find_unattached_volumes()
        old_snaps = self.find_old_snapshots()
        
        total_savings = sum(v['CostPerMonth'] for v in unattached)
        total_savings += sum(s['CostPerMonth'] for s in old_snaps)
        
        return {
            'monthly_savings': round(total_savings, 2),
            'yearly_savings': round(total_savings * 12, 2),
            'unattached_volumes_count': len(unattached),
            'old_snapshots_count': len(old_snaps)
        }