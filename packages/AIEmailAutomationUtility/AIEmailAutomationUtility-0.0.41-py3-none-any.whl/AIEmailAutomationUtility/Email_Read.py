import imaplib
import email
import time
import loggerutility as logger
from datetime import datetime

import threading
import traceback
import json
import os, shutil
import csv

import io
import pandas as pd
import docx
import PyPDF2

from .Save_Transaction import Save_Transaction
from .Email_Classification import Email_Classification
from .EmailReplyAssistant import EmailReplyAssistant
from .Process_Category import Process_Category

import re
from email.utils import parseaddr
from email.header import decode_header

import docx2txt
import cv2
import pytesseract
import pdfplumber
import numpy as np
from PIL import Image

# import fitz
import pdfplumber

shared_status = True

class Email_Read:
    def read_email(self, email_config):
        try:
            logger.log("inside read_email")
            mail = imaplib.IMAP4_SSL(email_config['host'], email_config['port'])
            mail.login(email_config['email'], email_config['password'])
            logger.log("login successfully")
            mail.select('inbox')

            while True:
                status, email_ids = mail.search(None, 'UNSEEN')
                emails = []
                
                if status == 'OK':
                    email_ids = email_ids[0].split()

                    if not email_ids: 
                        logger.log("Email not found, going to check new mail")
                        logger.log("Email not found,\ngoing to check new mail \n")
                    else:
                    
                        for email_id in email_ids:
                            email_body = ""
                            attachments = []
                            status, data = mail.fetch(email_id, '(RFC822)')
                            
                            if status == 'OK':
                                raw_email = data[0][1]
                                msg = email.message_from_bytes(raw_email)
                                sender_email = msg['From']
                                cc_email = msg['CC']
                                subject = msg['Subject']
                                to = msg['To']

                                if msg.is_multipart():
                                    for part in msg.walk():
                                        content_type = part.get_content_type()
                                        if content_type == "text/plain":
                                            email_body += part.get_payload(decode=True).decode('utf-8', errors='replace')
                                else:
                                    email_body = msg.get_payload(decode=True).decode('utf-8', errors='replace')                              

                                email_data = {
                                    "email_id": email_id,
                                    "from": sender_email,
                                    "to": to,
                                    "cc": cc_email,
                                    "subject": subject,
                                    "body": email_body
                                }
                                emails.append(email_data)
                                logger.log(f"emails:: {emails}")
                                call_save_transaction = Save_Transaction()
                                save_transaction_response = call_save_transaction.email_save_transaction(email_data)
                                logger.log(f"save_transaction_response:: {save_transaction_response}")
                time.sleep(10)
        
        except Exception as e:
            return {"success": "Failed", "message": f"Error reading emails: {str(e)}"}
        finally:
            try:
                mail.close()
                mail.logout()
            except Exception as close_error:
                logger.log(f"Error during mail close/logout: {str(close_error)}")

    def read_email_automation(self, email_config,user_id):
        logger.log(f"inside read_email_automation")
        LABEL                       = "Unprocessed_Email"
        file_JsonArray              = []
        templateName                = "ai_email_automation.json"
        fileName                    = ""

        Model_Name =  email_config.get('model_type', 'OpenAI') 
        reciever_email_addr = email_config.get('email', '').replace("\xa0", "").strip()
        receiver_email_pwd = email_config.get('password', '').replace("\xa0", "").strip()
        host =  email_config.get('host', '') 
        port =  email_config.get('port', '') 

        try:
            mail = imaplib.IMAP4_SSL(host, port)
            mail.login(reciever_email_addr, receiver_email_pwd)
            logger.log("login successfully")
            login_status = "Success"
            mail.select('inbox')

            file_JsonArray, categories = self.read_JSON_File(templateName, user_id)

        except Exception as e:
            login_status = "Failed"
            logger.log(f"Login failed: {e}")
            raise Exception(e)   

        # Log the result
        self.log_email_login(user_id, reciever_email_addr, Model_Name, login_status)

        while True:
            shared_status = self.read_status()

            if shared_status:
                status, email_ids = mail.search(None, 'UNSEEN')
                emails = []
                
                if status == 'OK':
                    email_ids = email_ids[0].split()
                
                    if not email_ids: 
                        logger.log("Email not found, going to check new mail")
                        logger.log("Email not found,\ngoing to check new mail \n")
                    else:
                    
                        for email_id in email_ids:
                            email_body = ""
                            attachments = []
                            # status, data = mail.fetch(email_id, '(RFC822)')
                            status, data = mail.fetch(email_id, '(RFC822 UID)') # Fetch UID as well
                            emailCategory = "Not Classified"

                            if status == 'OK':
                                raw_email = data[0][1]
                                msg = email.message_from_bytes(raw_email)

                                subject = msg['Subject']
                                sender_email_addr   = msg['From']
                                cc_email_addr       = msg['CC']
                                subject             = msg['Subject']
                                to_email_addr = msg.get('To', '')
                                

                                # Extract UID
                                logger.log(f" the data -----{data[0][0]}")
                                raw_uid = data[0][0].decode() if isinstance(data[0][0], bytes) else data[0][0]
                                logger.log(f"the raw uid is ------- {raw_uid}")
                                uid_match = re.search(r'UID (\d+)', raw_uid)
                                uid = uid_match.group(1) if uid_match else "N/A"

                                is_html = False  # Initialize is_html

                                if msg.is_multipart():
                                    for part in msg.walk():
                                        content_type = part.get_content_type()
                                        if content_type == "text/html" and not is_html:
                                            is_html = True  # Set flag if HTML part is found

                                        if content_type == "text/plain":
                                            email_body += part.get_payload(decode=True).decode('utf-8', errors='replace')
                                        
                                else:
                                    email_body = msg.get_payload(decode=True).decode('utf-8', errors='replace')                              
                                    content_type = msg.get_content_type()
                                    is_html = (content_type == "text/html")  # Set is_html based on single-part type
                                
                                openai_Process_Input  = email_body 

                                logger.log(f"\nEmail Subject::: {subject}")
                                logger.log(f"\nEmail body::: {openai_Process_Input}")

                                openai_api_key = email_config.get('openai_api_key', '') 
                                geminiAI_APIKey = email_config.get('gemini_api_key', '') 
                                signature = email_config.get('signature', '') 
                                localAIURL = email_config.get('local_ai_url', '') 
                                
                                if len(str(openai_Process_Input)) > 0 :
                                    email_cat_data = {
                                        "model_type" : Model_Name,
                                        "openai_api_key" : openai_api_key,
                                        "categories" : categories,
                                        "email_body" : email_body,
                                        "gemini_api_key" : geminiAI_APIKey,
                                        "signature" : signature,
                                        "local_ai_url" : localAIURL,
                                    }
                                    # logger.log(f"\nemail_cat_data ::: {email_cat_data}")
                                    email_classification = Email_Classification()
                                    emailCategory = email_classification.detect_category(email_cat_data)
                                    emailCategory = emailCategory['message']
                                    logger.log(f"\nDetected Email category ::: {emailCategory}")

                                    dataValues = {
                                        'Model_Name': Model_Name,
                                        'file_JsonArray': file_JsonArray,
                                        'openai_api_key': openai_api_key,
                                        'openai_Process_Input': openai_Process_Input,
                                        'subject': subject,
                                        'sender_email_addr': sender_email_addr,
                                        'cc_email_addr': cc_email_addr,
                                        'email_body': email_body,
                                        'email_config': email_config,
                                        'msg': msg,
                                        'geminiAI_APIKey': geminiAI_APIKey,
                                        'localAIURL': localAIURL,
                                        'signature': signature,
                                        'LABEL': LABEL,
                                        'mail': mail,
                                        'email_id': email_id,
                                        "uid": uid,
                                        "to_email_addr": to_email_addr,
                                        "user_id": user_id,
                                        "is_html": is_html
                                    }
                                    processcategory = Process_Category()
                                    processcategory.process_cat(emailCategory, dataValues)

            time.sleep(10)

    def read_email_quotation(self, email_config,user_id):
        # try:
        LABEL                       = "Unprocessed_Email"
        file_JsonArray              = []
        templateName                = "ai_email_automation.json"
        fileName                    = ""

        Model_Name =  email_config.get('model_type', 'OpenAI') 
        reciever_email_addr = email_config.get('email', '').replace("\xa0", "").strip()
        receiver_email_pwd = email_config.get('password', '').replace("\xa0", "").strip()
        host =  email_config.get('host', '') 
        port =  email_config.get('port', '') 

        try:
            mail = imaplib.IMAP4_SSL(host, port)
            mail.login(reciever_email_addr, receiver_email_pwd)
            logger.log("login successfully")
            login_status = "Success"
            mail.select('inbox')

            file_JsonArray, categories = self.read_JSON_File(templateName, user_id)

        except Exception as e:
            logger.log(f"Login failed: {e}")
            return f"Login failed: {e}"

        # Log the result
        self.log_email_login(user_id, reciever_email_addr, Model_Name, login_status)

        while True:
            status, email_ids = mail.search(None, 'UNSEEN')
            emails = []
            
            if status == 'OK':
                email_ids = email_ids[0].split()

                if not email_ids: 
                    logger.log("Email not found, going to check new mail")
                    logger.log("Email not found,\ngoing to check new mail \n")
                else:
                
                    for email_id in email_ids:
                        email_body = ""
                        attachments = []
                        status, data = mail.fetch(email_id, '(RFC822 UID)')
                        
                        if status == 'OK' and data[0]!= None:
                            raw_email = data[0][1]
                            msg = email.message_from_bytes(raw_email)

                            subject = msg['Subject']
                            sender_email_addr   = msg['From']
                            cc_email_addr       = msg['CC']
                            subject             = msg['Subject']
                            to_email_addr = msg.get('To', '')

                            # Extract UID
                            raw_uid = data[0][0].decode() if isinstance(data[0][0], bytes) else data[0][0]
                            uid_match = re.search(r'UID (\d+)', raw_uid)
                            uid = uid_match.group(1) if uid_match else "N/A"

                            is_html = False  # Initialize is_html

                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    if content_type == "text/html" and not is_html:
                                        is_html = True  # Set flag if HTML part is found

                                    if content_type == "text/plain":
                                        email_body += part.get_payload(decode=True).decode('utf-8', errors='replace')

        
                            # For attachment
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_disposition = str(part.get("Content-Disposition") or "")
                                    content_type = part.get_content_type()

                                    if "attachment" in content_disposition.lower() or "inline" in content_disposition.lower():
                                        filename = part.get_filename() or "attachment"
                                        content_bytes = part.get_payload(decode=True)
                                        if content_bytes:
                                            extracted_content = self.Extract_attachment_content_OCR(filename, content_bytes)
                                            extracted_content =f"\n\n--- The Extracted Content of Attachment '{filename}' is below ---\n{extracted_content}\n"
                                            logger.log(extracted_content)
                                            # email_body += f"\n\n--- The content of the attachment '{filename}' is below ---\n{extracted_content}\n"
                                    else:
                                        extracted_content="NA"
                             
                            else:
                                email_body = msg.get_payload(decode=True).decode('utf-8', errors='replace')                              
                                content_type = msg.get_content_type()
                                is_html = (content_type == "text/html")  # Set is_html based on single-part type
                            
                            openai_Process_Input  = email_body 
                            logger.log(f"\nEmail Subject::: {subject}")
                            logger.log(f"\nEmail body::: {openai_Process_Input}")

                            openai_api_key = email_config.get('openai_api_key', '') 
                            geminiAI_APIKey = email_config.get('gemini_api_key', '') 
                            signature = email_config.get('signature', '') 
                            localAIURL = email_config.get('local_ai_url', '') 
                            logger.log(f"\ngeminiAI_APIKey::: {geminiAI_APIKey}")
                            logger.log(f"\nlocalAIURL::: {localAIURL}")
                            logger.log(f"\nsignature::: {signature}")
                            
                            if len(str(openai_Process_Input)) > 0 :
                                email_cat_data = {
                                    "model_type" : Model_Name,
                                    "openai_api_key" : openai_api_key,
                                    "categories" : categories,
                                    "email_body" : email_body,
                                    "gemini_api_key" : geminiAI_APIKey,
                                    "signature" : signature,
                                    "local_ai_url" : localAIURL,
                                }
                                # logger.log(f"\nemail_cat_data ::: {email_cat_data}")
                                email_classification = Email_Classification()
                                emailCategory = email_classification.detect_category(email_cat_data)
                                emailCategory = emailCategory['message']
                                logger.log(f"\nDetected Email category ::: {emailCategory}")
                                
                                dataValues = {
                                    'Model_Name': Model_Name,
                                    'file_JsonArray': file_JsonArray,
                                    'openai_api_key': openai_api_key,
                                    'openai_Process_Input': openai_Process_Input,
                                    'subject': subject,
                                    'sender_email_addr': sender_email_addr,
                                    'cc_email_addr': cc_email_addr,
                                    'email_body': email_body,
                                    'email_config': email_config,
                                    'msg': msg,
                                    'geminiAI_APIKey': geminiAI_APIKey,
                                    'localAIURL': localAIURL,
                                    'signature': signature,
                                    'LABEL': LABEL,
                                    'mail': mail,
                                    'email_id': email_id,
                                    "uid": uid,
                                    "to_email_addr": to_email_addr,
                                    "user_id": user_id,
                                    "is_html": is_html,
                                    "extracted_content" : extracted_content
                                }
                                processcategory = Process_Category()
                                processcategory.process_cat(emailCategory, dataValues)

            time.sleep(10)

    def Read_Email(self, data):
        try:

            reciever_email_addr = data.get("reciever_email_addr")
            receiver_email_pwd = data.get("receiver_email_pwd")
            host = data.get("host")
            port = data.get("port")
            openai_api_key = data.get("openai_api_key") 
            geminiAI_APIKey = data.get("GeminiAI_APIKey")
            localAIURL = data.get("LOCAL_AI_URL")

            if not all([reciever_email_addr, receiver_email_pwd, host, port]):
                raise ValueError("Missing required email configuration fields.")

            logger.log(f"\nReceiver Email Address: {reciever_email_addr}\t{type(reciever_email_addr)}", "0")
            logger.log(f"\nReceiver Email Password: {receiver_email_pwd}\t{type(receiver_email_pwd)}", "0")
            logger.log(f"\nHost: {host}\t{type(host)}", "0")
            logger.log(f"\nPort: {port}\t{type(port)}", "0")

            email_config = {
                'email': reciever_email_addr,
                'password': receiver_email_pwd,
                'host': host,
                'port': int(port),
                'openai_api_key': openai_api_key,
                'gemini_api_key': geminiAI_APIKey,
                'local_ai_url': localAIURL
            }

            emails = self.read_email(email_config)            
            logger.log(f"Read_Email response: {emails}")

        except Exception as e:
            logger.log(f"Error in Read_Email: {str(e)}")
    
    def extract_all_email_info(self, eml_content):
        # Parse the email content
        msg = email.message_from_string(eml_content)
        extracted_info = {}

        # Extracting To, From, and CC
        extracted_info['to'] = msg.get('To')
        extracted_info['from'] = msg.get('From')
        extracted_info['cc'] = msg.get('Cc')
        logger.log(f"To: {extracted_info['to']}, From: {extracted_info['from']}, CC: {extracted_info['cc']}")

        # Extracting subject and decoding it if necessary
        subject = decode_header(msg.get('Subject', ''))[0][0]
        if decode_header(msg.get('Subject', ''))[0][1]:
            subject = subject.decode()
        extracted_info['subject'] = subject
        logger.log(f"Subject: {extracted_info['subject']}")

        # Extracting the body content (text or HTML)
        text_body = None
        html_body = None
        if msg.is_multipart():
            logger.log("Multipart email detected.")
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                logger.log(f"Part content type: {content_type}, Content-Disposition: {content_disposition}")

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    text_body = part.get_payload(decode=True).decode()
                    logger.log("Text body extracted.")
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    html_body = part.get_payload(decode=True).decode()
                    logger.log("HTML body extracted.")
        else:
            if msg.get_content_type() == "text/plain":
                text_body = msg.get_payload(decode=True).decode()
                logger.log("Text body extracted (non-multipart) .")
            elif msg.get_content_type() == "text/html":
                html_body = msg.get_payload(decode=True).decode()
                logger.log("HTML body extracted (non-multipart).")

        extracted_info['email_body'] = text_body if text_body else html_body if html_body else None
        extracted_info['is_html'] = bool(html_body)

        # Extracting the date and converting it to ISO format
        date_tuple = email.utils.parsedate_tz(msg.get('Date'))
        logger.log(f"date tuple is {date_tuple}")
        if date_tuple:
            local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            extracted_info['date'] = local_date.isoformat()
            logger.log(f"Date: {extracted_info['date']}")
        else:
            extracted_info['date'] = None
            logger.log("No date found.")

        # Extracting the unique ID (Message-ID)
        extracted_info['unique_id'] = msg.get('Message-ID')
        logger.log(f"Unique ID: {extracted_info['unique_id']}")
        logger.log(f"-------------------------------The extracted info is --------------------------{extracted_info}")

        return extracted_info,msg
    
    def process_eml_files(self, user_id, eml_content,mail,Model_Name,email_config):
        LABEL = "Unprocessed_Email"
        file_JsonArray = []
        templateName = "ai_email_automation.json"
        fileName = ""
    
        file_JsonArray, categories = self.read_JSON_File(templateName, user_id)
        # Call the `extract_all_email_info` method to extract details from the eml content
        extracted_info,msg = self.extract_all_email_info(eml_content)

        # Extract the details from `extracted_info`
        subject = extracted_info.get('subject', '')
        sender_email_addr = extracted_info.get('from', '')
        cc_email_addr = extracted_info.get('cc', '')
        to_email_addr = extracted_info.get('to', '')
        date = extracted_info.get('date', '')
        email_body = extracted_info.get('email_body', '')
        msg_id = extracted_info.get('unique_id', '')
        is_html = extracted_info.get('is_html', False)  

        uid = re.sub(r'[<>]|\@.*|\+', '', msg_id) 
        logger.log(f"\nEmail Subject::: {subject}")
        logger.log(f"\nEmail body::: {email_body}")

        openai_Process_Input = email_body

        openai_api_key = email_config.get('openai_api_key', '') 
        geminiAI_APIKey = email_config.get('gemini_api_key', '') 
        signature = email_config.get('signature', '') 
        localAIURL = email_config.get('local_ai_url', '') 

        if len(str(openai_Process_Input)) > 0:
            email_cat_data = {
                "model_type": Model_Name,
                "openai_api_key": openai_api_key,
                "categories": categories,
                "email_body": email_body,
                "gemini_api_key": geminiAI_APIKey,
                "signature": signature,
                "local_ai_url": localAIURL,
            }
            email_classification = Email_Classification()
            emailCategory = email_classification.detect_category(email_cat_data)
            emailCategory = emailCategory['message']
            logger.log(f"\nDetected Email category ::: {emailCategory}")

            dataValues = {
                'Model_Name': Model_Name,
                'file_JsonArray': file_JsonArray,
                'openai_api_key': openai_api_key,
                'openai_Process_Input': openai_Process_Input,
                'subject': subject,
                'sender_email_addr': sender_email_addr,
                'cc_email_addr': cc_email_addr,
                'email_body': email_body,
                'email_config': email_config,
                'msg': msg,
                'geminiAI_APIKey': geminiAI_APIKey,
                'localAIURL': localAIURL,
                'signature': signature,
                'LABEL': LABEL,
                'mail': mail,
                'email_id': msg_id,
                "uid": uid,
                "to_email_addr": to_email_addr,
                "user_id": user_id,
                "is_html": is_html,
                "import_file": True
            }
            processcategory = Process_Category()
            processcategory.process_cat(emailCategory, dataValues)

        return "success"

    def read_JSON_File(self, json_fileName, user_id):
        category_list               = []
        categories                  = ""
        try:
            logger.log(f"\nEmail_Read() read_JSON_File user_id ::: {user_id}")
            user_file = json_fileName
            if user_id:
                user_dir = os.path.join('user_data', user_id)
                logger.log(f"\nEmail_Read() read_JSON_File user_dir ::: {user_dir}")
                if not os.path.exists(user_dir):
                    os.makedirs(user_dir, exist_ok=True)
                user_file = os.path.join(user_dir, json_fileName)
                if not os.path.exists(user_file) and os.path.exists(json_fileName):
                    shutil.copy(json_fileName, user_file)

            logger.log(f"\nEmail_Read() read_JSON_File user_file ::: {user_file}")

            if os.path.exists(user_file):
                with open(user_file, "r") as fileObj:
                    file_JsonArray = json.load(fileObj)
                    
                    for eachJson in file_JsonArray :
                        for key, value in eachJson.items():
                            if key == "Category":
                                category_list.append(value)
                        # categories = ", ".join(category_list)
                        
                return file_JsonArray, category_list

            else:
                message = f"{user_file} file not found."
                raise Exception(message)
        except Exception as e:
            msg = f"'{json_fileName}' file is empty. Please provide JSON parameters in the filename."
            trace = traceback.format_exc()
            logger.log(f"Exception in writeJsonFile: {msg} \n {trace} \n DataType ::: {type(msg)}")
            raise Exception(msg)

    def log_email_login(self, user_id, email, model_name, login_status):
        base_dir="EMail_log"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.join(base_dir, user_id)
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"{user_id}.csv")

        log_exists = os.path.isfile(log_file_path)
        with open(log_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not log_exists:
                writer.writerow(["timestamp", "user_id", "email", "Model_Name", "login_status"])
            writer.writerow([timestamp, user_id, email, model_name, login_status])

    def update_status(self):
        global shared_status
        shared_status = False

    def read_status(self):
        global shared_status
        return shared_status
    
    def Extract_attachment_content_OCR(self,filename, content_bytes):
        extension = os.path.splitext(filename)[1].lower()
        OCR_Text = ""

        logger.log(f"OCR Start !!!!!!!!!!!!!!!!!102","0")  
        dict = {}          
        if '.pdf' in extension:
            OCR_Text=self.pdfplumber_overlap(io.BytesIO(content_bytes))
            logger.log(f"\nLoading 'pdftotext' module OCR ::: {OCR_Text}\n ")

        elif '.docx' in extension:
            dict[str(1)] = docx2txt.process(io.BytesIO(content_bytes)).replace('\x00', '')
            OCR_Text = dict
            logger.log(f"OpenAI DOCX ocr ::::: {OCR_Text}","0")

        elif ".xls" in extension or ".xlsx" in extension:
            logger.log(f"inside .xls condition","0")
            df = pd.read_excel(io.BytesIO(content_bytes))
            xls_ocr = df.to_csv()
            dict[str(1)] = xls_ocr.replace(","," ").strip().replace('\x00', '')
            OCR_Text = dict
            logger.log(f"\nxls_ocr type ::::: \t{type(OCR_Text)}","0")
            logger.log(f"\nxls_ocr ::::: \n{OCR_Text}\n","0")
            
        elif ".csv" == extension :
            logger.log(f"inside .csv condition","0")
            df = pd.read_csv(io.BytesIO(content_bytes))
            csv_ocr = df.to_csv()           # to handle multiple spaces between columns
            dict[str(1)] = csv_ocr.replace(","," ").replace('\x00', '')
            OCR_Text = dict
            logger.log(f"\ncsv_ocr type ::::: \t{type(OCR_Text)}","0")
            logger.log(f"\ncsv_ocr ::::: \n{OCR_Text}\n","0")

        else:
            OCR_Text = self.extract_text_best_attempt(filename, content_bytes)
        logger.log(f"OCR End !!!!!!!!!!!!!!!!!156","0")
        return OCR_Text
    
    def extract_text_from_image(self,filename, content_bytes):
        try:
            file_bytes = np.frombuffer(content_bytes, np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"Could not decode image: {filename}")

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            denoised = cv2.medianBlur(gray, 5)
            _, threshold = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            pil_image = Image.fromarray(threshold)
            extracted_text = pytesseract.image_to_string(pil_image, config='--psm 6')
            cleaned_text = '\n'.join(line.strip() for line in extracted_text.split('\n') if line.strip())
            return cleaned_text
            
        except Exception as e:
            print(f"Error extracting text from {filename}: {str(e)}")
            return ""

    def extract_text_from_image_advanced(self,filename, content_bytes, preprocess=True):
        try:
            file_bytes = np.frombuffer(content_bytes, np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError(f"Could not decode image: {filename}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if preprocess:
                height, width = gray.shape
                scale_factor = max(2.0, 1000/max(height, width))  # Minimum 2x, or scale to 1000px
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                
                denoised = cv2.fastNlMeansDenoising(enhanced)
                
                filtered = cv2.bilateralFilter(denoised, 9, 75, 75)
                
                _, binary = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
                processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel, iterations=1)
                
                if cv2.mean(processed)[0] < 127:
                    processed = cv2.bitwise_not(processed)
                    
            else:
                processed = gray
            
            pil_image = Image.fromarray(processed)
            
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz().,%-/: '
            
            approaches = [
                ('Table optimized', r'--oem 3 --psm 6'),
                ('Document', r'--oem 3 --psm 4'),
                ('Auto page', r'--oem 3 --psm 3'),
                ('Single block', r'--oem 3 --psm 8'),
                ('Sparse text', r'--oem 3 --psm 11'),
                ('Custom whitelist', custom_config)
            ]
            
            results = []
            
            for name, config in approaches:
                try:
                    text = pytesseract.image_to_string(pil_image, config=config, lang='eng')
                    cleaned_text = []
                    for line in text.split('\n'):
                        line = line.strip()
                        if line and len(line) > 1:
                            cleaned_text.append(line)
                    
                    if cleaned_text:
                        results.append((name, '\n'.join(cleaned_text), len(cleaned_text)))
                except Exception as e:
                    continue
            
            if results:
                best_result = max(results, key=lambda x: x[2])
                return best_result[1]
            else:
                return pytesseract.image_to_string(pil_image)
            
        except Exception as e:
            print(f"Error extracting text from {filename}: {str(e)}")
            return ""

    def extract_text_table_focused(self,filename, content_bytes):
        try:
            file_bytes = np.frombuffer(content_bytes, np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError(f"Could not decode image: {filename}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            height, width = gray.shape
            scale_factor = max(3.0, 1500/max(height, width))
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            upscaled = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(upscaled)
            
            denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
            
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel)
            
            adaptive_thresh = cv2.adaptiveThreshold(
                sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
            )
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            
            if cv2.mean(cleaned)[0] < 127:
                cleaned = cv2.bitwise_not(cleaned)
            
            pil_image = Image.fromarray(cleaned)
            
            table_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            
            extracted_text = pytesseract.image_to_string(pil_image, config=table_config, lang='eng')
            
            lines = []
            for line in extracted_text.split('\n'):
                line = line.strip()
                if line:
                    line = line.replace('|', 'l')
                    line = line.replace('0', 'O') if line.isalpha() else line 
                    line = line.replace('5', 'S') if line.isalpha() else line 
                    lines.append(line)
            
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"Error extracting text from {filename}: {str(e)}")
            return ""

    def extract_text_minimal_processing(self,filename, content_bytes):
        try:
            file_bytes = np.frombuffer(content_bytes, np.uint8)
            
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError(f"Could not decode image: {filename}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            height, width = gray.shape
            scale_factor = 2.5
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            upscaled = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            if cv2.mean(binary)[0] < 127:
                binary = cv2.bitwise_not(binary)
            
            pil_image = Image.fromarray(binary)
            
            configs = [
                r'--oem 3 --psm 6', 
                r'--oem 3 --psm 4', 
                r'--oem 3 --psm 3', 
            ]
            
            best_result = ""
            max_lines = 0
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(pil_image, config=config, lang='eng')
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    if len(lines) > max_lines:
                        max_lines = len(lines)
                        best_result = '\n'.join(lines)
                except:
                    continue
            
            return best_result
            
        except Exception as e:
            print(f"Error extracting text from {filename}: {str(e)}")
            return ""

    def extract_text_with_deskew(self,filename, content_bytes):
        try:
            file_bytes = np.frombuffer(content_bytes, np.uint8)
            
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError(f"Could not decode image: {filename}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            height, width = gray.shape
            scale_factor = 3.0
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            upscaled = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            _, binary = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            def deskew(image):
                coords = np.column_stack(np.where(image > 0))
                if len(coords) == 0:
                    return image
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                
                if abs(angle) > 0.5:
                    (h, w) = image.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                    return rotated
                return image
            
            deskewed = deskew(binary)
            
            if cv2.mean(deskewed)[0] < 127:
                deskewed = cv2.bitwise_not(deskewed)
            
            pil_image = Image.fromarray(deskewed)
            
            text = pytesseract.image_to_string(
                pil_image, 
                config=r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz().,%-/: |',
                lang='eng'
            )
            
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 2:
                    lines.append(line)
            
            return '\n'.join(lines)
            
        except Exception as e:
            print(f"Error extracting text from {filename}: {str(e)}")
            return ""

    def extract_text_best_attempt(self,filename, content_bytes):
        approaches = [
            ("Minimal Processing", self.extract_text_minimal_processing),
            ("Table Focused", self.extract_text_table_focused),
            ("With Deskewing", self.extract_text_with_deskew),
            ("Advanced", lambda f, c: self.extract_text_from_image_advanced(f, c, True)),
            ("Basic", self.extract_text_from_image)
        ]
        
        results = []
        
        for name, func in approaches:
            try:
                text = func(filename, content_bytes)
                if text and len(text.strip()) > 20:  
                    lines = text.split('\n')
                    non_empty_lines = len([l for l in lines if l.strip()])
                    
                    has_numbers = any(char.isdigit() for char in text)
                    has_letters = any(char.isalpha() for char in text)
                    reasonable_chars = sum(1 for char in text if char.isalnum() or char in ' .,()-/')
                    total_chars = len(text)
                    char_ratio = reasonable_chars / total_chars if total_chars > 0 else 0
                    
                    score = non_empty_lines * 2 + (100 if has_numbers and has_letters else 0) + (char_ratio * 50)
                    
                    results.append((name, text, score, non_empty_lines))
                    
            except Exception as e:
                print(f"Error with {name}: {e}")
                continue
        
        if results:
            best = max(results, key=lambda x: x[2])
            print(f"Best result from: {best[0]} (Score: {best[2]:.1f}, Lines: {best[3]})")
            return best[1]
        else:
            return "No text could be extracted from the image."

    def pdfplumber_overlap(self, fileName):
        ocr_text_final  = ""
        OCR_dict        = {}
        method_used     = ""
        
        pdf = pdfplumber.open(fileName)
        # pdf_fitz = fitz.open(fileName)
        ocr_text = pdf.pages
        for page_no in range (len(ocr_text)):
            ocr_text_final = ocr_text[page_no].extract_text(layout=True, x_tolerance=1)
            if ocr_text_final and ocr_text_final.strip():
                method_used = "pdfplumber"
                logger.log("Extracted text by pdfplumber")
                OCR_dict[str(page_no+1)] = ocr_text_final.strip().replace('\x00', '')
            # else:
            #     method_used = "fitz"
            #     logger.log("Extracted text by fitz")
            #     page = pdf_fitz.load_page(page_no)
            #     ocr_text_final = page.get_text()
            #     OCR_dict[str(page_no+1)] = ocr_text_final.strip().replace('\x00', '')
        
        logger.log(f"OCR_dict after overlap:::: \t{type(OCR_dict)}\n{OCR_dict}\n")
        return OCR_dict, method_used