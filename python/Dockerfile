FROM python:3.10-alpine

WORKDIR /app

RUN addgroup -S mercari && adduser -S trainee -G mercari

RUN mkdir -p /db && chown -R trainee:mercari /db
ENV PATH="/usr/local/bin:$PATH"


# traineeユーザー用のPATHを追加
ENV PATH="/home/trainee/.local/bin:$PATH"


COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/

RUN chown -R trainee:mercari /app

USER trainee


#CMD ["python", "-V"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]

