FROM debian:bullseye-slim

WORKDIR /apib
RUN apt-get update
RUN apt-get install -y python3 python3-pip gnupg curl
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-6.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/mongodb-keyring.gpg] https://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
RUN apt-get update && apt-get install -y mongodb-mongosh mongodb-org-tools

COPY requirements.txt /apib/requirements.txt
RUN pip3 install --no-cache-dir -r /apib/requirements.txt

RUN mkdir ApiB
COPY backend/ /apib/ApiB/backend
COPY static/ /apib/ApiB/static
COPY templates/ /apib/ApiB/templates
COPY API.py /apib/ApiB/API.py
CMD ["sh", "-c", "mongosh mongodb://admin:pass@mongodb:27017 /apib/ApiB/backend/mongo-init.js && python3 /apib/ApiB/API.py"]