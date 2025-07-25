import os
import sys
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from html import unescape
from concurrent.futures import ProcessPoolExecutor, as_completed
import requests
import re


def log_failed_url(url, error):
    with open("failed_urls.log", "a", encoding="utf-8") as f:
        f.write(f"{url}\n# {error}\n\n")

def safe_path_from_url(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/')

    parts = path.split('/')
    safe_parts = [re.sub(r'[<>:"\\|?*]', '_', part) for part in parts]

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    lighthouse_dir = os.path.join(base_dir, 'templates', 'lighthouse_reports')

    return os.path.join(lighthouse_dir, *safe_parts)


def get_urls_from_sitemap(path):
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    return [unescape(loc.text) for loc in root.findall('ns:url/ns:loc', ns)]


def inject_script(report_path, script_path):
    try:
        with open(report_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        script_tag = f'<script src="{script_path}"></script>'
        html_content = html_content.replace('</body>', f'{script_tag}\n</body>')

        with open(report_path, 'w', encoding='utf-8') as file:
            file.write(html_content)

        print(f"✅ Script injected successfully into {report_path}")
    except Exception as e:
        print(f"❌ Error injecting script into {report_path}: {str(e)}")


def run_lighthouse(url):
    if not url_is_valid(url):
        log_failed_url(url, "URL not reachable (pre-check)")
        return f"⚠️ Skipped: {url} is not reachable."

    folder_path = safe_path_from_url(url)
    os.makedirs(folder_path, exist_ok=True)
    report_path = os.path.join(folder_path, 'index.html')

    command = (
        f'lighthouse "{url}" '
        f'--output html '
        f'--output-path "{report_path}" '
        f'--quiet '
        f'--chrome-flags="--no-sandbox --headless --disable-gpu --disable-dev-shm-usage --disable-setuid-sandbox" '
        f'--only-categories=seo,accessibility,best-practices '
        f'--chrome-path=/usr/bin/chromium'
    )

    env = os.environ.copy()
    env["CHROME_PATH"] = "/usr/bin/chromium"

    try:
        subprocess.run(command, shell=True, check=True, env=env)
        return f"✅ Success: {url}"
    except subprocess.CalledProcessError as e:
        log_failed_url(url, str(e))
        return f"❌ Failed: {url} | Error: {e}"


def crawlSitemap(sitemap_path=None, max_workers=1, chunk_index=None, total_chunks=None):
    print("Constructed sitemap path:", sitemap_path)
    if sitemap_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sitemap_path = os.path.join(script_dir, "../static/reports/sitemap/sitemap.xml")

    urls = get_urls_from_sitemap(sitemap_path)
    print(f"📄 Found {len(urls)} URLs in sitemap.")

    if chunk_index is not None and total_chunks is not None:
        chunk_index = int(chunk_index)
        total_chunks = int(total_chunks)
        chunk_size = len(urls) // total_chunks
        start = chunk_index * chunk_size
        end = len(urls) if chunk_index == total_chunks - 1 else start + chunk_size
        urls = urls[start:end]
        print(f"🔀 Processing chunk {chunk_index + 1}/{total_chunks}: {len(urls)} URLs")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_lighthouse, url) for url in urls]
        for future in as_completed(futures):
            print(future.result())


def crawlSinglePage(url):
    print(f"🔍 Auditing single page: {url}")
    result = run_lighthouse(url)
    print(f"✅ Result for {url}: {result}")


def crawlSection(section_path, sitemap_path=None, max_workers=1):
    if sitemap_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sitemap_path = os.path.join(script_dir, "../static/reports/sitemap/sitemap.xml")

    if not section_path.startswith('/'):
        section_path = '/' + section_path

    urls = get_urls_from_sitemap(sitemap_path)
    matching_urls = [url for url in urls if urlparse(url).path.startswith(section_path)]

    print(f"📁 Found {len(matching_urls)} URLs under section '{section_path}'.")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_lighthouse, url) for url in matching_urls]
        for future in as_completed(futures):
            print(future.result())


def url_is_valid(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == 'sitewide_report':
            chunk_index = os.getenv("CHUNK_INDEX")
            total_chunks = os.getenv("TOTAL_CHUNKS")

            crawlSitemap(chunk_index=chunk_index, total_chunks=total_chunks)
        elif mode == 'single_page_report':
            if len(sys.argv) > 2:
                url = sys.argv[2]
                crawlSinglePage(url)
            else:
                print("❌ Missing URL argument for single_page_report")
        elif mode == 'section_report':
            if len(sys.argv) > 2:
                section = sys.argv[2]
                crawlSection(section)
            else:
                print("❌ Missing section argument for section_report")
        else:
            print(f"❌ Unknown mode: {mode}")
    else:
        print("❌ No mode specified")
