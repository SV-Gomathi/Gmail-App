import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from custom_exception import DBException, DBIntegrityError
from db_manager import MySqlDBManager

class ReadMail:
    def __init__(self):
        self.scopes = ['https://mail.google.com/']
        self.creds = None
        self.service = None
        self.con_obj = MySqlDBManager()

    def __initiate_service(self):
        try:
            if os.path.exists('token.json'):
                self.creds = Credentials.from_authorized_user_file('token.json', self.scopes)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', self.scopes)
                    self.creds = flow.run_local_server(port=8080)

                with open('token.json', 'w') as token:
                    token.write(self.creds.to_json())

            self.service = build('gmail', 'v1', credentials=self.creds)

        except Exception as exp:
            print(f'Exception in {self.__initiate_service.__name__}')
            raise exp

    def __get_last_email_timestamp(self):
        try:
            query = "SELECT received_timestamp from emails ORDER BY id DESC LIMIT 1"
            last_timestamp = self.con_obj.processquery(query, count=1)
            print(f'Last timestamp - {last_timestamp}')
            return last_timestamp['received_timestamp'].rstrip('0') if last_timestamp else 0
        except Exception as exp:
            print(f'Exception in {self.__get_last_email_timestamp.__name__}')
            raise DBException(exp)

    def __add_email(self, email_data):
        try:
            label_ids = json.dumps(email_data.get("labelIds", []))
            query = """ INSERT INTO emails (message_id,
                                            thread_id,
                                            payload,
                                            history_id, 
                                            received_timestamp,
                                            label_ids) 
                                    VALUES (%s, %s, %s, %s, %s,%s) """
            query_args = (email_data["id"],
                          email_data["threadId"],
                          json.dumps(email_data["payload"]),
                          email_data["historyId"],
                          email_data["internalDate"],
                          label_ids)
            self.con_obj.processquery(
                query=query,
                arguments=query_args,
                fetch=False,
                returnprikey=1)
            self.con_obj.conn.commit()
        except DBIntegrityError as exp:
            print(f'Already fetched {email_data["id"]}')
        except Exception as exp:
            print(f'Exception in {self.__add_email.__name__}')
            raise DBException(exp)

    def fetch_and_sync_emails(self):
        last_timestamp = int(self.__get_last_email_timestamp())+2
        try:
            messages = self.service.users().messages().list(
                userId='me',
                maxResults=25,
                q=f'after:{last_timestamp}'
            ).execute()
            messages = messages.get('messages', [])
            for message in reversed(messages):
                email_data = self.service.users().messages().get(userId='me', id=message['id']).execute()
                labels = self.service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
                email_data["labelIds"] = labels.get("labelIds", [])
                self.__add_email(email_data)

        except Exception as exp:
            print(f'Exception in {self.fetch_and_sync_emails.__name__}')
            raise exp

    def execute(self):
        try:
            self.__initiate_service()
            self.fetch_and_sync_emails()
        except Exception as exp:
            print(f'Exception in {self.execute.__name__}')
            raise exp
        finally:
            if self.con_obj.conn:
                self.con_obj.conn.close()


if __name__ == '__main__':
    obj = ReadMail()
    obj.execute()


