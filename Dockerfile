FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 morning-alpha

COPY --chown=morning-alpha:morning-alpha . .

USER morning-alpha

EXPOSE 5050

CMD ["python", "-m", "flask", "--app", "src/api.py", "run", "--host=0.0.0.0", "--port=5050"]
