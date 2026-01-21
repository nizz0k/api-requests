import requests
import json
import base64

# CONFIGURATION
# ---------------------------------------------------------
DOMAIN = "lpc.qi-cms.com"
USERNAME = "kendallndesign@gmail.com"
PASSWORD = "NickKendall"
PROJECT_ID = 63  # From conversation history
OUTPUT_FILE = "project_63_custom_fields.json"

# API PARAMETERS
BASE_URL = f"https://{DOMAIN}/api/get/object"
FILTER_FIELD = "project_id"
FILTER_VALUE = PROJECT_ID

# FIELD SELECTION
# We map requested names to Schema names (using dot notation for related tables)
# Sources: [1], [2], [5], [6], [3]
fields_list = [
    "object_name",
    "context_id",         # Direct field from object table [4]
    "object_class_id",    # Direct field from object table [5]
    "start_date"
]

def encode_fields_param(fields):
    """
    Encodes the comma-separated list of fields into the specific 
    Base64 format required by the Qi API [7].
    """
    # 1. Join fields with commas
    raw_string = ",".join(fields)
    
    # 2. Standard Base64 Encode
    encoded_bytes = base64.b64encode(raw_string.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')
    
    # 3. Apply Qi-specific character replacements
    # '+' -> '-', '/' -> '_', '=' -> '~'
    safe_encoded_str = encoded_str.replace('+', '-').replace('/', '_').replace('=', '~')
    
    # 4. Prepend the required prefix
    return f"base64:{safe_encoded_str}"

def fetch_records():
    all_records = []
    offset = 0
    per_page = 10
    more_records = True

    # Generate the encoded fields parameter once
    fields_param = encode_fields_param(fields_list)
    print(f"Requesting fields: {fields_list}")
    print(f"Encoded parameter: {fields_param}")

    while more_records:
        # Construct URL with pagination, sorting, AND the _fields parameter
        url = (
            f"{BASE_URL}/{FILTER_FIELD}/{FILTER_VALUE}"
            f"/_per_page/{per_page}/_offset/{offset}"
            f"/_sort_by/id/_sort_direction/ASC"
            f"/_fields/{fields_param}"
        )

        try:
            response = requests.get(url, auth=(USERNAME, PASSWORD))
            response.raise_for_status()
            
            data = response.json()

            if not data:
                more_records = False
                print("No more records found.")
            else:
                count = len(data)
                print(f"Fetched {count} records (Offset: {offset})")
                all_records.extend(data)
                offset += per_page

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break

    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=4)
    
    print(f"Saved {len(all_records)} records to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_records()