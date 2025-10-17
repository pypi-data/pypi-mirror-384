import requests
from flask import Flask,request
import json
import loggerutility as logger 

class Save_Transaction:
    def generate_token(self, base_url, app_id, user_code, password, is_pwd_encrypt, data_format):
        url = f"{base_url}/ibase/rest/E12ExtService/login"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            "USER_CODE": user_code,
            "PASSWORD": password,
            "IS_PWD_ENCRYPT": str(is_pwd_encrypt).lower(),
            "APP_ID": app_id,
            "DATA_FORMAT": data_format
        }
        logger.log(f"url:; {url}")
        logger.log(f"payload:; {payload}")

        response = requests.post(url, data=payload, headers=headers)
        logger.log(f"response:: {response}")
        if response.status_code == 200:
            logger.log(f"response:: {response.text}")
            logger.log(f"response JSON:: {response.json()}")
            response_data = response.json()  # Parse the response JSON
            results = response_data.get("Response", {}).get("results", "")
            results_dict = json.loads(results)  # Parse the JSON-encoded string
            token_id = results_dict.get("TOKEN_ID")
            # token_id = response.json().get("TOKEN_ID")
            logger.log(f"token_id:; {token_id}")
            return token_id
        else:
            print(f"Failed to generate token. Status Code: {response.status_code}, Response: {response.text}")
            return None

    def email_save_transaction(self, input_data):
        logger.log(f"input_data:: {input_data}")
        data = request.get_data('jsonData', None)
        data = json.loads(data[9:])
        logger.log(f"jsondata:: {data}")

        base_url = data.get("base_url")
        token_id = data.get("token_id")
        obj_name = data.get("obj_name")
        enterprise_name = data.get("enterprise_name")
        app_id = data.get("app_id")

        url = f"{base_url}/ibase/rest/EDIService/setData/{obj_name}/{enterprise_name}/{app_id}/writefilesavetrans"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'TOKEN_ID': token_id
        }
        payload = {
            "INPUT_DATA": input_data
        }

        response = requests.post(url, data=payload, headers=headers)
        logger.log(f"response:: {response}")
        logger.log(f"response.status_code:: {response.status_code}")
        if response.status_code == 200:
            json_response = response.json()
            return {"status": "Success", "message": json_response}
        else:
            print(f"Failed to push transaction. Status Code: {response.status_code}, Response: {response.text}")
            return {"success": "Failed", "message": "failed in transaction"}
        
    def save_trans(self):

        data = request.get_data('jsonData', None)
        data = json.loads(data[9:])
        logger.log(f"jsondata:: {data}")

        base_url = data.get("base_url")
        app_id = data.get("app_id")
        user_code = data.get("user_code")
        password = data.get("password")
        is_pwd_encrypt = data.get("is_pwd_encrypt")
        data_format = data.get("data_format")
        input_data = "What are the modules are available in Proteus Vision ERP ?\r\nCan you please highlight the specific feature of manufacturing module"

        trans_details = self.generate_token(
                base_url,
                app_id,
                user_code,
                password,
                is_pwd_encrypt,
                data_format
            )
        logger.log(f"trans_details::  {trans_details}")
        # return trans_details
        

        token_id = self.email_save_transaction(base_url,input_data,trans_details)
        logger.log(f"token:::  {token_id}")
        return token_id
