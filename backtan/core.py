import datetime
import re
import mimetypes
from pathlib import Path
from config import Config
from ssh import Ssh
from gdrive import GDrive
from logger import Logger


def main():
    # 設定読み込み
    cfg = Config()

    # 現在時刻で出力ファイル名作成
    dt_now = datetime.datetime.now()
    file_name = '{}_{}.sql'.format(dt_now.strftime('%y%m%d-%H%M%S'), cfg.DB['NAME'])

    # 実行コマンド末尾にファイル名を足す
    # mysqldump --opt --single-transaction -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > file_name
    cfg.COMMAND += file_name

    # SSH接続
    ssh = Ssh(cfg.SSH['HOSTNAME'], cfg.SSH['CONFIG'])
    log.logging('info', 'SSH to {}({})'.format(cfg.SSH['HOSTNAME'], ssh.config['hostname']))

    # ログにはパスワード部分を置換したコマンドを記載
    log.logging('info', 'Exec Command: {}'.format(re.sub('-p.* ', '-p[password] ', cfg.COMMAND)))
    # サーバー上でDBバックアップ
    command_result = ssh.exec_command('cd {}; {}'.format(cfg.EXEC_DIR, cfg.COMMAND))
    detail = '({})'.format(command_result['detail']) if command_result['detail'] else ''
    log.logging(command_result['level'], 'Command Result: {}{}'.format(command_result['result'], detail))
    if command_result['level'] == 'error':
        return
    else:
        # バックアップ成功したら、古いファイルは削除
        remove_result = ssh.remove_old_files(dt_now, cfg.EXEC_DIR, cfg.THRESHOLD_STORAGE_DAYS)

        if remove_result is None:
            log.logging('info', 'No files are older than {} days'.format(cfg.THRESHOLD_STORAGE_DAYS))
        else:
            log.logging(remove_result['level'], 'Remove Result: {}'.format(remove_result['result']))
            log.logging(remove_result['level'], 'Removed Files: {}'.format(remove_result['detail']))

    # バックアップしたファイルのフルパス取得(srtip()で改行削除)
    download_target = ssh.exec_command('cd {}; ls `pwd`/{}'.format(cfg.EXEC_DIR, file_name))
    download_target['detail'] = download_target['detail'].strip()
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
        'parents': [cfg.UPLOAD_FOLDER_ID]
    }

    # Google Driveにアップロード
    token_dir = Path(root_dir).joinpath('token')
    gdrive = GDrive(token_dir)
    upload_result = gdrive.upload(downlaod_file_path, file_metadata)
    log.logging(upload_result['level'], 'Upload Result: {}({})'.format(upload_result['result'], upload_result['detail']))


if __name__ == '__main__':
    # プロジェクトルート
    root_dir = Path(__file__).resolve().parents[1]
    # ログ
    log = Logger(root_dir)
    log.logging('info', '===== backtan start =====')

    main()

    log.logging('info', '===== backtan end =====')
