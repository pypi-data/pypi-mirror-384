import traceback
from openai import OpenAI
from openai import OpenAI, AssistantEventHandler
from flask import Flask,request
import json
import loggerutility as logger 
import ast, re

class EmailReplyAssistant:
    class EventHandler(AssistantEventHandler):
        def __init__(self):
            super().__init__()
            self.delta_values = []

        def on_text_created(self, text):
            if isinstance(text, str):
                logger.log(f"\nAssistant: {text}")

        def on_text_delta(self, delta, snapshot):
            self.delta_values.append(delta.value)

        def on_tool_call_created(self, tool_call):
            logger.log(f"\nAssistant: {tool_call.type}\n")

        def on_tool_call_delta(self, delta, snapshot):
            if delta.type == 'code_interpreter':
                if delta.code_interpreter.input:
                    logger.log(delta.code_interpreter.input)
                if delta.code_interpreter.outputs:
                    logger.log(f"\n\nOutput >", flush=True)
                    for output in delta.code_interpreter.outputs:
                        if output.type == "logs":
                            logger.log(output.logs, flush=True)
    def __init__(self):
        pass

    def Reply_Email_Ai_Assistant(self, openAI_key, assistant_ID, email_content, subject):
        try:
            openAI_response = ""
            client = OpenAI(api_key=openAI_key)
            thread = client.beta.threads.create()

            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"subject:{subject}\nemail body:{email_content}",
            )

            event_handler = EmailReplyAssistant().EventHandler()

            with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=assistant_ID,
                instructions=f"Create a reply for the email received from a customer.\nDo not include any instruction as the output will be directly in a program.",
                event_handler=event_handler,
            ) as stream:
                stream.until_done()

            delta_values = event_handler.delta_values
            openAI_response = ''.join(delta_values)
            logger.log(f"openAI_response:: {type(openAI_response)}")
            logger.log(f"openAI_response:: {openAI_response}")
            return {"status": "Success", "message": openAI_response}

        except Exception as error:
            responseStr = "<br/><br/>" + str(error)
            trace = traceback.format_exc()
            logger.log(f"Exception in process_Email: {responseStr} \n {trace} \n DataType ::: {type(responseStr)}")
            m = re.search(r"({.*})", str(error))  
            data = ast.literal_eval(m.group(1)).get('error') if m else {}  
            return {"status": "Failed", "message": data.get('message')}

    def email_reply_assitant(self, data):
        try:
            openAI_key = data.get("openAI_key")
            assistant_ID = data.get("assistant_ID")
            email_content = data.get("email_content")
            subject = data.get("subject")

            if not all([openAI_key, assistant_ID, email_content, subject]):
                raise ValueError("Missing required email configuration fields.")

            email_response = self.Reply_Email_Ai_Assistant(
                openAI_key=openAI_key,
                assistant_ID=assistant_ID,
                email_content=email_content,
                subject=subject
            )

            # logger.log(f"Reply_Email_Ai_Assistant response: {email_response}")
            return email_response

        except Exception as e:
            logger.log(f"Error in Read_Email: {str(e)}")
        
    def create_quotation_draft(self, openAI_key, assistant_ID, email_content, subject, prompt):
        try:
            openAI_response = ""
            client = OpenAI(api_key=openAI_key)
            thread = client.beta.threads.create()

            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"subject:{subject}\nemail body:{email_content}",
            )

            event_handler = EmailReplyAssistant().EventHandler()

            with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=assistant_ID,
                instructions=prompt,
                event_handler=event_handler,
            ) as stream:
                stream.until_done()

            delta_values = event_handler.delta_values
            openAI_response = ''.join(delta_values)
            logger.log(f"openAI_response ::: {openAI_response}")
            formated_openAI_response = openAI_response.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV","").replace("html","")
            return formated_openAI_response

        except Exception as error:
            return None