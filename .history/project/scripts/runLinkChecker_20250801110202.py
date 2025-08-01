import os
import subprocess
import datetime

def run_linkchecker(url, levels=3):
    # Define report output path
    base_dir = os.path.abspath(os.path.dirname(__file__))
    report_dir = os.path.join(base_dir, '..', 'static', 'reports', 'linkchecker')
    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"linkchecker-report-{timestamp}.txt"
    report_path = os.path.join(report_dir, report_filename)

    # Build the linkchecker command
    command = [
        "linkchecker",
        url,
        "--check-extern",
        "--verbose",
        f"--file-output=text/{report_path}"
    ]

    # Run the command
    try:
        print(f"[INFO] Running LinkChecker on: {url}")
        subprocess.run(command, check=True)
        print(f"[SUCCESS] Report written to: {report_path}")
        return report_path
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] LinkChecker failed: {e}")
        return None

if __name__ == "__main__":
    test_url = "https://www.oakland.edu/eri/"
    run_linkchecker(test_url)
