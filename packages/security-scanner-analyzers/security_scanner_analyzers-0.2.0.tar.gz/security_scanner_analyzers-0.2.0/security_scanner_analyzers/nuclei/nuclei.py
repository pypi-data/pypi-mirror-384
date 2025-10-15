from security_scanner_analyzers.utils import load_json, generate_report, send_to_slack


def nuclei_count_field(data, field_name, skip_values=None):
    count_dict = {}
    for item in data:
        value = item.get("info", {}).get(field_name, "unknown").lower()
        if skip_values and value in skip_values:
            continue
        count_dict[value] = count_dict.get(value, 0) + 1
    return count_dict


def main(file_path, slack_url):
    data = load_json(file_path)
    severity_count = nuclei_count_field(data, "severity")

    report = generate_report(":rocket: Severity Report", severity_count)
    send_to_slack(slack_url, report)
