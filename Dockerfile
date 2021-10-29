FROM python:3.9.7 as builder
COPY requeriments.txt .

RUN pip install --user -r requeriments.txt

FROM python:3.9.7-slim
WORKDIR /

COPY --from=builder /root/.local /root/.local

COPY . .

ENTRYPOINT [ "python", "explicit.py" ]