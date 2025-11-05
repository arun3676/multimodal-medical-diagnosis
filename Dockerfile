# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir ensures we don't store the package cache, keeping the image small
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:create_app()"]
