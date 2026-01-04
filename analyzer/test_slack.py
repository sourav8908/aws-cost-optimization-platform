"""Test Slack integration"""
import yaml
from analyzer.slack_notifier import SlackNotifier

def main():
    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    webhook_url = config['slack'].get('webhook_url')
    
    if not webhook_url:
        print("❌ Slack webhook URL not configured in config/config.yaml")
        return
    
    print("🔔 Testing Slack connection...")
    slack = SlackNotifier(webhook_url, config['slack'])
    
    result = slack.test_connection()
    
    if result['success']:
        print("✅ Slack connection successful! Check your Slack channel.")
    else:
        print(f"❌ Failed: {result['error']}")

if __name__ == "__main__":
    main()