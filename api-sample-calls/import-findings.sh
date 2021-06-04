#!/bin/bash

path_to_report="$1"
curl -sS -X POST "http://localhost:8080/api/v2/import-scan/" \
-H  "accept: application/json" \
-H  "Authorization: Token $DEFECT_DOJO_API_TOKEN" \
-H  "Content-Type: multipart/form-data" \
-F  "scan_date="$(date +"%F")"" \
-F  "minimum_severity=Info" \
-F  "active=true" \
-F  "verified=true" \
-F  "scan_type=Meterian Scan" \
-F  "file=@"$path_to_report";type=application/json" \
-F  "engagement=$2" \
-F  "close_old_findings=false" \
-F  "push_to_jira=false" 2>> /dev/null