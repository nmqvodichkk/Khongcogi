import time
import requests

# URL để ping liên tục
url = "https://httpbin.org/get"

def keep_alive():
    while True:
        try:
            response = requests.get(url)
            print(f"Keepalive request sent: {response.status_code}")
        except Exception as e:
            print(f"Error while sending keepalive request: {e}")
        
        # Thực hiện request mỗi 5 phút (300 giây)
        time.sleep(300)

if __name__ == "__main__":
    keep_alive()
