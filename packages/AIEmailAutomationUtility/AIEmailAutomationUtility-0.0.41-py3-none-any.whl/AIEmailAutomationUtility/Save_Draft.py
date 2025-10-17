import cx_Oracle
from DatabaseConnectionUtility import Oracle 
from DatabaseConnectionUtility import Dremio
from DatabaseConnectionUtility import InMemory 
from DatabaseConnectionUtility import Oracle
from DatabaseConnectionUtility import MySql
from DatabaseConnectionUtility import MSSQLServer 
from DatabaseConnectionUtility import SAPHANA
from DatabaseConnectionUtility import Postgress
import loggerutility as logger
import commonutility as common
import traceback
import imaplib
from email.message import Message
import datetime
import time

class Save_Draft:

    connection = None
    
    def get_database_connection(self, dbDetails):
        if dbDetails['DB_VENDORE'] != None:
            klass = globals()[dbDetails['DB_VENDORE']]
            dbObject = klass()
            connection_obj = dbObject.getConnection(dbDetails)
        return connection_obj

    def commit(self):
        if self.connection:
            try:
                self.connection.commit()
                print("Transaction committed successfully.")
            except cx_Oracle.Error as error:
                print(f"Error during commit: {error}")
        else:
            print("No active connection to commit.")

    def rollback(self):
        if self.connection:
            try:
                self.connection.rollback()
                print("Transaction rolled back successfully.")
            except cx_Oracle.Error as error:
                print(f"Error during rollback: {error}")
        else:
            print("No active connection to rollback.")

    def close_connection(self):
        if self.connection:
            try:
                self.connection.close()
                print("Connection closed successfully.")
            except cx_Oracle.Error as error:
                print(f"Error during close: {error}")
        else:
            print("No active connection to close.")

    def draft_Email(self, reciever_email_addr, receiver_email_pwd, host_name, sender_email_addr, cc_email_addr, subject, email_body):
        try:
            mail_details = ""
            with imaplib.IMAP4_SSL(host=host_name, port=imaplib.IMAP4_SSL_PORT) as imap_ssl:
                resp_code, response = imap_ssl.login(reciever_email_addr, receiver_email_pwd)
                message = Message()
                message["From"] = reciever_email_addr
                message["To"]   = sender_email_addr
                message["CC"]   = cc_email_addr
                
                if subject.startswith("Re:"):
                    message["Subject"] = f"{subject} "
                else:
                    message["Subject"] = f"Re: {subject} "

                mail_details = f'{datetime.datetime.now().strftime("On %a, %b %d, %Y at %I:%M %p")} {sender_email_addr} wrote:'
                message.set_payload(f"{email_body}\n\n{mail_details}")      
                utf8_message = str(message).encode("utf-8")
                
                imap_ssl.append("[Gmail]/Drafts", '', imaplib.Time2Internaldate(time.time()), utf8_message)
                print("Draft Mail saved successfully.")

                return "Success"
        
        except Exception as error:
            print(f"Error ::: {error}")
            return "Fail"

    def check_drafts(self, dbDetails, email_info):

        while True:

            self.connection = self.get_database_connection(dbDetails)

            if self.connection:
                try:

                    cursor = self.connection.cursor()
                    queryy = f"SELECT * FROM DRAFT_EMAIL_INFO WHERE STATUS = 'Pending'"
                    cursor.execute(queryy)
                    pending_records = cursor.fetchall()
                    cursor.close()

                    for data in pending_records:
                        # print(f"data ::: {data}")
                        response = self.draft_Email(email_info['email'], email_info['password'], email_info['host'], data[0], data[1], data[2], data[3].read())
                        if response == 'Success':
                            cursor = self.connection.cursor()
                            update_query = """
                                UPDATE DRAFT_EMAIL_INFO SET
                                    STATUS = :status
                                WHERE TRIM(TO_EMAIL) = TRIM(:to_email)
                                AND TRIM(SUBJECT) = TRIM(:subject)
                            """
                            values = {
                                'status': 'Done',
                                'to_email': data[0],
                                'subject': data[2]
                            }
                            cursor.execute(update_query, values)
                            print(f"Successfully updated row.")
                            cursor.close()

                            self.commit()
                    
                except Exception as e:
                    print(f"Rollback due to error: {e}")
                    
                finally:
                    print('Closed connection successfully.')
                    self.close_connection()
            else:
                print(f'\n In getInvokeIntent exception stacktrace : ', "1")
                descr = str("Connection fail")
                print(f'\n Exception ::: {descr}', "0")

            time.sleep(10)


