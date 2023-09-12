from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class GDrive:
    def __init__(self, token_dir):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        SCOPES = ['https://www.googleapis.com/auth/drive']
        self.creds = None

        credentials_file_path = Path(token_dir).joinpath('credentials.json')
        token_file_path = Path(token_dir).joinpath('token.json')

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if token_file_path.exists():
            self.creds = Credentials.from_authorized_user_file(token_file_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file_path), SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file_path, 'w') as token:
                token.write(self.creds.to_json())

    def upload(self, local_file_path, file_metadata):
        """Insert new file.
        Returns : Id's of the file uploaded
        """
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.creds)

            media = MediaFileUpload(
                local_file_path,
                mimetype=file_metadata['mimeType']
            )

            file = service.files().create(body=file_metadata, media_body=media,
                                          fields='id').execute()
            return {'level': 'info', 'result': 'Succeeded', 'detail': 'File ID: {}'.format(file.get('id'))}

        except HttpError as error:
            return {'level': 'error', 'result': 'Failed', 'detail': str(error)}
