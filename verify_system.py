import requests
import time
import os

def test_services():
    print("--- Starting Verification ---")
    
    # 1. Check Frontend
    try:
        resp = requests.get("http://localhost:5175", timeout=5)
        print(f"[SUCCESS] Frontend is up (Status: {resp.status_code})")
    except Exception as e:
        print(f"[FAILURE] Frontend unreachable: {e}")

    # 2. Check Backend Health
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        print(f"[SUCCESS] Backend Health Check: {resp.json()}")
    except Exception as e:
        print(f"[FAILURE] Backend Health unreachable: {e}")

    # 3. Test Ranking API
    print("\nTesting Ranking API with actual files...")
    
    # Use absolute paths
    jd_path = r"c:\Users\Divya\Desktop\RESUME SCREENING SYSTEM\data\sample_jds\jd_backend_python.txt"
    resumes_dir = r"c:\Users\Divya\Desktop\RESUME SCREENING SYSTEM\data\sample_resumes"
    
    payload = {
        "jd_path": jd_path,
        "resumes_dir": resumes_dir,
        "top_n": 5
    }
    
    print(f"Requesting rank for resumes in: {resumes_dir}")
    start_time = time.time()
    try:
        resp = requests.post("http://localhost:8000/rank", json=payload, timeout=60)
        end_time = time.time()
        
        if resp.status_code == 200:
            results = resp.json()
            print(f"[SUCCESS] Ranking API responded in {end_time - start_time:.2f} seconds.")
            
            top_candidates = results.get("top_candidates", [])
            print(f"\nFound {len(top_candidates)} candidates ranked:")
            for candidate in top_candidates:
                score = candidate.get('score', candidate.get('match_score', 0))
                status = candidate.get('match_status', 'N/A')
                print(f"- {candidate['name']}: Score {score:.4f}, Status: {status}")
        else:
            print(f"[FAILURE] Ranking API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[FAILURE] Ranking API call failed: {e}")

if __name__ == "__main__":
    test_services()
