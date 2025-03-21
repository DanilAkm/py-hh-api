"""
Copyright (c) Danil Akhmadiev (@boyceing)

This module is licensed under the MIT License.
"""

from time import time
import requests

HH_API_BASE = "https://api.hh.ru"


class App:
    """
    Represents an application interacting with the HH.ru API.

    Handles authentication and provides methods to retrieve application-related data.
    """

    def __init__(self, config: dict, app_token=None):
        """
        Initializes the App instance.

        Args:
        config (dict): A dictionary containing client ID,secret, info, and host locale settings.
        app_token (str, optional): An existing application token. Defaults to None.
        """

        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.client_info = config.get("client_info")
        self.host = config.get("host")
        self.locale = config.get("locale")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        if app_token is None:
            response = requests.post(url=f"{HH_API_BASE}/token", data=data, timeout=10)
            app_token = response.json()["access_token"]
        self.app_token = app_token

    def get_app_info(self):
        """
        Retrieves information about the authenticated application.

        Returns:
            dict: Application details from the API.
        """

        headers = {
            "Authorization": f"Bearer {self.app_token}",
            "HH-User-Agent": self.client_info,
        }
        params = {"locale": self.locale, "host": self.host}
        response = requests.get(
            f"{HH_API_BASE}/me", params=params, headers=headers, timeout=10
        )
        return response.json()

    def get_link_for_authcode(self):
        """
        Generates a link for user authorization.

        Returns:
            str: The authorization URL.
        """

        return f"https://hh.ru/oauth/authorize?response_type=code&client_id={self.client_id}"


class Employee:
    """
    Represents an authenticated employee on the HH.ru platform.

    Handles authentication, token management,
    and provides methods to retrieve employee-related data.
    """

    def __init__(self, app: App, code=None, employee_data=None):
        """
        Initializes the Employee instance.

        Args:
            app (App): The application instance for authentication.
            code (str, optional): The authorization code for obtaining a token.
            employee_data (dict, optional): Existing employee authentication data.

        Raises:
            TypeError: If app is not an instance of App
            or if required authentication data is missing.
        """

        if not isinstance(app, App):
            raise TypeError("Expected an instance of App")

        if employee_data is None:
            if code is None:
                raise TypeError("Missing auth code")
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            data = {
                "code": code,
                "client_id": app.client_id,
                "client_secret": app.client_secret,
                "grant_type": "authorization_code",
            }

            response = requests.post(
                url=f"{HH_API_BASE}/token", headers=headers, data=data, timeout=10
            ).json()
            self.access_token = response["access_token"]
            self.refresh_token = response["refresh_token"]
            self.expires_at = time() + response["expires_in"]
        else:
            self.access_token = employee_data["access_token"]
            self.refresh_token = employee_data["refresh_token"]
            self.expires_at = time() + employee_data["expires_at"]

        self.appdata = app

    def renew_token(self):
        """
        Renews the employee's authentication token using the refresh token.
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {"refresh_token": self.refresh_token, "grant_type": "refresh_token"}

        response = requests.post(
            url=f"{HH_API_BASE}/token", headers=headers, data=data, timeout=10
        ).json()
        print(response)
        self.access_token = response["access_token"]
        self.refresh_token = response["refresh_token"]
        self.expires_at = time() + response["expires_in"]

    def invalidate_token(self):
        """
        Invalidates the employee's authentication token.

        Returns:
            dict: API response confirming token invalidation.
        """

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.delete(
            url=f"{HH_API_BASE}/token", headers=headers, timeout=10
        )
        return response.json()

    def get_info(self):
        """
        Retrieves information about the authenticated employee.

        Returns:
            dict: Employee details from the API.
        """

        headers = {
            "HH-User-Agent": self.appdata.client_info,
            "Authorization": f"Bearer {self.access_token}",
        }
        params = {"locale": self.appdata.locale, "host": self.appdata.host}
        response = requests.get(
            url=f"{HH_API_BASE}/me", headers=headers, params=params, timeout=10
        )
        return response.json()

    def get_resumes(self):
        """
        Retrieves the authenticated employee's resumes.

        Returns:
            dict: List of resumes associated with the employee.
        """

        headers = {
            "HH-User-Agent": self.appdata.client_info,
            "Authorization": f"Bearer {self.access_token}",
        }
        params = {"locale": self.appdata.locale, "host": self.appdata.host}
        response = requests.get(
            url=f"{HH_API_BASE}/resumes/mine",
            headers=headers,
            params=params,
            timeout=10,
        )
        return response.json()

    def get_vacancies_for_resume(self, resume_id: str, params: dict):
        """
        Retrieves similar vacancies for a given resume.

        Args:
            resume_id (str): The ID of the resume.
            params (dict): Additional parameters for filtering vacancies.

        Returns:
            dict: List of similar vacancies.
        """

        headers = {
            "HH-User-Agent": self.appdata.client_info,
            "Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(
            url=f"{HH_API_BASE}/resumes/{resume_id}/similar_vacancies",
            headers=headers,
            params=params,
            timeout=10,
        )
        return response.json()

    def apply_for_vacancy(self, resume_id: str, vacancy_id: str, message: str) -> int:
        """
        Sends application for a give vacancy with a given resume

        Args:
            resume_id (str): The ID if the resume.
            vacancy_id (str): the ID of the vacancy.

        Returns:
            int: http response code
        """
        headers = {
            "HH-User-Agent": self.appdata.client_info,
            "Authorization": f"Bearer {self.access_token}",
        }
        data = {
            'resume_id': resume_id,
            'vacancy_id': vacancy_id,
            'message': message
        }
        params = {"locale": self.appdata.locale, "host": self.appdata.host}

        response = requests.post(
            url=f"{HH_API_BASE}/negotiations",
            headers=headers,
            params=params,
            data=data,
            timeout=10,
        )
        print(response.status_code)
        if response.status_code == 403:
            print(response.json())
        return response.status_code

    def get_negotiations(self, params: dict):
        """
        Returns active negotiations base on filter

        Args:
            params (dict): search filters
        Returns:
            filtered negotiations
        """
        headers = {
            "HH-User-Agent": self.appdata.client_info,
            "Authorization": f"Bearer {self.access_token}",
        }
        response = requests.get(
            url=f"{HH_API_BASE}/negotiations",
            headers=headers,
            params=params,
            timeout=10,
        )
        return response.json()

    def get_negotitation_texts(self, negotiation_id: str, text_only = False) -> dict:
        """
        Returns message history in negotiation

        Atgs:
            negotiation_id (str):
            text_only (bool):

        Returns:
            pohuy
        """
        headers = {
            "HH-User-Agent": self.appdata.client_info,
            "Authorization": f"Bearer {self.access_token}",
        }
        params = {
            "locale": self.appdata.locale,
            "host": self.appdata.host,
            "with_text_only": text_only,
        }
        response = requests.get(
            url=f'{HH_API_BASE}/negotiations/{negotiation_id}/messages',
            headers=headers,
            params=params
        )
        return response.json()

if __name__ == "__main__":
    pass
