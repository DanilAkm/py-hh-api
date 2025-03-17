from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from hh_api import hh

load_dotenv()
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
app_token = os.getenv('APP_TOKEN')
mongo_connection= os.getenv('MONGO_CONNECTION')

app = FastAPI()

client = MongoClient(mongo_connection)
db = client["users"]
users = db["users"]

@app.post("/checkmail")
async def check_email(email: str = Form(...)):
    if users.find_one({"email": email}):
        return "You are already mine"
    else:
        users.insert_one({"email": email})
        return RedirectResponse(
          url=f"https://hh.ru/oauth/authorize?response_type=code&client_id={client_id}",
          status_code=303
        )

@app.get("/oauth")
async def oauth_callback(code: str):
    # Here you can process the OAuth code (e.g., exchange for a token)
    appdata = {
        'client_id': client_id,
        'client_secret': client_secret,
        'client_info': 'boyceing/1 (boyceing@boyceing.ru)',
        'host': 'hh.ru',
        'locale': 'RU'
    }
    app = hh.App(appdata, app_token=app_token)
    emp = hh.Employee(app, code)
    user_profile = emp.get_info()
    user_profile['access_token'] = emp.access_token
    user_profile['refresh_token'] = emp.refresh_token
    user_profile['expires_at'] = emp.expires_at
    query_filter = {'email' : emp.get_info()['email']}
    update_operation = { '$set' : user_profile }
    result = users.update_one(query_filter, update_operation)

    return f"I have your soul"


#  uvicorn register:app --host 0.0.0.0 --port 5000 --reload