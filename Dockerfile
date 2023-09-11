FROM python:3.11

WORKDIR $APP_HOME

COPY . .

EXPOSE 3000

ENTRYPOINT ["python", "main.py"]
