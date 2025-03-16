"""
Testing script for hh api
"""

import os
import time
import json
from dotenv import load_dotenv
import pymongo
from hh_api import hh

load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
app_token = os.getenv('APP_TOKEN')
mongo_connection= os.getenv('MONGO_CONNECTION')

myclient = pymongo.MongoClient(mongo_connection)
mydb = myclient["users"]
users = mydb["users"]

appdata = {
    'client_id': client_id,
    'client_secret': client_secret,
    'client_info': 'boyceing/1 (boyceing@boyceing.ru)',
    'host': 'hh.ru',
    'locale': 'RU'
}

app = hh.App(appdata, app_token=app_token)

TARGET_USER = 'akmd.uk@gmail.com'
userinfo = users.find_one({'email': TARGET_USER}, {'_id': False})

#    User not found in database
if userinfo is None:
    print(app.get_link_for_authcode())
    emp = hh.Employee(app, code=input())

    user_profile = emp.get_info()
    user_profile['access_token'] = emp.access_token
    user_profile['refresh_token'] = emp.refresh_token
    user_profile['expires_at'] = emp.expires_at

    users.insert_one(user_profile)

#    Found. If token expired - renew
else:
    emp = hh.Employee(app, employee_data=userinfo)
    if userinfo['expires_at'] < time.time():
        emp.renew_token()
        query_filter = {'email' : TARGET_USER}
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

def pretty_print(json_data):
    """
    Make json readable
    """
    print(json.dumps(json_data, indent=4, sort_keys=False, ensure_ascii=False))

def filter_vacancies(vacancies_json):
    """
    pretty print vacancy list
    """
    important_info = []

    for vacancy in vacancies_json.get("items", []):
        important_info.append({
            "Id": vacancy.get("id"),
            "Title": vacancy.get("name"),
            "Company": vacancy.get("employer", {}).get("name"),
            "Location": vacancy.get("area", {}).get("name"),
            "Salary": (
                f"""{vacancy['salary']['from']} -
                {vacancy['salary']['to']} {vacancy['salary']['currency']}"""
                if vacancy.get("salary") else "Not specified"
            ),
            "Requirements": vacancy.get("snippet", {}).get("requirement", "No details"),
            "Link": vacancy.get("url"),
            "Human link": vacancy.get("alternate_url"),
            "Letter": vacancy.get("response_letter_required")
        })
    out = json.dumps(important_info, indent=4, ensure_ascii=False)
    print(out)
    return out

# pretty_print(emp.get_vacancies_for_resume(resume_id, search_filter))
filter_vacancies(emp.get_vacancies_for_resume(resume_id, search_filter))
