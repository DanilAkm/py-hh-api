import requests
import json
from time import time

HH_API_BASE='https://api.hh.ru'

class App:
    def __init__(self, client_id: str,
                 client_secret: str,
                 client_info: str,
                 host: str,
                 locale='RU',
                 app_token=None):

        self.client_id = client_id
        self.client_secret = client_secret
        self.client_info = client_info
        self.host = host
        self.locale = locale

        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }

        if app_token is None:
            response = requests.post(url=f'{HH_API_BASE}/token', data=data)
            app_token = response.json()['access_token']
        self.app_token = app_token

    def get_app_info(self):
        headers = {
            'Authorization': f'Bearer {self.app_token}',
            'HH-User-Agent': self.client_info
        }
        params = {
            'locale': self.locale,
            'host': self.host
        }
        response = requests.get(f'{HH_API_BASE}/me', params=params, headers=headers)
        return response.json()

    def get_link_for_authcode(self):
        return f'https://hh.ru/oauth/authorize?response_type=code&client_id={self.client_id}'

class Employee:

    def __init__(self, app: App, code=None, employee_data=None):

        if not isinstance(app, App):
            raise TypeError("Expected an instance of App")

        if employee_data is None:
            if code is None:
                raise TypeError("Missing auth code")
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            data = {
                'code': code,
                'client_id': app.client_id,
                'client_secret': app.client_secret,
                'grant_type': 'authorization_code'
            }

            response = requests.post(url=f'{HH_API_BASE}/token', headers=headers ,data=data).json()
            print(response)
            self.access_token = response['access_token']
            self.refresh_token = response['refresh_token']
            self.expires_at = time() + response['expires_in']
        else:
            self.access_token = employee_data['access_token']
            self.refresh_token = employee_data['refresh_token']
            self.expires_at = time() + employee_data['expires_at']

        self.appdata = app

    def renew_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }

        response = requests.post(url=f'{HH_API_BASE}/token', headers=headers, data=data).json()
        print(response)
        self.access_token = response['access_token']
        self.refresh_token = response['refresh_token']
        self.expires_at = time() + response['expires_in']
    
    def invalidate_token(self):
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.delete(url=f'{HH_API_BASE}/token', headers=headers)
        return response.json()
    
    def get_info(self):
        headers = {
            'HH-User-Agent': self.appdata.client_info,
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'locale': self.appdata.locale,
            'host': self.appdata.host
        }
        response = requests.get(url=f'{HH_API_BASE}/me', headers=headers, params=params)
        return response.json()

    def get_resumes(self):
        headers = {
            'HH-User-Agent': self.appdata.client_info,
            'Authorization': f'Bearer {self.access_token}'
        }
        params = {
            'locale': self.appdata.locale,
            'host': self.appdata.host
        }
        response = requests.get(url=f'{HH_API_BASE}/resumes/mine', headers=headers, params=params)
        return response.json()
    
    def get_vacancies_for_resume(self, resume_id: str, params: dict):
        headers = {
            'HH-User-Agent': self.appdata.client_info,
            'Authorization': f'Bearer {self.access_token}'
        }
        response = requests.get(url=f'{HH_API_BASE}/resumes/{resume_id}/similar_vacancies', headers=headers, params=params)
        return response.json()

        


if __name__ == '__main__':
    pass