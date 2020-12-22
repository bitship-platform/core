import requests,json

url = "http://api.tortoisecommunity.co:8000/private/user/1231231231231/"
headers = {"Authorization": "Token 6ec37450b31cc95b628bbd3630dae820107ef077", "Content-type": "application/json"}
data = {"id":1231231231231,"name":"Ryuga","tag":"0001","avatar":"","verified":True,"perks":1000}
r = requests.get(url=url,headers=headers,data=json.dumps(data))
print(r.text)
