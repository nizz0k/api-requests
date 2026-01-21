import requests
import json
import base64
import time
import sys  # Required for the progress tracker

# CONFIGURATION
# ---------------------------------------------------------
DOMAIN = "lpc.qi-cms.com"
USERNAME = "kendallndesign@gmail.com"
PASSWORD = "NickKendall"  # Update with your actual password
PROJECT_ID = 63 
OUTPUT_FILE = "project_63_readable_dump.json"

# ESTIMATE FOR PROGRESS BAR
# Based on your previous mention of ~127,000 records. 
# This is used only for the percentage calculation.
TOTAL_ESTIMATE = 127000 

# API PARAMETERS
BASE_URL = f"https://{DOMAIN}/api/get/object"
FILTER_FIELD = "project_id"
FILTER_VALUE = PROJECT_ID

# FIELD SELECTION
# Using the human-readable fields you successfully verified via curl
# Sources: [1], [2], [3], [4], [5]
fields_list = [
    "object_name", 
    "object_number",       
    "context.name",        # Resolves to text (e.g. "Context 101")
    "object_class.name",   # Resolves to text (e.g. "Ceramic")
    "start_date"
]

def encode_fields_param(fields):
    """
    Encodes the fields list to Base64 with Qi-specific character replacements.
    Source: [6]
    """
    raw_string = ",".join(fields)
    encoded_bytes = base64.b64encode(raw_string.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')
    # Replace special characters: + -> -, / -> _, = -> ~
    safe_encoded_str = encoded_str.replace('+', '-').replace('/', '_').replace('=', '~')
    return f"base64:{safe_encoded_str}"

def fetch_all_records():
    all_records = []
    offset = 0
    per_page = 100 # Optimized for speed with _skip_relationship
    more_records = True

    # Generate encoded parameter
    fields_param = encode_fields_param(fields_list)
    
    print(f"Targeting Project {PROJECT_ID}. Estimated records: {TOTAL_ESTIMATE}")
    print("Starting extraction... (Press Ctrl+C to stop early)")

    start_time = time.time()

    while more_records:
        # Construct URL with _fields and _skip_relationship
        # Source: [7], [5]
        url = (
            f"{BASE_URL}/{FILTER_FIELD}/{FILTER_VALUE}"
            f"/_per_page/{per_page}/_offset/{offset}"
            f"/_sort_by/id/_sort_direction/ASC"
            f"/_fields/{fields_param}"
            f"/_skip_relationship/1" # Critical for performance [7]
        )

        try:
            response = requests.get(url, auth=(USERNAME, PASSWORD))
            response.raise_for_status()
            data = response.json()

            count = len(data)

            if count == 0:
                more_records = False
                # Print a clean newline when finished so the next print doesn't overwrite
                sys.stdout.write("\n") 
                print(f"Finished. Total records retrieved: {len(all_records)}")
            else:
                all_records.extend(data)
                
                # SAFETY LOGIC: Always increment by the ACTUAL number received [8]
                offset += count
                
                # PROGRESS TRACKER LOGIC
                current_total = len(all_records)
                percent = (current_total / TOTAL_ESTIMATE) * 100
                
                # \r returns the cursor to the start of the line
                status_msg = f"\rProgress: [{percent:.2f}%] {current_total} / {TOTAL_ESTIMATE} records fetched..."
                sys.stdout.write(status_msg)
                sys.stdout.flush()

        except requests.exceptions.RequestException as e:
            sys.stdout.write("\n") # Move to new line to print error
            print(f"Network Error at offset {offset}: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
            # We do NOT break here, we let the loop retry the same offset
            continue
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            print("Extraction stopped by user. Saving what we have...")
            break

    # SAVE TO FILE
    duration = time.time() - start_time
    print(f"Extraction took {duration/60:.2f} minutes.")
    print(f"Saving to {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, ensure_ascii=False, indent=4)
    
    print("Done!")

if __name__ == "__main__":
    fetch_all_records()