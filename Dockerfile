FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV FLASK_APP=input.py
ENV FLASK_DEBUG=0
EXPOSE 5000
CMD ["python", "input.py"]
