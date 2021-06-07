import json
import requests
import os
import datetime
import sys
import subprocess
from urllib import parse
from shutil import which

def error(*args):
    for arg in args:
        print(arg, end=" ")
    print()
    sys.exit(-1)

if "DEFECTDOJO_API_TOKEN" in os.environ:
    dd_auth_token = os.environ["DEFECTDOJO_API_TOKEN"]
else:
    error("Error: DEFECTDOJO_API_TOKEN is not set!")

DD_SERVER_URL = "https://dd.meterian.io/"

def find_product_by_project_name(project_name):
    url = DD_SERVER_URL + '/api/v2/products/?' + parse.urlencode({"name": project_name})
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + dd_auth_token,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        if response.json()["count"] == 0:
            error("Error: no products found matching '", project_name, "'")
    else:
        error("Error: failure while retreiving product with name", project_name, "\n", response)
    
    return response.json()["results"][0]["id"]
    

def create_ad_hoc_engagement(product_id):
    url = DD_SERVER_URL + '/api/v2/engagements/'
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + dd_auth_token,
        "Content-Type": "application/json",
    }

    date = datetime.datetime.now()
    engagement_title="AdHoc Import - " + date.strftime("%a, %d %b %Y %H:%M:%S")
    data = json.dumps({
      "tags": [],
      "name": engagement_title,
      "description": None,
      "version": "",
      "first_contacted": None,
      "target_start": date.strftime("%F"),
      "target_end": date.strftime("%F"),
      "reason": None,
      "active": True,
      "tracker": None,
      "test_strategy": None,
      "threat_model": False,
      "api_test": False,
      "pen_test": False,
      "check_list": False,
      "status": "In Progress",
      "engagement_type": "Interactive",
      "build_id": "",
      "commit_hash": "",
      "branch_tag": "",
      "source_code_management_uri": None,
      "deduplication_on_engagement": False,
      "lead": None,
      "requester": None,
      "preset": None,
      "report_type": None,
      "product": product_id,
      "build_server": None,
      "source_code_management_server": None,
      "orchestration_engine": None
    })

    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 201:
        return response.json()["id"]
    else:
        error("Error: failure while creating engagement", response)

def upload_scan_findings(engagement_id, report_file_path):
    date = datetime.datetime.now()
    process = subprocess.Popen([
        "curl", "-sS", "-X", "POST", DD_SERVER_URL + "/api/v2/import-scan/",
        "-H",  "accept: application/json",
        "-H",  "Authorization: Token " + dd_auth_token,
        "-H",  "Content-Type: multipart/form-data",
        "-F",  "scan_date="+date.strftime("%F"),
        "-F",  "minimum_severity=Info",
        "-F",  "active=true",
        "-F",  "verified=true",
        "-F",  "scan_type=Meterian Scan",
        "-F",  "file=@"+report_file_path+";type=application/json",
        "-F",  "engagement=" + str(engagement_id),
        "-F",  "close_old_findings=false",
        "-F",  "push_to_jira=false"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    error = stderr.decode("utf-8").strip()
    output=stdout.decode("utf-8").strip()
    if output != "":
        js_out = json.loads(output)
        return js_out["test"]
    else:
        error("Error: failure while uploading scan results to Defect Dojo\n", error)

def parse_json(json_input):
    try:
        data = json_input.read()
        try:
            json_element = json.loads(str(data, 'utf-8'))
        except:
            json_element = json.loads(data)
    except:
        raise Exception("Invalid format")

    return json_element

def get_project_name_from_report(report_path):
    if os.path.isfile(report_path) == False:
        raise Exception("Report file does not exist")

    report = parse_json(open(report_path))
    if "name" in report:
        return report["name"]
    else:
        raise Exception("Could not parse project name from report file " + report_path)

def is_curl_installed():
    return which("curl") is not None

def is_dd_server_reachable():
    try:
        response = requests.get(DD_SERVER_URL + "/api/v2/")
        if response.status_code != 200:
            raise Exception()
    except:
        error("Error: Defect Dojo is not reachable")

if is_curl_installed():

    is_dd_server_reachable()

    script_args = sys.argv
    if len(script_args[1:]) > 0:
        report_path = sys.argv[1]

        project_name = get_project_name_from_report(report_path)
        product_id = find_product_by_project_name(project_name)
        print("Fetching for product matching project name:", project_name)
        if product_id != None:
            print("Found product (ID: " + str(product_id) + ")")
            engagement_id = create_ad_hoc_engagement(product_id)
            if engagement_id != None:
                print("Created new AdHoc import engagement (ID: " + str(engagement_id) + ")")
                test_id = upload_scan_findings(engagement_id, report_path)
                if test_id != None:
                    print("Imported findigs to test (ID: " + str(test_id) + ")")
    else:
        error("Error: expected JSON report path but nothing was provided")
else:
    error("Error: curl was not found, please install it")
