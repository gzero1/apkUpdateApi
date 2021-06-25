FROM python:3.9

WORKDIR /UpdaterApi

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/ .


CMD ["python", "./app.py"]
 