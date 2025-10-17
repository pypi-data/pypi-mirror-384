
import requests
import loggerutility as logger
from flask import Flask, request
import json

class Email_Upload_Document:

    def upload_files(self, file_path):
        data = request.get_data('jsonData', None)
        data = json.loads(data[9:])
        logger.log(f"jsondata:: {data}")
        base_url = data.get("base_url")
        token_id = data.get("token_id")

        url = f"{base_url}/ibase/rest/DocumentHandlerService/uploadDocument"

        headers = {
            "TOKEN_ID": token_id,
            "Content-Type": "multipart/form-data" 
        }

        with open(file_path, 'rb') as file_to_upload:
            files = {'file': file_to_upload}
            logger.log(f"files:: {files}")
            logger.log(f"file_to_upload:: {file_to_upload}")

            response = requests.post(url, headers=headers, files=files)

        if response.status_code == 200:
            logger.log("File uploaded successfully!")
            logger.log("Response:", response.json())  
            return {"success": "Success", "message": "File uploaded"}
        else:
            logger.log("Failed to upload file.")
            logger.log("Status Code:", response.status_code)
            logger.log("Response:", response.text)
            return {"success": "Failed", "message": "File not uploaded"}

        

