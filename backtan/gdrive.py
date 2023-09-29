from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


class GDrive:
    def __init__(self, token_dir, time_zone):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        SCOPES = ['https://www.googleapis.com/auth/drive']
        self.creds = None

        self.time_zone = ZoneInfo(time_zone)
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

    def delete_old_files(self, param_dict, threshold_storage_date):
        """Search file in drive location

        https://developers.google.com/drive/api/guides/search-files
        https://developers.google.com/drive/api/reference/rest/v3/files
        https://developers.google.com/drive/api/reference/rest/v3/files/list
        """
        params = '("{}" in parents) and (mimeType = "{}")'.format(
            param_dict['folder_id'],
            param_dict['mimetype']
        )
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.creds)
            delete_files = []
            page_token = None
            while True:
                # pylint: disable=maybe-no-member
                response = service.files().list(q=params,
                                                spaces='drive',
                                                fields='nextPageToken, '
                                                'files(id, name, createdTime, trashed)',
                                                pageToken=page_token).execute()
                for file in response.get('files', []):
                    # createdTimeはUTCなので、タイムゾーンを変換する
                    created_utc = datetime.fromisoformat(file.get('createdTime'))
                    converted_timezone = created_utc.astimezone(self.time_zone)
                    # ゴミ箱に移動されていなくて保管期限日付を過ぎていたら、ファイル削除
                    if converted_timezone.date() < threshold_storage_date and not file.get('trashed'):
                        service.files().delete(
                            fileId=file.get('id')
                        ).execute()
                        delete_files.append('{}({})'.format(file.get('name'), file.get('id')))
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

            if len(delete_files) == 0:
                return None
            return {'level': 'info', 'result': 'Succeeded', 'detail': delete_files}
        except HttpError as error:
            print(F'An error occurred: {error}')
            return {'level': 'error', 'result': 'Failed', 'detail': str(error)}
