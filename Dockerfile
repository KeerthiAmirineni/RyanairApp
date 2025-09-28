
FROM python:3.10-slim
WORKDIR /app

# Install system dependencies for Playwright browsers
RUN apt-get update && apt-get install -y \
	wget \
	ca-certificates \
	fonts-liberation \
	libasound2 \
	libatk-bridge2.0-0 \
	libatk1.0-0 \
	libcups2 \
	libdbus-1-3 \
	libdrm2 \
	libexpat1 \
	libgbm1 \
	libglib2.0-0 \
	libgtk-3-0 \
	libnspr4 \
	libnss3 \
	libpango-1.0-0 \
	libx11-xcb1 \
	libxcomposite1 \
	libxdamage1 \
	libxext6 \
	libxfixes3 \
	libxkbcommon0 \
	libxrandr2 \
	xdg-utils \
	--no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY src/ /app/src/
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install

CMD ["python", "src/book_ryanair.py"]