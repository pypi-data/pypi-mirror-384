import logging
from typing import Dict, Any, List, Optional


class VendorFormValidationError(Exception):
    """Custom exception for vendor form validation errors."""
    pass


class VendorIntakeForm:
    """
    Handles vendor intake form operations for the Whistic API.

    This class provides methods to retrieve the vendor intake form
    from the Whistic platform and generate form submissions.
    """

    def __init__(self, whistic_instance):
        """
        Initialize VendorIntakeForm with a Whistic instance.

        Args:
            whistic_instance: The main Whistic client instance
        """
        self.whistic = whistic_instance
        self.question_map = None
        self.required_questions = None
        self.all_questions = None

    def get(self):
        """
        Get the vendor intake form from /company/vendor-intake-form.

        Returns:
            dict: The vendor intake form data if successful, None otherwise
        """
        logging.debug("Querying vendor intake form")
        url = f"{self.whistic.endpoint}/company/vendor-intake-form"
        response = self.whistic._make_request_with_retry(url)

        if response and response.status_code == 200:
            logging.info(f"{response.status_code} - {url}")
            return response.json()
        else:
            if response:
                logging.error(f"{response.status_code} - {url} - {response.content}")
            return None

    def show(self):
        '''show the intake form in a way we can add the fields to the vendor_intake process'''
        vif = self.get()

        frm = {}
        for i in vif['sections']:
            for c in i['columns']:
                for q in c['questions']:
                    frm[f"{i['title']}:{q['text']}"] = ""
        print("vendor_intake_form(")
        for i in frm:
            print(f"   \"{i}\" : \"TODO\",")
        print("  )")

    def vendor_intake(self,data):
        vif = self.get()
        # == validate we got the required data in the form
        # This is a list of fields that are in the vendor intake form that should not make their way to the custom attributes
        fields_to_ignore = {
            "Vendor Information" : [
                "Job Title",
                "Vendor URL",
                "Vendor Name",
                "Product / Service Name",
                "Write a description of the vendor / service",
                "First Name",
                "Last Name",
                "Email Address",
                "Type of Vendor",
                "Job Title",
                "Phone Number"
            ],
            "Primary Business Owner Information" : [
                "First Name",
                "Last Name",
                "Email Address"
            ]
        }
        custom_attributes = []
        error = False
        for i in vif['sections']:
            custom_attributes_this = {
                "section" : i['title'],
                "attributes" : []
            }
            for c in i['columns']:
                for q in c['questions']:
                    # Only include the fiels that are not on the ignore list
                    if q['text'] not in fields_to_ignore.get(i['title'],[]):
                        key = f"{i['title']}:{q['text']}"
                        if q['answer_required']:
                            if key not in data:
                                logging.error(f"Missing required question: {key}")
                                error = True
                        if 'answer_text' in q and key in data:
                            q['answer_text'] = [ data[key] ]
                            custom_attributes_this['attributes'].append({
                                    'identifier' : q['identifier'],
                                    'answer_required' : q['answer_required'],
                                    'values' : q['answer_text'],
                                    'label' : q['text'],
                                    'type' : q['type']
                                })
                            
                        if 'answer_options' in q and key in data:
                            if data[key] not in q['answer_options']:
                                logging.error(f"Question {key} has an invalid option")
                                error = True
                                for option in q['answer_options']:
                                    logging.error(f" - Valid option: {option}")
                            else:
                                q['chosen_answers'] = [ data[key]]
                                custom_attributes_this['attributes'].append({
                                    'identifier' : q['identifier'],
                                    'answer_required' : q['answer_required'],
                                    'values' : q['chosen_answers'],
                                    'label' : q['text'],
                                    'type' : q['type']
                                })
            if len(custom_attributes_this['attributes']) != 0:
                custom_attributes.append(custom_attributes_this)
        if error:
            logging.error("Validation errors found. Fix the errors before submitting the form.")
            raise VendorFormValidationError("Form validation failed. Check logs for details.")

        # generate the payload
        payload = {
            'url'           : data.get('Vendor Information:Vendor URL', ''),
            'name'          : data.get('Vendor Information:Vendor Name', ''),
            'service'       : data.get('Vendor Information:Product / Service Name', ''),
            'description'   : data.get('Vendor Information:Write a description of the vendor / service', ''),
            'status'        : 'ACTIVE',
            'vendor_intake_form_identifier' : vif['identifier'],
            "external_contacts": [{
                "title"     : data.get('Vendor Information:Job Title',''),
                "first_name": data.get('Vendor Information:First Name', ''),
                "last_name" : data.get('Vendor Information:Last Name', ''),
                "email"     : data.get('Vendor Information:Email Address', ''),
                "phone"     : data.get('Vendor Information:Phone Number',''),
                "type"      : "INTERNAL",
                "editable"  : True
            }],
            "internal_contacts": [{
                "first_name": data.get('Primary Business Owner Information:First Name', ''),
                "last_name": data.get('Primary Business Owner Information:Last Name', ''),
                "email": data.get('Primary Business Owner Information:Email Address', ''),
                "phone": data.get('Primary Business Owner Information:Phone Number', ''),
                "type": "INTERNAL",
                "editable": True
            }],
            "custom_attributes" : custom_attributes,
            "enable_smart_search": False,
            "_links": {
                "self": {
                "href": "string",
                "templated": True,
                "title": "string",
                "type": "string"
                }
            }
        }

        # Use the Vendors class to create the new vendor
        logging.debug("Submitting vendor intake form")
        result = self.whistic.vendors.new(payload)

        if result:
            logging.info("Vendor intake form submitted successfully")
            return True
        else:
            logging.error("Failed to submit vendor intake form")
            return False

