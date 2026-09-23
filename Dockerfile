FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y ffmpeg curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Instala Deno para o yt-dlp resolver os desafios JavaScript do YouTube
RUN curl -fsSL https://deno.land/install.sh | sh

ENV PATH="/root/.deno/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir "yt-dlp[default]" gunicorn Flask

COPY . .

RUN mkdir -p temp

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "300", "app:app"]
