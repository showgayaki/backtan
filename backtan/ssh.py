import paramiko
from pathlib import Path
from datetime import date


class Ssh:
    def __init__(self, hostname, config_file_path):
        ssh_config = paramiko.SSHConfig()
        with open(config_file_path, 'r') as f:
            ssh_config.parse(f)

        self.config = ssh_config.lookup(hostname)
        if 'port' not in self.config:
            self.config['port'] = 22

    def exec_command(self, command):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.load_system_host_keys()
        try:
            client.connect(
                self.config['hostname'],
                username=self.config['user'],
                key_filename=self.config['identityfile'],
                port=self.config['port']
            )

            stdin, stdout, stderr = client.exec_command(command)
            cmd_result = ''
            for line in stdout:
                cmd_result += line

            return {'level': 'info', 'result': 'Succeeded', 'detail': cmd_result}
        except Exception as e:
            return {'level': 'error', 'result': 'Failed', 'detail': str(e)}
        finally:
            client.close()
            del client, stdin, stdout, stderr

    def sftp_download(self, server, local):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.load_system_host_keys()
        try:
            client.connect(
                self.config['hostname'],
                username=self.config['user'],
                key_filename=self.config['identityfile'],
                port=self.config['port']
            )
            sftp_connection = client.open_sftp()
            sftp_connection.get(server, local)
            return {'level': 'info', 'result': 'Succeeded', 'detail': local}
        except Exception as e:
            return {'level': 'error', 'result': 'Failed', 'detail': str(e)}
        finally:
            client.close()

    def remove_old_files(self, dt_now, dir, threshold_storage_days):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.load_system_host_keys()
        try:
            client.connect(
                self.config['hostname'],
                username=self.config['user'],
                key_filename=self.config['identityfile'],
                port=self.config['port']
            )
            sftp_connection = client.open_sftp()

            # dir変数から絶対パスを取得
            stdin, stdout, stderr = client.exec_command(f'cd {dir}; pwd')
            dir = [line.strip() for line in stdout][0]
            # dir内のファイルで、拡張子が.sqlのファイルのみリストにして返す
            file_list = [file for file in sftp_connection.listdir(dir) if Path(file).suffix == '.sql']
            file_list.sort()

            removed_files = []
            for file_name in file_list:
                file_path = Path(dir).joinpath(file_name)
                # ファイルのメタデータを取得
                file_stat = sftp_connection.stat(str(file_path))
                # ファイル更新日から何日経ったか計算
                elapsed_days = (dt_now.date() - date.fromtimestamp(file_stat.st_mtime)).days
                if elapsed_days > threshold_storage_days:
                    removed_files.append(str(file_path))
                    client.exec_command('rm {}'.format(file_path))

            if len(removed_files) == 0:
                return None
            return {'level': 'info', 'result': 'Succeeded', 'detail': removed_files}
        except Exception as e:
            print(e)
            return {'level': 'error', 'result': 'Failed', 'detail': str(e)}
        finally:
            client.close()
            del client, stdin, stdout, stderr
