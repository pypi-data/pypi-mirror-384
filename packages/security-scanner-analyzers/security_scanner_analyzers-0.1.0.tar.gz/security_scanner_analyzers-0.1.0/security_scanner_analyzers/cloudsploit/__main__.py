from argparse import ArgumentParser
from security_scanner_analyzers.cloudsploit.parser import main

if __name__ == "__main__":
    parser = ArgumentParser(description="Process a CloudSploit JSON report.")
    parser.add_argument(
        "--file", "-f", required=True, help="Path to the CloudSploit JSON report file."
    )
    parser.add_argument(
        "--slack", "-s", required=True, help="Slack Webhook URL to send the report."
    )
    args = parser.parse_args()
    main(args.file, args.slack)
