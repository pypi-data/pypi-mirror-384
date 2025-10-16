import requests
import json
from mcp.server.fastmcp import FastMCP
import logging
import os
from pathlib import Path

mcp = FastMCP("Taiwan_weather")

# Get the directory where this module is located
MODULE_DIR = Path(__file__).parent

def get_api_key(filename='GOV_api_key.txt'):
    """Try to load API key from file in current directory or module directory"""
    # Try current directory first
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as file:
                api_key = file.read().strip()
                if api_key:
                    return api_key
        except FileNotFoundError:
            pass
    
    # Try module directory
    module_file = MODULE_DIR / filename
    if module_file.exists():
        try:
            with open(module_file, 'r') as file:
                api_key = file.read().strip()
                if api_key:
                    return api_key
        except FileNotFoundError:
            pass
    
    return None

def load_alias_county_name(filename='aliased.txt'):
    """Load county name aliases from file"""
    alias_county_name = {}
    filepath = MODULE_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            key, value = line.strip().split(',')
            alias_county_name[key] = value
    return alias_county_name

def load_counties(filename='counties.txt'):
    """Load list of available counties from file"""
    filepath = MODULE_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file]

alias_county_name = load_alias_county_name()
counties = load_counties()

BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"  # Updated base URL
API_KEY = get_api_key()  # Retrieve API key from file

if not API_KEY :
    logging.error("API key not found. Please ensure 'GOV_api_key.txt' exists and contains the API key.")
    raise ValueError("API key not found. Please ensure 'GOV_api_key.txt' exists and contains the API key.")
if API_KEY =="":
    logging.error("API key is empty. Please ensure 'GOV_api_key.txt' contains a valid API key.")
    raise ValueError("API key is empty. Please ensure 'GOV_api_key.txt' contains a valid API key.")


def normalize_weather_data(raw_data: dict) -> dict:
    """將氣象局爛格式轉成結構化良好的 JSON"""
    result = {}

    # 資料集描述
    dataset_desc = raw_data.get("records", {}).get("datasetDescription", "")
    result["datasetDescription"] = dataset_desc
    result["locations"] = []

    for loc in raw_data.get("records", {}).get("location", []):
        location_name = loc.get("locationName")
        elements = loc.get("weatherElement", [])

        # 先整理各 elementName 對應時間資料
        timeline_map = {}
        for elem in elements:
            elem_name = elem["elementName"]
            for t in elem["time"]:
                start = t["startTime"]
                end = t["endTime"]
                param = t["parameter"]

                key = (start, end)
                if key not in timeline_map:
                    timeline_map[key] = {
                        "startTime": start,
                        "endTime": end
                    }

                # 動態建立 element 內容，只加有值的欄位
                entry = {}
                name = param.get("parameterName")
                value = param.get("parameterValue")
                unit = param.get("parameterUnit")

                if name is not None:
                    entry["value"] = name
                #if value is not None:
                #    entry["index"] = value
                if unit is not None:
                    entry["unit"] = unit

                # 只有當 entry 有內容才加入
                if entry:
                    timeline_map[key][elem_name] = entry

        # 轉成 list 並依時間排序
        timeline = sorted(timeline_map.values(), key=lambda x: x["startTime"])

        result["locations"].append({
            "locationName": location_name,
            "timeline": timeline
        })

    return result
#@app.route('/get_weather', methods=['GET'])
@mcp.tool()
def get_weather(given_location: str):
    selected_county = given_location
    global alias_county_name
    if selected_county in alias_county_name:
        selected_county = alias_county_name[selected_county]

    if not selected_county:
        return json.dumps({"error": "selected_county parameter is required"}, ensure_ascii=False)
    # Construct the URL
    url = f"{BASE_URL}?Authorization={API_KEY}&format=JSON&locationName={selected_county}"  # Use API key dynamically

    try:
        # Fetch data from the API
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        data=normalize_weather_data(data)
        # Return the response with ensure_ascii=False to keep non-ASCII characters
        return json.dumps(data, ensure_ascii=False)
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

@mcp.tool()
def list_available_locations():
    # Return the list of available locations
    global counties,alias_county_name
    return json.dumps({"available_locations": counties,"alias_counties": alias_county_name}, ensure_ascii=False)

    #exists = location in counties or location in alias_county_name
  
    #return Response(json.dumps({"location": location, "exists": exists}, ensure_ascii=False), mimetype='application/json')

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()