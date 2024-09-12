import io
import json
import datetime
import requests
import pytz
from custom_exception import DBException
from db_manager import MySqlDBManager

utc=pytz.UTC


class Rules:
    def __init__(self):
        self.endpoint = "https://gmail.googleapis.com/gmail/v1/users/me/messages/"
        self.token = None
        self.rules = []
        self.field_map = {
            'subject': 'Subject',
            'from': 'From',
            'to': 'To',
            'date_received': 'Date'
        }
        self.predicate_validator = {
            'contains': lambda x, y: y in x,
            'equals': lambda x, y: x == y,
            'not_equals': lambda x, y: x != y,
            'less_than': lambda x, y: x < y,
            'greater_than': lambda x, y: x > y,
            'does_not_contains':lambda x, y: y not in x
        }
        self.con_obj = MySqlDBManager()

    def __get_token(self):
        try:
            with io.open('token.json', "r", encoding="utf-8") as json_file:
                self.token = json.load(json_file)
            if 'token' not in self.token:
                raise ValueError("Token not found in token.json file")
        except Exception as exp:
            print(f'Exception in {self.__get_token.__name__}: {exp}')
            raise exp

    def __get_emails(self):
        try:
            query = "SELECT * FROM emails WHERE processed = (%s) ORDER BY id"
            query_args = (False,)
            emails = self.con_obj.processquery(query, arguments=query_args)
            return emails
        except Exception as exp:
            print(f'Exception in {self.__get_emails.__name__}: {exp}')
            raise DBException(exp)

    def __mark_email_as_processed(self, message_id, label_ids):
        try:
            query = "UPDATE emails SET processed = (%s), modified_datetime=now(),modified_by=%s,label_ids = %s WHERE message_id = (%s)"
            query_args = (True, "execute_rules", label_ids, message_id)
            self.con_obj.processquery(query, arguments=query_args, fetch=False)
            self.con_obj.conn.commit()
        except Exception as exp:
            print(f'Exception in {self.__mark_email_as_processed.__name__}: {exp}')
            raise DBException(exp)

    def __fetch_label_ids(self, message_id):
        try:
            headers = {'Authorization': f'Bearer {self.token["token"]}'}
            response = requests.get(self.endpoint + message_id, headers=headers)
            email_data = response.json()
            label_ids = email_data.get('labelIds', [])
            return ','.join(label_ids)
        except Exception as exp:
            print(f'Exception in {self.__fetch_label_ids.__name__}: {exp}')
            raise exp

    def __initiate_rules(self):
        try:
            # Load rules from JSON file
            with open('rules.json', 'r') as file:
                self.rules = json.load(file)
        except Exception as exp:
            print(f'Exception in {self.__initiate_rules.__name__}')
            raise exp

    def process_emails(self):
        existing_mails = self.__get_emails()
        for email in existing_mails:
            payload = json.loads(email['payload'])
            raw_headers = payload['headers']
            processed_headers = {}
            labels = set()

            # Extract headers
            for header in raw_headers:
                if header['name'] in self.field_map.values():
                    processed_headers[header['name']] = header['value']

            for rule_entry in self.rules:
                break_flag = True if rule_entry['predicate'] == 'any' else False
                bool_flag = True

                for rule in rule_entry['rules']:
                    left_value = processed_headers.get(self.field_map[rule['field']], None)
                    if left_value is None:
                        continue  # Skip if the field does not exist
                    right_value = rule['value']

                    if rule['field'] == 'date_received':
                        left_value = left_value.split(" ")[:5]
                        date_value = datetime.datetime.strptime(" ".join(left_value), '%a, %d %b %Y %H:%M:%S')

                        # Check if value is in days or months
                        if 'days' in right_value:
                            days_to_add = int(right_value.split()[0])
                            right_value = date_value + datetime.timedelta(days=days_to_add)
                        elif 'months' in right_value:
                            months_to_add = int(right_value.split()[0])
                            right_value = date_value + datetime.timedelta(
                                days=30 * months_to_add)
                        else:
                            right_value = date_value + datetime.timedelta(days=int(right_value))

                        right_value = right_value.replace(tzinfo=utc)
                        left_value = datetime.datetime.utcnow().replace(tzinfo=utc)

                    # Validate the predicate
                    bool_flag = self.predicate_validator[rule['predicate']](left_value, right_value)
                    if (break_flag and bool_flag) or (not break_flag and not bool_flag):
                        break

                # Apply actions if the rule conditions are met
                if bool_flag:
                    labels = labels | set(rule_entry['action'])

            if labels:
                print("changing labels")
                self.change_labels(email['message_id'], labels)
                # Fetch and update label IDs in the database
                label_ids = self.__fetch_label_ids(email['message_id'])
                self.__mark_email_as_processed(email['message_id'],label_ids)
            else:
                self.__mark_email_as_processed(email['message_id'],email['label_ids'])

    def change_labels(self, message_id, labels):
        try:
            headers = {'Authorization': f'Bearer {self.token["token"]}'}
            data = {
                "addLabelIds": list(labels),
                "removeLabelIds": []
            }

            if "READ" in labels:
                data["removeLabelIds"].append("UNREAD")
                data["addLabelIds"].remove("READ")

            response = requests.post(
                headers=headers,
                url=self.endpoint + message_id + "/modify",
                data=data)
            print(response.json())

        except Exception as exp:
            print(f'Exception in {self.change_labels.__name__}: {exp}')
            raise exp

    def execute(self):
        try:
            self.__get_token()
            self.__initiate_rules()
            self.process_emails()
        except Exception as exp:
            print(f'Exception in {self.execute.__name__}: {exp}')
            raise exp
        finally:
            if self.con_obj.conn:
                self.con_obj.conn.close()


if __name__ == '__main__':
    obj = Rules()
    obj.execute()


