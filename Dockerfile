FROM node:16.4.0-buster-slim

COPY requirements.txt  .
RUN apt update && apt install python3 python3-pip git locales locales-all cron -y
RUN python3 -m pip install -r requirements.txt

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && crontab /etc/cron.d/crontab

RUN git clone https://github.com/rino-wallet/frontend

ENV LC_ALL="en_US.UTF-8"
ENV LANG="en_US.UTF-8"
ENV LANGUAGE="en_US.UTF-8"

COPY . .
RUN chmod +x /check_hash.sh
RUN chmod 777 /check_hash.py
ENTRYPOINT ["cron", "-f"]
