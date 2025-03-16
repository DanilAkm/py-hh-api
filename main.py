from hh_api import HH
from dotenv import load_dotenv
import os
import pymongo
import time

load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
app_token = os.getenv('APP_TOKEN')
mongo_connection= os.getenv('MONGO_CONNECTION')

myclient = pymongo.MongoClient(mongo_connection)
mydb = myclient["users"]
users = mydb["users"]

app = HH.App(client_id, client_secret, 'boyceing/1 (boyceing@boyceing.ru)', 'hh.ru', app_token=app_token)

target_user = 'akmd.uk@gmail.com'
userinfo = users.find_one({'email': target_user}, {'_id': False})

#  User not found in database
if userinfo is None:
  print(app.get_link_for_authcode())
  emp = HH.Employee(app, code=input())

  user_profile = emp.get_info()
  user_profile['access_token'] = emp.access_token
  user_profile['refresh_token'] = emp.refresh_token
  user_profile['expires_at'] = emp.expires_at

  users.insert_one(user_profile)

#  Found. If token expired - renew 
else:
  emp = core.Employee(app, employee_data=userinfo)
  if userinfo['expires_at'] < time.time():
    emp.renew_token()
    query_filter = {'email' : target_user}
    update_operation = { '$set' : {
        'access_token': emp.access_token,
        'refresh_token': emp.refresh_token,
        'expires_at': emp.expires_at
      }
    }
    result = users.update_one(query_filter, update_operation)

# https://api.hh.ru/openapi/redoc#tag/Poisk-vakansij-dlya-soiskatelya/operation/get-vacancies-similar-to-resume
search_filter = {
  'salary': 200000
}

resume_id = emp.get_resumes()['items'][0]['id']
print(emp.get_vacancies_for_resume(resume_id, search_filter))
