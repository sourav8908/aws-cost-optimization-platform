"""
AWS Cost Analyzer
Analyzes AWS resources to identify cost optimization opportunities
"""

__version__ = "1.0.0"
__author__ = "Sourav Mohanty"

from .ebs_analyzer import EBSAnalyzer
from .ec2_analyzer import EC2Analyzer
from .report_generator import ReportGenerator

__all__ = [
    'EBSAnalyzer',
    'EC2Analyzer', 
    'ReportGenerator'
]