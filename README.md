# backtan
- DBサーバーにSSH
- DBバックアップ
- sqlファイルをダウンロード
- sqlファイルをGoogle Driveにアップロード

する、とっても便利なやつ。


## config.json
プロジェクトルートに置いておく。  
対象のデータベースを増やしたければ、DATABASESに追加していけばよろし。
```
{
    "SSH_HOST": "",
    "DATABASES": [
        {
            "NAME": "",
            "USER": "",
            "PASSWORD": "",
            "UPLOAD_FOLDER_ID": "",  # Google DriveのフォルダーID
            "THRESHOLD_STORAGE_DAYS": 60
        },
        {
            "NAME": "",
            "USER": "",
            "PASSWORD": "",
            "UPLOAD_FOLDER_ID": "",  # Google DriveのフォルダーID
            "THRESHOLD_STORAGE_DAYS": 60
        }
    ],
    "EXEC_COMMAND": "mysqldump --opt --single-transaction -u ${DB_USER} -p${DB_PASSWORD} ${DB_NAME} > ",
    "EXEC_DIR": "~/db",
    "TIME_ZONE": "Asia/Tokyo"
}
```

## Opitons
`--db`: DATABASES[n]["NAME"]のDB名で指定(スペース区切りで複数指定可)  
ex: `[path to]/backtan/run.sh --db camenashi kakeibosan`  

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
ExecStart=[path to]/backtan/run.sh --db kakeibosan

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

`sudo systemctl daemon-reload`  
`sudo systemctl enable backtan.timer`  
`sudo systemctl start backtan.timer`  
