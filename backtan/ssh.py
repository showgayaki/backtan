import paramiko


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
