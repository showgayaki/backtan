import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    def __init__(self, config_file_path=str(Path.home().joinpath('.ssh', 'config'))):
        load_dotenv()

        self.SSH = {
            'HOSTNAME': os.environ.get('SSH_HOSTNAME'),
            'CONFIG': config_file_path,
        }
        self.DB = {
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASS': os.environ.get('DB_PASSWORD'),
        }
        self.COMMAND = os.environ.get('COMMAND')
        self.EXEC_DIR = os.environ.get('EXEC_DIR')
        self.UPLOAD_FOLDER_ID = os.environ.get('UPLOAD_FOLDER_ID')
