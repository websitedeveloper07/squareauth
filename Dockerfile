# Use the official Python slim image for a smaller footprint
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Expose port 8000 (Render's default port)
EXPOSE 8000

# Set environment variables for Flask and Gunicorn
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
