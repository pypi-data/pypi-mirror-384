import imaplib
import email
from email.message import Message
import datetime
import time
import loggerutility as logger
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

class Email_Draft:
    def draft_email(self, email_config, email_details, response_content):
        try:
            with imaplib.IMAP4_SSL(host=email_config['host'], port=imaplib.IMAP4_SSL_PORT) as imap_ssl:
                imap_ssl.login(email_config['email'], email_config['password'])
                
                message = Message()
                message["From"] = email_config['email']
                message["To"] = email_details['sender']
                message["CC"] = email_details['cc']
                
                subject = email_details['subject']
                if not subject.startswith("Re:"):
                    subject = f"Re: {subject}"
                message["Subject"] = subject
                
                mail_details = f'{datetime.datetime.now().strftime("On %a, %b %d, %Y at %I:%M %p")} {email_details["sender"]} wrote:'
                message.set_payload(f"{response_content}\n\n{mail_details}\n\n{email_details['body']}")
                
                utf8_message = str(message).encode("utf-8")
                # logger.log(f"utf8_message:: {utf8_message}")
                imap_ssl.append("[Gmail]/Drafts", '', imaplib.Time2Internaldate(time.time()), utf8_message)
                
                return True, utf8_message.decode("utf-8")
                
        except Exception as e:
            return False, str(e)

    def quotation_draft_email(self, email_config, email_details, response_content):
        try:
            with imaplib.IMAP4_SSL(host=email_config['host'], port=imaplib.IMAP4_SSL_PORT) as imap_ssl:
                imap_ssl.login(email_config['email'], email_config['password'])

                # Create the email object
                message = MIMEMultipart("alternative")
                message["From"] = email_config['email']
                message["To"] = email_details['sender']
                message["CC"] = email_details['cc']

                # Set the subject with "Re:" prefix
                subject = email_details['subject']
                if not subject.startswith("Re:"):
                    subject = f"Re: {subject}"
                message["Subject"] = subject

                # Email details for original message
                mail_details = f'{datetime.datetime.now().strftime("On %a, %b %d, %Y at %I:%M %p")} {email_details["sender"]} wrote:'

                # Extract response content
                body = response_content.get('body', '')
                table_html = response_content.get('table_', '')
                aligned_table_html = self.align_numeric_cells_right(table_html)
                signature = response_content.get('signature', '')
                email_body = email_details['body']

                # Replace new lines with <br> for proper HTML formatting
                body_html = body.replace("\n", "<br>").replace("\n\n", "<br>")
                signature_html = signature.replace("\n", "<br>").replace("\n\n", "<br>")
                email_body_html = email_body.replace("\n", "<br>").replace("\n\n", "<br>")

                # Create HTML content
                html_content = (
                    "<html><body>"
                    f"<p>{body_html}</p>"
                    f"{aligned_table_html}"
                    f"<b>GST Extra as per applicable.</b>"
                    f"<p>{signature_html}</p>"
                    "<hr>"
                    f"<p>{mail_details}</p>"
                    f"<p>{email_body_html}</p>"
                    "</body></html>"
                )

                # Attach HTML content
                message.attach(MIMEText(html_content, "html"))

                utf8_message = message.as_string().encode("utf-8")

                # Append the draft to Gmail
                imap_ssl.append("[Gmail]/Drafts", '', imaplib.Time2Internaldate(time.time()), utf8_message)

                return True, utf8_message.decode("utf-8")

        except Exception as e:
            return False, str(e)

    def draft_email_response(self, email_details):
        try:
            logger.log("Creating draft email with the following details:")
            logger.log(f"From: {email_details.get('from')}")
            logger.log(f"To: {email_details.get('to')}")
            logger.log(f"CC: {email_details.get('cc')}")
            logger.log(f"Subject: {email_details.get('subject')}")
            logger.log(f"Body: {email_details.get('body')}")

            return "Success", {
                "from": email_details['from'],
                "to": email_details['to'],
                "cc": email_details.get('cc', ""),
                "subject": email_details['subject'],
                "body": email_details['body']
            }

        except Exception as e:
            logger.log(f"Error creating draft: {str(e)}")
            return "Failed", None

    def draft_mail(self, data):
        try:

            if "reciever_email_addr" in data and data["reciever_email_addr"] != None:
                reciever_email_addr = data["reciever_email_addr"]
                logger.log(f"\nInside reciever_email_addr value:::\t{reciever_email_addr} \t{type(reciever_email_addr)}","0")

            if "receiver_email_pwd" in data and data["receiver_email_pwd"] != None:
                receiver_email_pwd = data["receiver_email_pwd"]
                logger.log(f"\nInside receiver_email_pwd value:::\t{receiver_email_pwd} \t{type(receiver_email_pwd)}","0")

            if "host_name" in data and data["host_name"] != None:
                host_name = data["host_name"]
                logger.log(f"\nInside host_name value:::\t{host_name} \t{type(host_name)}","0")
            
            if "sender_email_addr" in data and data["sender_email_addr"] != None:
                sender_email_addr = data["sender_email_addr"]
                logger.log(f"\nInside sender_email_addr value:::\t{sender_email_addr} \t{type(sender_email_addr)}","0")

            if "cc_email_addr" in data and data["cc_email_addr"] != None:
                cc_email_addr = data["cc_email_addr"]
                logger.log(f"\nInside cc_email_addr value:::\t{cc_email_addr} \t{type(cc_email_addr)}","0")

            if "subject" in data and data["subject"] != None:
                subject = data["subject"]
                logger.log(f"\nInside subject value:::\t{subject} \t{type(subject)}","0")

            if "email_body" in data and data["email_body"] != None:
                email_body = data["email_body"]
                logger.log(f"\nInside email_body value:::\t{email_body} \t{type(email_body)}","0")

            if "signature" in data and data["signature"] != None:
                signature = data["signature"]
                logger.log(f"\nInside signature value:::\t{signature} \t{type(signature)}","0")
            

            email_config = {
                "email": data["reciever_email_addr"],
                "password": data["receiver_email_pwd"],
                "host": data["host_name"]
            }
            logger.log(f"data::{data}")
            email_details = {
                "from": data["sender_email_addr"],
                "to":data["reciever_email_addr"],
                "cc": cc_email_addr,
                "subject": data["subject"],
                "body": data["email_body"],
                "signature": data["signature"]
            }

            success, draft_message = self.draft_email_response(email_details)
            
            if success == "Success":
                logger.log(f"draft_message  {draft_message}")
                return draft_message

        except Exception as e:
            logger.log(f"Error in Draft_Save: {str(e)}")

    def align_numeric_cells_right(self,table_html):
        soup = BeautifulSoup(table_html, 'html.parser')
        rows = soup.find_all('tr')

        for row in rows[1:]:  # Skip header row
            cells = row.find_all('td')
            for cell in cells:
                text = cell.get_text(strip=True)
                # Check if the content is numeric (int or float)
                try:
                    float(text.replace(',', ''))  # Handle values like '7,500.00'
                    # If 'text-align: right;' is not present, add it
                    style = cell.get('style', '')
                    if 'text-align: right' not in style:
                        if style:
                            style += '; '
                        style += 'text-align: right;'
                        cell['style'] = style
                except ValueError:
                    continue  # Not numeric

        return str(soup)
