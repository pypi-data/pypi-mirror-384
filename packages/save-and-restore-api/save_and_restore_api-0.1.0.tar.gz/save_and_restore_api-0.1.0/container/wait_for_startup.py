import time

import httpx

t_wait = 120
BASE_URL = "http://localhost:8080/save-restore"
root_node_uid = "44bef5de-e8e6-4014-af37-b8f6c8a939a2"

if __name__ == "__main__":
    t_start = time.time()
    url = f"/node/{root_node_uid}"
    with httpx.Client(base_url=BASE_URL, timeout=1) as client:
        while time.time() - t_start < t_wait:
            try:
                response = client.request("GET", url)
                if response.status_code == 200:
                    print("Success: save-and-restore server is up")
                    exit(0)
            except Exception:
                pass

    print(f"TIMEOUT: save-and-restore server failed to start in {t_wait} seconds")
    exit(1)
