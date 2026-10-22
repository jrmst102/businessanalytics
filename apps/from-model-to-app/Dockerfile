# Hosted deployment image: Python engine API + Node.js dashboard in one container.
# Local use does not need Docker (see README.md: python launch.py).
FROM python:3.12-slim

# Node.js for the web server (Debian's nodejs >= 18 is sufficient).
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Engine dependencies (the test-only packages add little; one layer keeps it simple).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Web server dependencies.
COPY server/package.json server/package-lock.json server/
RUN npm ci --prefix server --omit=dev

COPY . .

ENV PORT=8080 ENGINE_URL=http://127.0.0.1:8000
EXPOSE 8080
CMD ["bash", "start.sh"]
