FROM python:3.10

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel

# We can install the dependencies here manually, or we can use a requirements.txt file, which is better
# RUN pip install pygame
# RUN pip install asyncio
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8888

CMD ["python", "game-server.py"]