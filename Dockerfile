FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget unzip curl fonts-liberation libasound2 libgtk-3-0 libnss3 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Use official Chromedriver version 141 for Chrome 141.x
RUN wget -q https://storage.googleapis.com/chrome-for-testing-public/141.0.7390.0/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm -rf chromedriver-linux64 chromedriver-linux64.zip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
