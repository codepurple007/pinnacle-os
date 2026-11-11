FROM python:3.12-slim

WORKDIR /srv
ENV PYTHONPATH=/srv/packages/google:/srv/apps/api
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY packages/google /srv/packages/google
COPY apps/api/requirements.txt /srv/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /srv/apps/api/requirements.txt \
    && pip install --no-cache-dir /srv/packages/google

COPY apps/api /srv/apps/api
WORKDIR /srv/apps/api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
