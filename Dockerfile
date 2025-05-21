# Bước 1: Chọn image Python chính thức từ Docker Hub
FROM python:3.9-slim
# Bước 2: Cài đặt các dependencies cần thiết cho psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# Bước 2: Thiết lập thư mục làm việc trong container
WORKDIR /app

# Bước 3: Sao chép file requirements.txt vào container
COPY requirements.txt .

# Bước 4: Cài đặt các thư viện từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Bước 5: Sao chép toàn bộ mã nguồn ứng dụng vào container
COPY . .

# Bước 6: Mở cổng 8000 cho ứng dụng FastAPI
EXPOSE 8000

# Bước 7: Chạy ứng dụng FastAPI bằng Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]