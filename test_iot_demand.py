#!/usr/bin/env python3
"""
Test script to send IoT demand data to /api/iot/demand endpoint
Simulates ESP32 buyer device sending demand via potentiometer
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "test_token_buyer"

# Test data - simulate potentiometer reading 2.5 kWh
test_demand = {
    "auth_token": AUTH_TOKEN,
    "device_id": "ESP32_BUYER_002",
    "house_id": "HOUSE_FDR12_002",
    "demand_kwh": 2.5,
    "signal_strength": 85
}

print("=" * 60)
print("Testing IoT Demand Endpoint")
print("=" * 60)
print(f"\nSending POST to: {BASE_URL}/api/iot/demand")
print(f"Payload: {json.dumps(test_demand, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/iot/demand",
        json=test_demand,
        timeout=10
    )
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✓ POST request successful!")
        
        # Now test the GET endpoint
        print("\n" + "=" * 60)
        print("Testing IoT Demand Status Endpoint")
        print("=" * 60)
        print(f"\nSending GET to: {BASE_URL}/api/iot/demand-status/HOUSE_FDR12_002")
        
        time.sleep(1)  # Give backend time to process
        
        response = requests.get(
            f"{BASE_URL}/api/iot/demand-status/HOUSE_FDR12_002",
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ GET request successful!")
            print(f"  - Current Demand: {data.get('current_demand_kwh')} kWh")
            print(f"  - Device Online: {data.get('device_online')}")
            print(f"  - Allocation: {data.get('allocation')}")
    else:
        print(f"\n✗ POST request failed with status {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("\n✗ Connection Error: Could not connect to backend at {BASE_URL}")
    print("   Make sure the backend is running: python main.py")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
