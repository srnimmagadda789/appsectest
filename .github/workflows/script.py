import requests
import json
from datetime import datetime

# --- CONFIGURATION ---
SNYK_API_TOKEN = 'your_snyk_api_token'
SNYK_ORG_ID = 'your_snyk_org_id'
JIRA_SITE_URL = 'https://your-domain.atlassian.net'
JIRA_USER_EMAIL = 'your-email@example.com'
JIRA_API_TOKEN = 'your_jira_api_token'
JIRA_PROJECT_KEY = 'SEC' 

# Date filter: Issues identified BEFORE April 1st, 2026
END_DATE = "2026-04-01"

def get_historical_snyk_issues():
    """Fetches SAST and SCA issues discovered BEFORE END_DATE."""
    # We use the /reporting/issues endpoint with a 'to' filter
    url = f"https://api.snyk.io/v1/reporting/issues/?to={END_DATE}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {SNYK_API_TOKEN}"
    }
    body = {
        "filters": {
            "orgs": [SNYK_ORG_ID],
            "types": ["vuln", "code"],
            "isFixed": False # Only fetch things still needing attention
        }
    }
    
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json().get('results', [])

def create_jira_backlog_item(issue_data):
    """Creates a Jira issue. By default, new issues land in the Backlog."""
    url = f"{JIRA_SITE_URL}/rest/api/3/issue"
    auth = (JIRA_USER_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    
    title = issue_data.get('issue', {}).get('title')
    severity = issue_data.get('issue', {}).get('severity')
    project_name = issue_data.get('project', {}).get('name')
    snyk_url = issue_data.get('issue', {}).get('url')

    payload = json.dumps({
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": f"[HISTORICAL] Snyk: {title} - {project_name}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": f"Severity: {severity}\n"},
                            {"type": "text", "text": f"Found before: {END_DATE}\n"},
                            {"type": "text", "text": f"Link: {snyk_url}"}
                        ]
                    }
                ]
            },
            "issuetype": {"name": "Bug"},
            # Ensure no 'sprint' field is populated to keep it in the backlog
        }
    })
    
    res = requests.post(url, data=payload, headers=headers, auth=auth)
    if res.status_code == 201:
        print(f"Backlog item created: {title}")
    else:
        print(f"Error: {res.text}")

if __name__ == "__main__":
    print(f"Scanning for Snyk vulnerabilities older than {END_DATE}...")
    issues = get_historical_snyk_issues()
    
    if not issues:
        print("No historical issues found.")
    else:
        print(f"Found {len(issues)} historical issues. Moving to Jira Backlog...")
        for item in issues:
            create_jira_backlog_item(item)
