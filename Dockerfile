FROM python:3.10-slim

COPY . .

RUN python3 -m pip install -r requirements.txt

ENTRYPOINT [ "python3","kraken.py" ]