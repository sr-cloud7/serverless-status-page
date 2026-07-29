import os
import json
import requests
from datetime import datetime, timezone

# --- Configuration ---
TARGETS_FILE = "targets.json"

# These environment variables are automatically provided by GitHub Actions
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY") # e.g., "shivam-gupta/serverless-status-page"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_open_issues():
    """Fetch currently open issues to prevent duplicate incident spam."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return []
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return [issue['title'] for issue in response.json()]
    return []

def create_issue(service_name, status_code, error_msg):
    """Create a GitHub issue for a detected outage."""
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print(f"Skipping issue creation for {service_name} (Running locally, no token).")
        return

    title = f"🚨 Outage Detected: {service_name}"
    open_issues = get_open_issues()
    
    # Alert Deduplication: Don't create an issue if one is already open
    if title in open_issues:
        print(f"Incident already open for {service_name}. Skipping duplicate alert.")
        return

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    body = {
        "title": title,
        "body": f"**Service:** {service_name}\n**Status Code:** {status_code}\n**Error:** {error_msg}\n**Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n_This issue was created automatically by the SRE Uptime Monitor CI/CD Pipeline._",
        "labels": ["incident", "automated-alert"]
    }
    
    response = requests.post(url, headers=HEADERS, data=json.dumps(body))
    if response.status_code == 201:
        print(f"Successfully created incident issue for {service_name}")
    else:
        print(f"Failed to create issue: {response.text}")

def main():
    # 1. Load the endpoints to monitor
    with open(TARGETS_FILE, 'r') as f:
        targets = json.load(f)

    results = []
    
    # 2. Perform the Health Checks
    for target in targets:
        name = target['name']
        url = target['url']
        
        try:
            # 5-second timeout ensures the script doesn't hang forever
            response = requests.get(url, timeout=5)
            status_code = response.status_code
            latency = round(response.elapsed.total_seconds() * 1000)
            
            if response.status_code >= 400:
                status = "Down 🔴"
                create_issue(name, status_code, "HTTP Error returned")
            else:
                status = "Operational 🟢"
        
        except requests.exceptions.RequestException as e:
            # Handles timeouts, DNS failures, and connection refused
            status = "Down 🔴"
            status_code = "N/A"
            latency = "N/A"
            create_issue(name, status_code, str(e))
            
        results.append({
            "name": name,
            "url": url,
            "status": status,
            "status_code": status_code,
            "latency": latency
        })

    # 3. Generate the Static HTML Dashboard
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SRE Status Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px auto; max-width: 800px; padding: 20px; background-color: #f6f8fa; color: #24292f; }}
            h1 {{ border-bottom: 1px solid #d0d7de; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 6px; overflow: hidden; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #d0d7de; }}
            th {{ background-color: #f6f8fa; font-weight: 600; }}
            .operational {{ color: #1a7f37; font-weight: bold; }}
            .down {{ color: #cf222e; font-weight: bold; }}
            .footer {{ margin-top: 20px; font-size: 0.9em; color: #57606a; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>System Status Dashboard</h1>
        <table>
            <thead>
                <tr>
                    <th>Service Endpoint</th>
                    <th>Current Status</th>
                    <th>Latency (ms)</th>
                </tr>
            </thead>
            <tbody>
    """

    for r in results:
        css_class = "operational" if "Operational" in r['status'] else "down"
        html_content += f"""
                <tr>
                    <td><a href="{r['url']}" target="_blank">{r['name']}</a></td>
                    <td class="{css_class}">{r['status']}</td>
                    <td>{r['latency']}</td>
                </tr>
        """

    html_content += f"""
            </tbody>
        </table>
        <div class="footer">
            Automated check completed at: {timestamp}
        </div>
    </body>
    </html>
    """

    # 4. Write the results to index.html
    with open("index.html", "w") as f:
        f.write(html_content)
        
    print("Health checks complete. Static index.html updated successfully.")

if __name__ == "__main__":
    main()
