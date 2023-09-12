#!/bin/bash
cd `dirname $0`
source .venv/bin/activate

# 「token.json」がなければ、「--noauth_local_webserver」オプションをつける
# --noauth_local_webserverについては、このへん↓
# https://zenn.dev/wtkn25/articles/python-googledriveapi-auth#quickstart.pyを実行する
# https://tech-blog.fancs.com/entry/2017/12/04/Gmail_API取得できたけど、Oauth認証でひっかかった話#--noauth_local_webserver-オプション
if [ -e "./token/token.json" ]; then
    python backtan/core.py
else
    python backtan/core.py  --noauth_local_webserver
fi
