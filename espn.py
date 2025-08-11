import requests

response = requests.get("https://www.espn.com/nfl/team/stats/_/type/team/name/bal/season/2023/seasontype/2")

print(response)