import os
import json
from requests import post
from datetime import datetime


def load_json(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")



def generate_report(title, count_dict, format='%Y-%m-%d %H:%M:%S'):
    report_lines = [f"{title}"]
    report_lines.append(f"Generated at: {datetime.now().strftime(format)}")
    report_lines.append("-" * 40)
    for key, count in count_dict.items():
        report_lines.append(f"{key.capitalize():<10}: {count}")
    report_lines.append("-" * 40)
    report = "\n".join(report_lines)
    return report

def send_to_slack(webhook_url, report):
    response = post(webhook_url, json={"text": report})
    if response.status_code == 200:
        print(":white_check_mark: Report sent to Slack successfully.")
    else:
        print(f":x: Failed to send report to Slack. Status code: {response.status_code}")