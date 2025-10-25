
import requests

url = "https://www.thesportsdb.com/api/v2/json/123/all/leagues"


response = requests.get(url)

if response.status_code == 200:
    print(response.json())
else:
    print(f"Request failed with status code: {response.status_code}")
						