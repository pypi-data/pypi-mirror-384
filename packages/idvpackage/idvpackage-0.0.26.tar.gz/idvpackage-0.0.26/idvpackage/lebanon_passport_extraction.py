import json
import time
import openai
import re
import logging
import json
import time
import datetime
import openai
from langchain.tools import tool
from langchain.tools.render import format_tool_to_openai_function
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field, validator
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from typing import Optional, Literal
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
import idvpackage.genai_utils as genai_utils
import idvpackage.genai_utils as sanity_utils
from idvpackage.genai_utils import convert_pydantic_to_openai_function2
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pydantic import ValidationError
import logging
from langchain.schema.agent import AgentFinish

import openai
import json

import openai
import json

class Verify_LBN_Passport(BaseModel):
    """Validates whether a given OCR text represents a valid Lebanese Passport"""
    is_valid_id: Literal["True", "False", ""] = Field(..., description="Return True if document is a valid Lebanese Passport" 
            "It should contain English Text: Republic of Lebanon"
            "It should contain things a passport typically has like two-line mrz, date of issue, expiry, name, etc."
            "Return False otherwise.")

@tool(args_schema=Verify_LBN_Passport)
def verify_lbn_passport(is_valid_id):
    return is_valid_id

def route(result):
    if isinstance(result, AgentFinish):
        return result.return_values['output']
    else:
        tools = {
            "verify_lbn_passport": verify_lbn_passport
        }
        return tools[result.tool].run(result.tool_input)

def verify_lbn_pss_chain(ocr_text, openai_key):
    gpt_model = 'gpt-4o'
    print("WE ARE IN EXTRACTION CHAIN")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at identifying Lebanese Passports."
         ),
        ("user", "{ocr_text}")
    ])

    model = ChatOpenAI(model=gpt_model, temperature=0,
                       openai_api_key=openai_key)
    functions = [convert_pydantic_to_openai_function(Verify_LBN_Passport)]
    verification_model = model.bind(functions=functions)
    verification_chain = prompt | verification_model | JsonOutputFunctionsParser()

    result = verification_chain.invoke({"ocr_text":ocr_text})
    is_valid_id = result.get("is_valid_id","")
    return is_valid_id

def make_api_request_with_retries(prompt: str, max_retries: int = 3, delay_seconds: float = 2):
    """
    Helper function to make API requests with retry logic using OpenAI
    """
    for attempt in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                temperature=0.4,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            logging.info(f"OpenAI successfully prompted.{response.choices[0].message.content} ")
            result = response.choices[0].message.content

            try:
                return json.loads(result)
            except json.JSONDecodeError:
                try:
                    json_match = re.search(r'```(json|python|plaintext)?\s*(.*?)\s*```|\s*({.*?})', result, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(2) or json_match.group(3)
                        try:
                            return json.loads(json_str)
                        except:
                            return eval(json_str.replace("'", '"'))
                except:
                    pass

            return json.loads(result)

        except Exception as e:
            print(f"Error during API request (attempt {attempt + 1} of {max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay_seconds)
            else:
                raise Exception(f"Max retries exceeded. Last error: {str(e)}")


def lebanon_passport_extraction(passport_data):
    try:
        prompt = f"From the attached text, please extract the data in a structured format, the response should be a dictionary, having first_name(only English), mother_name(mother english name if available, else empty string ''), father_name(only English), name which is last_name(only English), passport_number, dob(dd/mm/yyyy), place_of_birth, nationality(ISO 3166-1 alpha-3 country code), issue_date(dd/mm/yyyy), expiry_date(dd/mm/yyyy), gender(FEMALE, MALE), mrz1, mrz2, registry_place_and_issue_number(if not available then empty string ''). Note that the passport_number should always be  2 letters and 7 digits, if the length is less than 7 then append 0 in the start for passport_number_en and same way for passport_number_ar(numbers in passport arabic as well). Also note that the names should be extracted correctly, don't pick any random words for names, especially for first and last_name, it can be verified from the mrz1 string. So please make sure the names are correctly extracted.  The structure of the response should be 'first_name', 'father_name', 'last_name', 'mother_name', 'id_number', 'dob', 'expiry_date', 'issue_date', 'place_of_birth', nationality, registry_place_and_issue_number, etc.. Make sure that the response should only contain a dictionary, and nothing else. Here's the text for your task: {passport_data}"

        back_data = make_api_request_with_retries(prompt)

        if back_data:

            if back_data.get('registry_place_and_issue_number', ''):
                back_data['registry_place_and_number'] = back_data.pop('registry_place_and_issue_number', '')

            if back_data.get('passport_number', ''):
                back_data['id_number'] = back_data.pop('passport_number', '')

            if back_data.get('mrz1', '') and back_data.get('mrz2', ''):
                back_data['mrz'] = back_data.get('mrz1', '') + back_data.get('mrz2', '')

            back_data['issuing_country'] = 'LBN'

            if not back_data.get('nationality', ''):
                back_data['nationality'] = 'LBN'

            if "gender" in back_data:
                gender = back_data["gender"].strip().upper()
                if gender == "F":
                    back_data["gender"] = "FEMALE"
                elif gender == "M":
                    back_data["gender"] = "MALE"

            if 'gender' in back_data:
                back_data["gender"] = back_data["gender"].strip().upper()


    except Exception as e:
        print(f"Error in processing the extracted data: {e}")
        back_data = {
            'first_name': '',
            'last_name': '',
            'dob': '',
            'place_of_birth': '',
            'expiry_date': ''
        }

    return back_data
