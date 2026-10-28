import httpx
import json
import os
import time
import random

API_URL = "https://index-api.nawa.ncnp.gov.sa/api/v1/organizations"
OUTPUT_JSONL = "data_clean/nawa_raw_hierarchy.jsonl"
PAGE_SIZE = 50  # Optimal page size based on previous successful runs

def download_nawa_hierarchy():
    """
    Advanced & Resilient JSONL Scraper for GeoImpact KSA (Cromogentx).
    Incorporates anti-rate-limiting, error 500/429 handling, and sleep intervals.
    """
    print("🔄 Starting Resilient Structured API Data Extraction (JSONL Format)...")
    os.makedirs("data_clean", exist_ok=True)
    
    current_page = 1
    total_fetched = 0
    max_retries = 4
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Referer": "https://index.nawa.ncnp.gov.sa/",
        "Accept-Language": "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    with httpx.Client(headers=headers, timeout=30.0) as client, open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        while True:
            params = {
                "page_number": current_page,
                "page_size": PAGE_SIZE,
                "filter": "{}"
            }
            
            success = False
            orgs_list = []
            last_page = 1
            
            for attempt in range(max_retries):
                try:
                    response = client.get(API_URL, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        nested_data = data.get('data', {})
                        
                        if isinstance(nested_data, dict):
                            orgs_list = nested_data.get('data', [])
                            last_page = nested_data.get('last_page', 1)
                        else:
                            orgs_list = nested_data if isinstance(nested_data, list) else []
                            
                        success = True
                        break
                        
                    elif response.status_code in [500, 502, 503, 504, 429]:
                        sleep_time = 8 * (attempt + 1)
                        print(f"⚠️ Server load or rate limit (Status {response.status_code}) on page {current_page}. Waiting {sleep_time}s ({attempt+1}/{max_retries})...")
                        time.sleep(sleep_time)
                    else:
                        print(f"❌ Unexpected status code {response.status_code} at page {current_page}")
                        break
                except Exception as e:
                    print(f"🌐 Network fluctuation at page {current_page}: {e}. Retrying...")
                    time.sleep(5)
            
            if not success:
                print(f"⚠️ Skipping problematic page {current_page} temporarily and continuing...")
                current_page += 1
                continue
                
            if not orgs_list:
                print("🏁 All platform pages successfully exhausted!")
                break
                
            # Write each record directly in JSONL format to preserve deep nested hierarchy
            for item in orgs_list:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                total_fetched += 1
                
            print(f"✅ Successfully fetched page {current_page}. Total records so far: {total_fetched:,}")
            
            if current_page >= last_page or len(orgs_list) < PAGE_SIZE:
                print("🏁 Reached the end of the database completely.")
                break
                
            current_page += 1
            # Smart random sleep interval to prevent HTTP 429 rate limits
            time.sleep(random.uniform(3.0, 5.0))
            
    print(f"\n✨ Extraction completed successfully! Hierarchical data saved to: {OUTPUT_JSONL} with a total of {total_fetched:,} records.")

if __name__ == "__main__":
    download_nawa_hierarchy()