# build stage
FROM python:3.10-slim As builder
WORKDIR /myblog
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# final stage
FROM python:3.10-slim
WORKDIR /myblog
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
EXPOSE 5000
CMD ["sh", "-c", "python init_db.py && python app.py"]



