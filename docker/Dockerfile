FROM python:3.12-slim

RUN pip3 install wheel
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" >/etc/timezone  

# 先只复制 requirements.txt
COPY requirements.txt ./

# 安装依赖（利用缓存）
RUN pip3 install flask_frame:1.0.0

RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN chmod +x ./script/run.sh
