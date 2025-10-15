import http.client
import json
import os
import re
import ssl
import subprocess
from urllib.parse import urlparse


def runAzure(subscription_id, start, end, path_to_output, log, dry=False):
    if not dry:
        ssl.SSLContext.verify_mode = property(
            lambda self: ssl.CERT_OPTIONAL, lambda self, newval: None
        )

        conn = http.client.HTTPSConnection("management.azure.com")
        subprocess.run(f"az account set --subscription {subscription_id}", shell=True)
        # results = subprocess.run(f'az account show --query id" -o tsv', shell=True, stdout=subprocess.PIPE)
        # subscription_id = results.stdout.decode()[:-1]
        # 80dc7a6b-df94-44be-a235-7e7ade335a3c
        req_path = (
            f"/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query"
        )
        req_params = "api-version=2023-03-01"
        body = {
            "dataset": {
                "granularity": "Daily",
                "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": "ServiceName"}],
            },
            "timeframe": "custom",
            "timePeriod": {"from": str(start), "to": str(end)},
            "type": "ActualCost",
        }
        results = subprocess.run(
            "az account get-access-token --resource=https://management.azure.com/ --query accessToken -o tsv",
            shell=True,
            stdout=subprocess.PIPE,
        )

        bearer_token = "Bearer " + results.stdout.decode().strip()
        # print(bearer_token)
        print("Fetching data for subscription: " + subscription_id)

        next_link = req_path + "?" + req_params
        is_first_request = True
        all_rows = []

        while next_link:
            parsed_url = urlparse(next_link)
            host = parsed_url.netloc or "management.azure.com"
            conn = http.client.HTTPSConnection(host)

            path_and_query = parsed_url.path + (
                "?" + parsed_url.query if parsed_url.query else ""
            )

            method = "POST" if is_first_request else "GET"
            headers = {"Authorization": bearer_token}
            if method == "POST":
                headers["Content-Type"] = "application/json"

            request_body = json.dumps(body) if is_first_request else None
            conn.request(method, path_and_query, headers=headers, body=request_body)

            response = conn.getresponse()
            data = json.loads(response.read().decode())

            if "error" in data:
                log(msg=json.dumps(data["error"]), tag="Azure error")
                return []

            all_rows.extend(data["properties"]["rows"])
            next_link = data.get("properties", {}).get("nextLink") or data.get(
                "nextLink"
            )

            is_first_request = False

        vals = all_rows

        with open(f"{path_to_output}/azure_output_raw.json", "w") as outfile:
            outfile.write(json.dumps({"properties": {"rows": all_rows}}, indent=4))

        new_vals = []
        for val in vals:
            nv = {
                "Date": str(val[1]),
                "Cost": str(val[0]),
                "Group": val[2],
                "Currency": val[3],
            }
            s = nv["Date"]
            if re.match("^[0-9]*$", s) and len(s) == 8:
                nv["Date"] = s[0:4] + "-" + s[4:6] + "-" + s[6:8]
            new_vals.append(nv)
        upload = {
            "metadata": {"provider": "azure", "account": subscription_id},
            "data": new_vals,
        }
    # End dry block

    az_output_file = os.path.join(path_to_output, f"az-cost-{subscription_id}.json")

    if not dry:
        with open(az_output_file, "w") as outfile:
            outfile.write(json.dumps(upload, indent=4))

    return az_output_file
