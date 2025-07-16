import os
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from html import unescape
from concurrent.futures import ProcessPoolExecutor, as_completed
import requests  # Add this at the top with your other imports
import re
from flask import render_template_string

def log_failed_url(url, error):
    with open("failed_urls.log", "a", encoding="utf-8") as f:
        f.write(f"{url}\n# {error}\n\n")

def safe_path_from_url(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/')

    # Split path into components and sanitize each component
    parts = path.split('/')
    safe_parts = [re.sub(r'[<>:"\\|?*]', '_', part) for part in parts]

    # Always resolve relative to the project root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    lighthouse_dir = os.path.join(base_dir, 'templates', 'lighthouse_reports')

    return os.path.join(lighthouse_dir, *safe_parts)


# Parse sitemap
def get_urls_from_sitemap(path):
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    return [unescape(loc.text) for loc in root.findall('ns:url/ns:loc', ns)]


# Inject script into Lighthouse HTML file
def inject_script(report_path, script_path):
    try:
        with open(report_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Insert the <script> tag just before the closing </body> tag
        script_tag = f'<script src="{script_path}"></script>'
        html_content = html_content.replace('</body>', f'{script_tag}\n</body>')

        # Write the modified content back to the file
        with open(report_path, 'w', encoding='utf-8') as file:
            file.write(html_content)

        print(f"✅ Script injected successfully into {report_path}")
    except Exception as e:
        print(f"❌ Error injecting script into {report_path}: {str(e)}")


# Create or modify section-overview.html file
def create_or_modify_section_overview(section_path):
    # Define the path to the section-overview.html file
    section_overview_path = os.path.join(safe_path_from_url(section_path), 'section-overview.html')

    # Always overwrite the file (no check for existence)
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(section_overview_path), exist_ok=True)

        # Define the HTML content with Jinja2 template tags
        html_template = """
        <html>
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1">
        <link rel="icon" href='data:image/svg+xml;utf8,<svg fill="none" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="m14 7 10-7 10 7v10h5v7h-5l5 24H9l5-24H9v-7h5V7Z" fill="%23F63"/><path d="M31.561 24H14l-1.689 8.105L31.561 24ZM18.983 48H9l1.022-4.907L35.723 32.27l1.663 7.98L18.983 48Z" fill="%23FFA385"/><path fill="%23FF3" d="M20.5 10h7v7h-7z"/></svg>'>
        <title>{{ section_path }} Overview</title>
        <link rel="stylesheet"  href="{{ url_for('static', filename='css/style.css') }}" />
        <link id="theme-link" rel="stylesheet" href="/static/css/dark-mode.css">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">

        <link href="/static/css/report-styles.css" type="text/css" rel="stylesheet">
        
        </head>
        <body class="dark-theme">
            {% include "includes/header.html" %}
            <header>
            <h1 style="text-transform: uppercase;">{{ section_path }} Overview</h1>
            </header>
            <!-- Container for Lighthouse scores TESTING -->
            <div class="lh-container">
                <div>
                    <div class="lh-scores-wrapper">
                        <div class="lh-scores-container"></div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Use Flask's `render_template_string` to process the template and render it
        rendered_html = render_template_string(html_template, section_path=section_path)

        # Write the rendered HTML to the file
        with open(section_overview_path, 'w', encoding='utf-8') as file:
            file.write(rendered_html)

        # Inject the script into the newly created section-overview.html file
        script_path = '/static/js/totals.js'
        inject_script(section_overview_path, script_path)

        print(f"✅ Created and injected script into {section_overview_path}")
    except Exception as e:
        print(f"❌ Error creating/modifying section-overview.html at {section_overview_path}: {str(e)}")


# Run Lighthouse on one URL
def run_lighthouse(url):
    # Skip if URL isn't valid (e.g., returns 404)
    if not url_is_valid(url):
        log_failed_url(url, "URL not reachable (pre-check)")
        return f"⚠️ Skipped: {url} is not reachable."

    folder_path = safe_path_from_url(url)

    os.makedirs(folder_path, exist_ok=True)
    report_path = os.path.join(folder_path, 'index.html')

    command = f'lighthouse "{url}" --output html --output-path "{report_path}" --quiet --chrome-flags="--headless" --only-categories=seo,accessibility,best-practices'
    try:
        subprocess.run(command, shell=True, check=True)

        # Inject the script only if it's a first-level page
        path_parts = urlparse(url).path.strip('/').split('/')
        if len(path_parts) == 1:
            
            create_or_modify_section_overview(path_parts[0])

        return f"✅ Success: {url}"
    except subprocess.CalledProcessError as e:
        log_failed_url(url, str(e))
        return f"❌ Failed: {url} | Error: {e}"


# Crawl entire sitemap
def crawlSitemap(sitemap_path=None, max_workers=4):
    
    print("Constructed sitemap path:", sitemap_path)
    if sitemap_path is None:
        print(True)
        # Get absolute path to sitemap.xml regardless of where script is run from
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sitemap_path = os.path.join(script_dir, "../static/reports/sitemap/sitemap.xml")
        print(sitemap_path)
    urls = get_urls_from_sitemap(sitemap_path)
    print(f"📄 Found {len(urls)} URLs in sitemap.")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_lighthouse, url) for url in urls]
        for future in as_completed(futures):
            print(future.result())


# Crawl a single page
def crawlSinglePage(url):
    print(f"🔍 Auditing single page: {url}")

    # Run Lighthouse for the given URL (it will work for any page)
    result = run_lighthouse(url)
    print(f"✅ Result for {url}: {result}")


# Crawl pages under a specific section
def crawlSection(section_path, sitemap_path=None, max_workers=4):
    if sitemap_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sitemap_path = os.path.join(script_dir, "../static/reports/sitemap/sitemap.xml")

    if not section_path.startswith('/'):
        section_path = '/' + section_path

    # Get the URLs from the sitemap
    urls = get_urls_from_sitemap(sitemap_path)
    
    # Filter URLs that match the section path
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


# Example usage
if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        if action == 'sitewide_report':
            crawlSitemap()
        elif action == 'section_report':
            crawlSection("/eri")
        elif action == 'single_page_report':
            crawlSinglePage("https://www.oakland.edu/housing/")
        else:
            print(f"❌ Unknown action: {action}")
    else:
        print("❌ No action specified")
