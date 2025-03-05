"""Tool that pulls corporate information from ZoomInfo."""

import datetime
import http
import json
import os
import ssl

import certifi
import requests


# Initialize global variables
zoom_token_update_time = datetime.datetime.min
zoom_token = None


def get_token():
  """Retrieves an access token from ZoomInfo using username and password."""
  global zoom_token_update_time
  global zoom_token
  username = os.environ.get("ZOOMINFO_USERNAME")
  password = os.environ.get("ZOOMINFO_PASSWORD")

  context = ssl.create_default_context(cafile=certifi.where())

  minutes = (
      datetime.datetime.now() - zoom_token_update_time
  ).total_seconds() / 60
  conn = http.client.HTTPSConnection("api.zoominfo.com", context=context)

  if zoom_token is None or zoom_token == "" or minutes > 55:
    print("Refreshing zoominfo jwt token.")
    payload = json.dumps({"username": username, "password": password})
    headers = {"Content-Type": "application/json"}
    conn.request("POST", "/authenticate", payload, headers)
    res = conn.getresponse()
    auth = res.read()
    # set the token and update time
    try:
      zoom_token = json.loads(auth)["jwt"]
      zoom_token_update_time = datetime.datetime.now()
      print("Token update was a success. Resetting token and time.")
    except (json.JSONDecodeError, KeyError) as e:
      print(f"Error decoding JSON or missing key: {e}")
      print(f"Response content: {auth}")
      zoom_token = None  # Reset to none if there's an error
      return None

  return zoom_token


def search_companies(access_token, company_name):
  """Searches for companies by name."""
  endpoint = "/search/company"
  base_url = "https://api.zoominfo.com"  # Or your region specific base url
  headers = {
      "Authorization": f"Bearer {access_token}",
      "Content-Type": "application/json",
  }
  params = {"name": company_name}  # Parameters to pass to the api

  try:
    response = requests.get(
        f"{base_url}{endpoint}", headers=headers, params=params
    )
    response.raise_for_status()
    return response.json()

  except requests.exceptions.RequestException as e:
    print(f"Error during API call: {e}")
    return None


def enrich_company(company_domain: str) -> str:
  """Enriches company data from ZoomInfo.

  Args:
      company_domain: Domain name of the company such as google.com

  Returns:
      Enriched information about the company from ZoomInfo in JSON format
  """
  access_token = get_token()
  if access_token is None:
    print("Could not get access token")
    return None
  context = ssl.create_default_context(cafile=certifi.where())
  conn = http.client.HTTPSConnection("api.zoominfo.com", context=context)
  if company_domain and len(company_domain) > 3:
    company_filter = {"companyWebsite": f"http://www.{company_domain}"}
  else:
    print("Must provide either company_domain")
    return None

  payload = json.dumps({
      "matchCompanyInput": [company_filter],
      "outputFields": [
          "id",
          "ticker",
          "name",
          "website",
          "logo",
          "parentId",
          "parentName",
          "SocialMediaUrls",
          "revenue",
          "employeeCount",
          "phone",
          "street",
          "city",
          "state",
          "zipCode",
          "country",
          "metroArea",
          "companyStatus",
          "companyStatusDate",
          "descriptionList",
          "sicCodes",
          "naicsCodes",
          "competitors",
          "ultimateParentId",
          "ultimateParentName",
          "ultimateParentRevenue",
          "ultimateParentEmployees",
          "subUnitCodes",
          "subUnitType",
          "subUnitIndustries",
          "primaryIndustry",
          "industries",
          "alexaRank",
          "metroArea",
          "revenueRange",
          "employeeRange",
          "companyFunding",
          "recentFundingAmount",
          "recentFundingDate",
          "totalFundingAmount",
          "businessModel",
          "departmentBudgets",
          "employeeCountByDepartment",
      ],
  })
  headers = {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + access_token,
  }
  conn.request("POST", "/enrich/company", payload, headers)
  res = conn.getresponse()
  data = res.read()
  try:
    return json.loads(data.decode("utf-8"))
  except json.JSONDecodeError:
    print("Error: could not convert json from ZoomInfo")
    return None
