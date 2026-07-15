import subprocess, json, requests
from orchestrator import plan_task

def check_health():
    services = ["penpot-frontend", "strapi", "saleor-api", "appsmith", "payment-service"]
    for svc in services:
        try:
            r = requests.get(f"http://{svc}:80/health", timeout=2)
            if r.status_code != 200:
                return f"Service {svc} unhealthy"
        except:
            return f"Service {svc} unreachable"
    return "OK"

def heal(service):
    log = subprocess.check_output(["docker", "logs", service, "--tail", "50"]).decode()
    fix = plan_task(f"Analyze this error log for {service}:\n{log}\nSuggest a fix command.")
    print(f"Proposed fix: {fix}")
    if input("Apply fix? (y/n): ").lower() == 'y':
        subprocess.run(fix, shell=True)
