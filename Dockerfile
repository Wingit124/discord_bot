FROM python:3.11

WORKDIR /bot

# Install Packages
RUN pip install --upgrade pip
RUN pip install discord.py
RUN pip install pynacl
RUN pip install requests
RUN pip install python-dotenv
RUN pip install boto3
RUN pip install yt-dlp
RUN pip install https://github.com/coletdjnz/yt-dlp-youtube-oauth2/archive/refs/heads/master.zip
# Install FFmpeg
RUN apt-get update
RUN apt-get install -y ffmpeg
RUN rm -rf /var/lib/apt/lists/*

COPY . /bot

CMD python -u main.py
