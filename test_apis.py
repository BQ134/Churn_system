import requests
import json

# Test the analytics APIs
base_url = "http://localhost:5000"

apis_to_test = [
    "/api/analytics/summary",
    "/api/analytics/trend",
    "/api/analytics/feature-importance", 
    "/api/analytics/confidence-distribution",
    "/api/analytics/feature-averages"
]

print("Testing Analytics APIs...")
print("=" * 50)

for api in apis_to_test:
    try:
        response = requests.get(f"{base_url}{api}")
        print(f"\n{api}:")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Data: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"\n{api}:")
        print(f"Error: {e}")

print("\n" + "=" * 50)
print("API testing complete!") 