import json
from openai import OpenAI
import google.generativeai as genai
import openai
import loggerutility as logger 
from flask import Flask,request

class Email_Classification:
    def detect_category_openai(self, openai_api_key, categories, email_body):
        logger.log("Inside detect_category_openai::")
        try:
            categories_str = ', '.join(categories)
            message = [{
                "role": "user",
                "content": f"Classify the mail into one of the following categories: {categories_str} and Others. Based on the email content: {email_body}, provide ONLY the category in JSON format as {{\"category\": \"category\"}}."
            }]
            
            logger.log(f"Final GPT message for detecting category::: {message}")
            client = OpenAI(api_key=openai_api_key)
            result = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=message,
                temperature=0,
                max_tokens=1800,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            category = json.loads(result.choices[0].message.content.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV",""))['category']
            logger.log(f"category:: {category}")
            return {"status": "Success", "message": category}
        except Exception as e:
            logger.log(f"Error detecting category with OpenAI: {str(e)}")
            return {"success": "Failed", "message": f"Error detecting category with OpenAI: {str(e)}"}

    def detect_category_gemini(self, gemini_api_key, categories, email_body, detect_email_category=True, signature=None):
        logger.log("Inside detect_category_gemini::")
        try:
            categories_str = ', '.join(categories) 
            if detect_email_category:
                message = [{
                    "role": "user",
                    "content": f"Classify the mail into one of the following categories: {categories_str} and Others. Based on the email content: {email_body}, provide ONLY the category in JSON format as {{\"category\": \"category\"}}."
                }]
            else:
                message = [{
                    "role": "user",
                    "content": f"Create a reply for the email received from a customer. Include the email signature as {signature}\nDo not include any instruction as the output will be directly in a program."
                }]

            logger.log(f"Final Gemini AI message for detecting category::: {message}")
            message_list = str(message)

            generation_config = {
                "temperature": 0,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            }

            genai.configure(api_key=gemini_api_key)
            # model = genai.GenerativeModel('gemini-1.0-pro')
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(message_list)

            # logger.log(f"Input Question ::: {email_body}\ngemini-1.0-pro Response::: {response} {type(response)}")
            # logger.log(f"\n\nResponse GeminiAI endpoint::::: {response} \n{type(response)}", "0")

            final_result = ""
            for part in response:
                final_result = part.text
                if final_result:
                    try:
                        final_result = final_result.replace("\\", "").replace('```', '').replace('json', '')
                        if final_result.startswith("{{") and final_result.endswith("}}"):
                            final_result = final_result[1:-1]
                        final_result = json.loads(final_result)
                        logger.log(f"finalResult:::  {final_result}")
                    except json.JSONDecodeError:
                        logger.log(f"Exception : Invalid JSON Response GEMINI 1.5: {final_result} {type(final_result)}")

            if detect_email_category:
                category = final_result.get('category', 'Others')
                return {"status": "Success", "message": category}
            else:
                logger.log(f"finalResult:::  {final_result}")
                return {"status": "Success", "message": final_result}

        except Exception as e:
            logger.log(f"Error with Gemini AI detection/generation: {str(e)}")
            return {"success": "Failed", "message": f"Error with Gemini AI detection/generation: {str(e)}"}

    def detect_category_local(self, openai_api_key, categories, email_body, detect_email_category=True, signature=None, local_ai_url=None):
        logger.log("Inside detect_category_local::")
        try:
            categories_str = ', '.join(categories)
            if detect_email_category:
                message = [{
                    "role": "user",
                    "content": f"Classify the mail into one of the following categories: {categories_str} and Others. Based on the email content: {email_body}, provide ONLY the category in JSON format as {{\"category\": \"category\"}}."
                }]
            else:
                message = [{
                    "role": "user",
                    "content": f"Create a reply for the email received from a customer. Include the email signature as {signature}\nDo not include any instruction as the output will be directly in a program."
                }]

            logger.log(f"Final Local AI message for detecting category::: {message}")
            openai.api_key = openai_api_key
            client = OpenAI(base_url=local_ai_url, api_key="lm-studio")
            completion = client.chat.completions.create(
                model="mistral",
                messages=message,
                temperature=0,
                stream=False,
                max_tokens=4096
            )

            final_result = str(completion.choices[0].message.content)
            logger.log(f"\n\nInput Question ::: {email_body}\nLocalAI endpoint finalResult ::::: {final_result} \n{type(final_result)}", "0")

            if detect_email_category:
                try:
                    json_start = final_result.find("{")
                    json_end = final_result.rfind("}") + 1
                    if json_start != -1 and json_end != -1:
                        json_str = final_result[json_start:json_end]
                        final_result = json.loads(json_str)
                        logger.log(f"finalResult:::  {final_result}")
                        category = final_result.get('category', 'Others')
                        logger.log(f"category::1037 {category}")
                        return {"status": "Success", "message": category}
                    else:
                        raise ValueError("No valid JSON object found in the response")
                except json.JSONDecodeError as e:
                    logger.log(f"JSON decode error: {e}")
                    raise
            else:
                logger.log(f"finalResult:1040  {final_result}")
                return {"status": "Success", "message": final_result}

        except Exception as e:
            logger.log(f"Error with LocalAI detection/generation: {str(e)}")
            return {"success": "Failed", "message": f"Error with LocalAI detection/generation: {str(e)}"}

    def detect_category(self, data):
        try:
            model_type = data.get('model_type', 'OpenAI')  
            
            required_fields = ['email_body', 'categories']
            if model_type == 'OpenAI':
                required_fields.append('openai_api_key')
            elif model_type == 'GeminiAI':
                required_fields.append('gemini_api_key')
            elif model_type == 'LocalAI':
                required_fields.extend(['openai_api_key', 'local_ai_url'])

            if model_type == 'OpenAI':
                response = self.detect_category_openai(
                    openai_api_key=data['openai_api_key'],
                    categories=data['categories'],
                    email_body=data['email_body']
                )
            elif model_type == 'GeminiAI':
                response = self.detect_category_gemini(
                    gemini_api_key=data['gemini_api_key'],
                    categories=data['categories'],
                    email_body=data['email_body'],
                    detect_email_category=data.get('Detect_Email_category', True),
                    signature=data.get('signature', '')
                )
            elif model_type == 'LocalAI':
                response = self.detect_category_local(
                    openai_api_key=data['openai_api_key'],
                    categories=data['categories'],
                    email_body=data['email_body'],
                    detect_email_category=data.get('Detect_Email_category', True),
                    signature=data.get('signature', ''),
                    local_ai_url=data['local_ai_url']
                )
            else:
                return {"status": "Failed", "message": f"Invalid model_type: {model_type}"}
            
            logger.log(f"Detect_Category response: {response}")
            return response

        except Exception as e:
            logger.log(f"Error in Detect_Category: {str(e)}")
            return e
