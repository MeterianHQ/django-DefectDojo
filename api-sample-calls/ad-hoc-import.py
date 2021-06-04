import json
import requests
import os
import datetime
import sys
from urllib import parse

dd_auth_token = os.environ["DEFECT_DOJO_API_TOKEN"]

# Assuming all products are manually created on DD
def find_product_by_project_name(project_name):
    url = 'https://dd.meterian.io/api/v2/products/?' + parse.urlencode({"name": project_name})
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + dd_auth_token,
        "Content-Type": "application/json",
    }

    response = requests.get(url, headers=headers)
    if response.json()["count"] == 0:
        print("Error: no products found matching '", project_name, "'")
        return None
    
    return response.json()["results"][0]["id"]
    

def create_ad_hoc_engagement(product_id):
    url = 'https://dd.meterian.io/api/v2/engagements/'
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
        print("Error: failure while creating engagement", response)
        return None

def upload_scan_findings(engagement_id, report_file_path):
    # report_file_name = "report.json"
    # report_file_path = os.getcwd() + "/" + report_file_name
    # url = "http://localhost:8080/api/v2/import-scan/"
    # headers = {
    #     "accept": "application/json",
    #     "Authorization": "Token " + dd_auth_token,
    #     "Content-Type": "multipart/form-data",
    # }

    # files = {
    #     "file": (report_file_name, open(report_file_path, "rb"), "application/json")
    # }

    # date = datetime.datetime.now()
    # payload = {
    #     "scan_date": date.strftime("%F"),
    #     "minimum_severity": "Info" ,
    #     "active": True ,
    #     "verified": True ,
    #     "scan_type": "Meterian Scan" ,
    #     "engagement": engagement_id ,
    #     "close_old_findings": False ,
    #     "push_to_jira": False
    # }

    # response = requests.post(url, headers=headers, data=payload, files=files)
    # if response.status_code == 201:
    #     return response.json()["test"]
    # else:
    #     print("Error: failure while uploading scan results to Defect Dojo", response)
    #     return None

    output=os.popen("./import-findings.sh" + " " + report_file_path  + " " + str(engagement_id)).read()
    if output != "":
        js_out = json.loads(output)
        return js_out["test"]
    else:
        print("Error: failure while uploading scan results to Defect Dojo")
        return None

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

script_args = sys.argv
if len(script_args[1:]) > 0:
    report_path = sys.argv[1]

    project_name = get_project_name_from_report(report_path)
    product_id = find_product_by_project_name(project_name)
    if product_id != None:
        print("Found product:", product_id)
        engagement_id = create_ad_hoc_engagement(product_id)
        if engagement_id != None:
            print("Created new AdHoc import engagement:", engagement_id)
            test_id = upload_scan_findings(engagement_id, report_path)
            if test_id != None:
                print("Imported findigs to test:", test_id)
else:
    print("Error: expected JSON report path but nothing was provided")
