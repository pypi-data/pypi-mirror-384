from argparse import ArgumentParser
from security_scanner_analyzers.nuclei.nuclei import main

if __name__ == "__main__":
    parser = ArgumentParser(description="Scan a JSON file and count severity levels.")
    parser.add_argument(
        "--file", "-f", required=True, help="Path to the JSON file to scan."
    )
    parser.add_argument(
        "--slack", "-s", required=True, help="Slack Webhook URL to send the report."
    )
    args = parser.parse_args()
    main(args.file, args.slack)