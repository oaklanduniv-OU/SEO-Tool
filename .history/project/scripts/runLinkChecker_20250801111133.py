import os
import subprocess
import datetime
from pathlib import Path
import shutil

def cleanup_old_backups(directory, max_backups=5):
    backups = sorted(
        [f for f in directory.glob("linkchecker-report-BACKUP-*.txt")],
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    # Keep only the most recent N backups
    for old_backup in backups[max_backups:]:
        try:
            old_backup.unlink()
            print(f"[INFO] Deleted old backup: {old_backup}")
        except Exception as e:
            print(f"[WARN] Failed to delete {old_backup}: {e}")



def run_linkchecker(url, levels=1):
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Paths
    reports_dir = Path(__file__).resolve().parent / ".." / "static" / "reports" / "linkchecker"
    reports_dir.mkdir(parents=True, exist_ok=True)

    main_report_path = reports_dir / "linkchecker-report.txt"
    backup_path = reports_dir / f"linkchecker-report-BACKUP-{now}.txt"
    timestamped_output_path = reports_dir / f"linkchecker-report-{now}.txt"

    # Backup current report if it exists
    if main_report_path.exists():
        shutil.move(str(main_report_path), str(backup_path))
        print(f"[INFO] Backed up old report to: {backup_path}")

    # Build the LinkChecker command
    command = [
        "linkchecker",
        url,
        f"-r{levels}",
        "--check-extern",
        "--verbose",
        f"--file-output=text/{timestamped_output_path}"
    ]

    try:
        print(f"[INFO] Running LinkChecker on: {url}")
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            print(f"[WARN] LinkChecker exited with code {result.returncode} — likely due to broken links.")

        # Rename newly created timestamped report to linkchecker-report.txt
        if timestamped_output_path.exists():
            shutil.copy(str(timestamped_output_path), str(main_report_path))
            print(f"[SUCCESS] New report saved as: {main_report_path}")
        else:
            print(f"[ERROR] Expected report was not created: {timestamped_output_path}")

        return str(main_report_path)
    except Exception as e:
        print(f"[ERROR] LinkChecker failed: {e}")
        return None


if __name__ == "__main__":
    test_url = "https://www.oakland.edu/eri/"
    run_linkchecker(test_url)
