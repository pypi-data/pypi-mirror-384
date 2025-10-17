import json
import requests
from requests.auth import HTTPBasicAuth

user = "kbtoku"
pw = "abcxyz"

service_type = "ingest"

endpoint = "/services/available.json?serviceType=org.opencastproject." + str(
    service_type
)
url = "%s%s" % ("http://opencast-dev.bibliothek.kit.edu:8080", endpoint)

print(url)
res = requests.get(url, auth=HTTPBasicAuth(user, pw))

if res.ok:
    print(res.json())

    services = (json.loads(res.content).get("services") or {}).get("service", [])

else:
    print("FAIL!")
