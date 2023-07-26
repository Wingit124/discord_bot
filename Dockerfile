FROM python:3.11

WORKDIR /bot
RUN pip install --upgrade pip
RUN pip install discord.py
RUN pip install pynacl
RUN pip install requests
COPY . /bot

CMD python main.py
