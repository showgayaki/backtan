import argparse
import datetime
import re
import mimetypes
from pathlib import Path

from config import Config
from ssh import Ssh
from gdrive import GDrive
from logger import Logger


class Args(argparse.Namespace):
    db: list[str] | None


def parse_args() -> Args:
    parser = argparse.ArgumentParser(description='Backtan Database Backup Tool')
    parser.add_argument(
        '--db',
        nargs='+',  # 複数指定できる
        help='Database name(s) to backup. If omitted, all databases in config.json are backed up.',
    )
    return parser.parse_args(namespace=Args())


def main(selected_dbs: list[str] | None = None) -> None:
    # 設定読み込み
    cfg = Config().config
    log.logging('info', f'Selected DB(s): {selected_dbs}')

    for db in cfg.DATABASES:
        if selected_dbs and db.NAME not in selected_dbs:
            continue

        log.logging('info', f'--- Starting backup DB: {db.NAME} ---')

        # 現在時刻で出力ファイル名作成
        dt_now = datetime.datetime.now()
        file_name = '{}_{}.sql'.format(dt_now.strftime('%y%m%d-%H%M%S'), db.NAME)
        # 保存期限の日付を計算
        threshold_storage_date = (dt_now - datetime.timedelta(days=db.THRESHOLD_STORAGE_DAYS)).date()

        # SSH接続
        ssh = Ssh(cfg.SSH_HOST)
        log.logging('info', 'SSH to {}({})'.format(cfg.SSH_HOST, ssh.config['hostname']))

        # 実行コマンド
        # mysqldump --opt --single-transaction -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > file_name
        exec_command = cfg.EXEC_COMMAND.replace("${DB_USER}", db.USER).replace("${DB_PASSWORD}", db.PASSWORD).replace("${DB_NAME}", db.NAME)
        exec_command = f'{exec_command}{file_name}'
        # ログにはパスワード部分を置換したコマンドを記載
        log.logging('info', 'Exec Command: {}'.format(re.sub('-p\\S+\\s', '-p[password] ', exec_command)))
        # サーバー上でDBバックアップ
        command_result = ssh.exec_command(f'{cfg.EXEC_DIR}/{db.NAME}', exec_command)
        detail = '({})'.format(command_result['detail']) if command_result['detail'] else ''
        log.logging(command_result['level'], 'Command Result: {}{}'.format(command_result['result'], detail))
        if command_result['level'] == 'error':
            return
        else:
            # バックアップ成功したら、古いファイルは削除
            remove_result = ssh.remove_old_files(f'{cfg.EXEC_DIR}/{db.NAME}', threshold_storage_date)

            if remove_result is None:
                log.logging('info', 'SSH server: No files are older than {} days'.format(db.THRESHOLD_STORAGE_DAYS))
            else:
                log.logging(remove_result['level'], 'Remove Result: {}'.format(remove_result['result']))
                log.logging(remove_result['level'], 'Removed Files: {}'.format(remove_result['detail']))

        # バックアップしたファイルのフルパス取得
        download_target = ssh.exec_command(f'{cfg.EXEC_DIR}/{db.NAME}', f'ls `pwd`/{file_name}')
        log.logging(download_target['level'], 'Download Target: {}'.format(download_target['detail']))
        if download_target['level'] == 'error':
            return

        # ダウンロードディレクトリ
        downlaod_dir = Path(root_dir).joinpath('download')
        if not downlaod_dir.is_dir():
            Path.mkdir(downlaod_dir)
            log.logging('info', 'Make Directory: {}'.format(downlaod_dir))
        downlaod_file_path = Path(downlaod_dir).joinpath(file_name)

        # バックアップしたファイルをSFTPでダウンロード
        download_result = ssh.sftp_download(download_target['detail'], str(downlaod_file_path))
        log.logging(download_result['level'], 'Download Result: {}({})'.format(download_target['result'], download_result['detail']))
        if download_result['level'] == 'error':
            return

        # ダウンロードしたファイルのMIMEタイプ取得
        mimetype, _ = mimetypes.guess_type(downlaod_file_path)
        file_metadata = {
            'name': file_name,
            'mimeType': mimetype,
            'parents': [db.UPLOAD_FOLDER_ID]
        }

        # Google Driveにアップロード
        token_dir = Path(root_dir).joinpath('token')
        log.logging('info', 'Start Upload to Google Drive.')
        gdrive = GDrive(token_dir, cfg.TIME_ZONE)

        upload_result = gdrive.upload(downlaod_file_path, file_metadata)
        log.logging(upload_result['level'], 'Upload Result: {}({})'.format(upload_result['result'], upload_result['detail']))

        if upload_result['level'] == 'error':
            return
        else:
            # アップロード成功したら、古いファイルは削除
            params = {
                'folder_id': db.UPLOAD_FOLDER_ID,
                'mimetype': mimetype
            }
            delete_result = gdrive.delete_old_files(params, threshold_storage_date)

            if delete_result is None:
                log.logging('info', 'Google Drive: No files are older than {} days'.format(db.THRESHOLD_STORAGE_DAYS))
            else:
                log.logging(delete_result['level'], 'Delete Result: {}'.format(delete_result['result']))
                log.logging(delete_result['level'], 'Deleted Files: {}'.format(delete_result['detail']))


if __name__ == '__main__':
    # プロジェクトルート
    root_dir = Path(__file__).resolve().parents[1]
    # ログ
    log = Logger(root_dir)
    log.logging('info', '===== backtan start =====')

    args = parse_args()
    main(args.db)

    log.logging('info', '===== backtan end =====')
