FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libxss1 \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome WebDriver
RUN CHROME_DRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# Upgrade pip
RUN pip install --upgrade pip

# Install basic Python packages first
RUN pip install --no-cache-dir wheel setuptools

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies with error handling
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Retrying installation with additional dependencies..." && \
     pip install --no-cache-dir -r requirements.txt)

# If still having issues with specific packages, install them separately
RUN pip install --no-cache-dir python-telegram-bot==20.3 \
    gspread==5.10.0 \
    oauth2client==4.1.3 \
    python-dotenv==1.0.0 \
    urllib3==2.0.7 \
    beautifulsoup4==4.12.2 \
    schedule==1.2.0 \
    selenium==4.9.0 \
    webdriver-manager==3.8.6

# Copy the application code
COPY . .

# Set environment variables
ENV USE_SELENIUM=true
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:${PATH}"

# Run the application
CMD ["python", "main.py"]
