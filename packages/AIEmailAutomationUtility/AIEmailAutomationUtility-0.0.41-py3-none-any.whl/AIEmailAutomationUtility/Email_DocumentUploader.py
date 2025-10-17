import os
import json
import shutil
import requests
import loggerutility as logger
from flask import Flask,request
from datetime import datetime

class Email_DocumentUploader:
    def upload_document(self, upload_config, file_data):
        document_type = upload_config['document_type']
        # try:
        logger.log("inside function" )
        # Create temp directory if needed
        today_date = datetime.today().strftime('%Y-%m-%d')
        temp_dir = os.path.join(document_type, today_date)
            
        # Save file temporarily
        file_path = os.path.join(temp_dir, file_data['filename'])
        logger.log(f"file_path:: {file_path}")
        with open(file_path, 'wb') as f:
            f.write(file_data['content'])
        
        # Prepare headers and parameters
        headers = {"TOKEN_ID": upload_config["token_id"]}
        params = {}
        
        param_fields = {
            "DOCUMENT_TYPE": "document_type",
            "OBJ_NAME": "obj_name",
            "FILE_TYPE": "file_type",
            "APP_ID": "app_id"
        }
        logger.log(f"param_fields:: {param_fields}")
        
        for api_key, config_key in param_fields.items():
            if config_key in upload_config and upload_config[config_key]:
                params[api_key] = upload_config[config_key]
        
        # Upload file
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.request(
                upload_config["method"],
                upload_config["url"],
                headers=headers,
                files=files,
                data=params
            )
        logger.log("file read")
        
        if response.status_code == 200:
            result = json.loads(response.text)
            logger.log(f"file Upload Response ::: {result}")
            document_id = result["ID"]["Document_Id"]
            return str(response.status_code), document_id
        else:
            return str(response.status_code), f"Upload failed: {response.text}"

    def email_document_upload(self, file, parameters_details):
        logger.log(f"file ::: {file}")
        if not file:
            return "file not found"

        upload_config = {
            'token_id': parameters_details.get('TOKEN_ID'),
            'document_type': parameters_details.get('DOCUMENT_TYPE', ''),
            'obj_name': parameters_details.get('OBJ_NAME', ''),
            'file_type': parameters_details.get('FILE_TYPE', ''),
            'app_id': parameters_details.get('APP_ID', ''),
            'method': parameters_details.get('Method_Type', 'POST'),
            'url': parameters_details.get('RestAPI_Url')
        }

        # Validate required fields
        if not upload_config['token_id'] or not upload_config['url']:
            return "Missing required fields: TOKEN_ID or RestAPI_Url"
        
        file_data = {
            'filename': os.path.basename(file.name),
            'content': file.read()
        }

        response_status, restAPI_Result = self.upload_document(upload_config, file_data)
        
        logger.log(f"Upload_Document response result: {restAPI_Result}")
        return response_status, restAPI_Result