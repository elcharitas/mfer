FROM python:3.9-slim-buster

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on (dynamically from ENV)
EXPOSE ${PORT}

# Run the application using Gunicorn, reading the port from environment variable
CMD ["gunicorn", "app:app"]