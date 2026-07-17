
FROM python:3.13.14-alpine
RUN apk add --no-cache shadow && groupadd -r GroupForDjango && useradd -r -g GroupForDjango djmanager
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip
WORKDIR /app/www/LibraryData
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN chmod +x entrypoint.sh
USER djmanager
ENTRYPOINT ["./entrypoint.sh"]