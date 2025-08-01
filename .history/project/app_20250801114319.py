from flask import Flask, render_template, jsonify, send_from_directory, Blueprint, request
import subprocess
import os
import sys
from werkzeug.utils import secure_filename
import time
from functools import lru_cache
import requests
import json

import math

sys.path.append('./scripts')
from average_scores import walk_and_average_scores  # Removed REPORTS_ROOT import
from GenerateSEOReports import crawlSitemap, crawlSinglePage, crawlSection
from flask_caching import Cache

app = Flask(__name__)

# Define Blueprint and routes BEFORE registering
api = Blueprint('api', __name__)

# Set up Flask-Caching
app.config['CACHE_TYPE'] = 'simple'  # Use in-memory cache
cache = Cache(app)

@app.route('/get-level-1-dirs')
def get_level_1_dirs():
    reports_dir = os.path.join(app.root_path, 'static', 'reports', 'lighthouse_reports')
    try:
        # List directories in /templates/lighthouse_reports/
        dirs = [d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))]
        return jsonify(dirs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Configure the folder for uploaded files
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'reports', 'sitemap')
ALLOWED_EXTENSIONS = {'xml'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-sitemap', methods=['POST'])
def upload_sitemap():
    if 'sitemap-file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['sitemap-file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        # Secure the filename to prevent any security risks
        filename = secure_filename(file.filename)
        # Save the file to the uploads folder
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'message': 'Sitemap uploaded successfully!'}), 200
    else:
        return jsonify({'message': 'Invalid file format. Only XML files are allowed.'}), 400

# Custom cache with expiration time
CACHE_EXPIRATION_TIME = 60 * 60 # 1 hour in seconds
cache = {}
# Cache function to avoid re-scanning the directories
def get_index_html_count_with_expiration(reports_root):
    current_time = time.time()
    # Check if cached value exists and has not expired
    if reports_root in cache:
        cached_time, cached_result = cache[reports_root]
        if current_time - cached_time < CACHE_EXPIRATION_TIME:
            return cached_result  # Return the cached result if it's still valid

    # If no valid cache, recalculate the count
    total = 0
    for root, _, files in os.walk(reports_root):
        total += files.count("index.html")

    # Cache the result with the current timestamp
    cache[reports_root] = (current_time, total)
    return total

# Your endpoint logic
@api.route('/api/average-scores', defaults={'subpath': '', 'page': 1})
@api.route('/api/average-scores/<path:subpath>', defaults={'page': 1})
@api.route('/api/average-scores/<path:subpath>/<int:page>')
def get_average_scores(subpath, page):
    report_dir = os.path.join(app.root_path, 'static', 'reports', 'lighthouse_reports')

    if subpath:
        reports_root = os.path.join(report_dir, subpath.strip('/'))
    else:
        reports_root = report_dir

    per_page = 10
    page_param = request.args.get('page', '1')

    if page_param.lower() == 'all':
        cache_file = os.path.join(app.root_path, 'static', 'reports', 'average-scores.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            total_items = len(data['pages'])
            total_pages = math.ceil(total_items / per_page)
            return jsonify({
                'average': data.get('average', {}),
                'pages': data.get('pages', []),
                'pagination': {
                    'current_page': 'all',
                    'total_pages': total_pages,
                    'total_items': total_items
                }
            })
        else:
            return jsonify({"error": "average-scores.json not found"}), 404
    else:
        try:
            page = int(page_param)
        except ValueError:
            page = 1

        if page < 1:
            page = 1

        offset = (page - 1) * per_page

        data = walk_and_average_scores(
            reports_root,
            base_path=report_dir,
            limit=per_page,
            offset=offset,
            compute_average=False
        )

        # Get the count of index.html files from the cached function
        total_items = get_index_html_count_with_expiration(reports_root)
        total_pages = math.ceil(total_items / per_page)

        if page > total_pages:
            page = total_pages

        return jsonify({
            'average': None,
            'pages': data['pages'],
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_items': total_items
            }
        })


# Register Blueprint AFTER defining all routes
app.register_blueprint(api)


GITHUB_REPO = "arkomeshak-OU/SEO-Tool"  # <-- Replace with your actual GitHub repo
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")  # From Render's env variables
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows"

def trigger_workflow(workflow_filename, inputs=None):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "ref": "main"
    }

    if inputs:
        data["inputs"] = inputs

    response = requests.post(
        f"{GITHUB_API_URL}/{workflow_filename}/dispatches",
        json=data,
        headers=headers
    )

    if response.status_code == 204:
        return True, "Workflow triggered successfully"
    else:
        return False, f"Failed to trigger workflow: {response.text}"

@app.route('/run-script', methods=['POST'])
def run_script():
    action = request.form.get('action')
    section = request.form.get('section')
    url = request.form.get('url')

    if action == 'sitewide_report':
        success, message = trigger_workflow("seo-reports.yml")  # <-- Use actual file name
        return jsonify({"message": message}), (200 if success else 500)

    elif action == 'section_report':
        if not section:
            return jsonify({"message": "No section selected"}), 400
        success, message = trigger_workflow("manual-reports.yml", inputs={"mode": "section", "value": section})
        return jsonify({"message": message}), (200 if success else 500)

    elif action == 'single_page_report':
        if not url:
            return jsonify({"message": "No URL provided"}), 400
        success, message = trigger_workflow("manual-reports.yml", inputs={"mode": "single_page", "value": url})
        return jsonify({"message": message}), (200 if success else 500)
    elif action == 'link_checker_report':
        # Trigger the GitHub workflow for linkchecker, assuming you have one
        success, message = trigger_workflow("generate-linkchecker-report.yml") 
        return jsonify({"message": message}), (200 if success else 500)

    else:
        return jsonify({"message": "Invalid action"}), 400

@app.route('/workflow-status')
def workflow_status():
    mode = request.args.get('mode')
    value = request.args.get('value')
    
    if not GITHUB_TOKEN:
        return jsonify({"error": "Missing GitHub token"}), 500

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    workflow_name = "manual-reports.yml"

    response = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow_name}/runs",
        headers=headers
    )

    if response.status_code != 200:
        return jsonify({"error": response.json()}), response.status_code

    runs = response.json().get("workflow_runs", [])
    if not runs:
        return jsonify({"status": "not_found"})

    latest_run = runs[0]

    # Fetch jobs for this run to get step info
    jobs_url = latest_run['jobs_url']
    jobs_resp = requests.get(jobs_url, headers=headers)
    if jobs_resp.status_code != 200:
        return jsonify({
            "status": latest_run["status"],
            "conclusion": latest_run.get("conclusion"),
            "html_url": latest_run["html_url"]
        })

    jobs_data = jobs_resp.json()
    jobs = jobs_data.get('jobs', [])
    
    # Flatten all steps from all jobs into one list
    all_steps = []
    for job in jobs:
        all_steps.extend(job.get('steps', []))

    total_steps = len(all_steps)
    current_step_index = 0

    # Find first incomplete or in-progress step
    for idx, step in enumerate(all_steps):
        if step['conclusion'] is None:  # Step is running or pending
            current_step_index = idx + 1
            current_step_name = step['name']
            break
    else:
        # If all steps have conclusion, then set current step to total
        current_step_index = total_steps
        current_step_name = "Finishing up"

    return jsonify({
        "status": latest_run["status"],  # queued, in_progress, completed
        "conclusion": latest_run.get("conclusion"),
        "html_url": latest_run["html_url"],
        "progress": {
            "current_step": current_step_index,
            "total_steps": total_steps,
            "current_step_name": current_step_name
        }
    })



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/linkchecker')
def linkchecker():
    return render_template('linkchecker/index.html')

@app.route('/generate-reports')
def report_generation():
    report_dir = os.path.join(app.root_path, 'static', 'reports', 'lighthouse_reports')
    level_1_dirs = [d for d in os.listdir(report_dir) if os.path.isdir(os.path.join(report_dir, d))]
    return render_template('generate-reports/index.html', level_1_dirs=level_1_dirs)

@app.route('/reports/', defaults={'subpath': ''})
@app.route('/reports/<path:subpath>')
def serve_report(subpath):
    report_dir = os.path.join(app.root_path, 'static', 'reports', 'lighthouse_reports')
    subpath = subpath.strip('/')
    requested_path = os.path.join(report_dir, subpath)
    if os.path.isdir(requested_path):
        requested_path = os.path.join(requested_path, 'index.html')
    elif not os.path.exists(requested_path):
        index_candidate = os.path.join(requested_path, 'index.html')
        if os.path.exists(index_candidate):
            requested_path = index_candidate
        else:
            return "Not Found", 404
    subpath = os.path.relpath(requested_path, report_dir)
    subpath = subpath.replace(os.sep, '/')
    return send_from_directory(report_dir, subpath)

if __name__ == "__main__":
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    REPORTS_ROOT = os.path.join(BASE_DIR, '..', 'static', 'reports', 'lighthouse_reports')
    OUTPUT_FILE = os.path.join(BASE_DIR, '..', 'static', 'reports', 'average-scores.json')

    result = walk_and_average_scores(REPORTS_ROOT)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Wrote average scores to {OUTPUT_FILE}")
