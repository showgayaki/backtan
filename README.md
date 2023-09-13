# backtan


## .env
```
SSH_HOSTNAME=
DB_NAME=
DB_USER=
DB_PASSWORD=
COMMAND="mysqldump --opt --single-transaction -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > "
EXEC_DIR=
THRESHOLD_STORAGE_DAYS=
UPLOAD_FOLDER_ID=
```

## systemd
`chmod 755 run.sh`  
### service
`sudo vi /lib/systemd/system/backtan.service`  
```
[Unit]
Description=backtan

[Service]
Type=simple
User=[user name]
ExecStart=[path to]/backtan/run.sh

[Install]
WantedBy=multi-user.target
```
### timer 
`sudo vi /lib/systemd/system/backtan.timer`  
```
[Unit]
Description=backtan-timer

[Timer]
OnCalendar=*-*-* 06:00:00

[Install]
WantedBy=timers.target
```