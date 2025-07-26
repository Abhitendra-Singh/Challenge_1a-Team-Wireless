# Stage 1: Build the application environment
# Use a specific, stable Python version on linux/amd64 architecture
FROM --platform=linux/amd64 python:3.10-slim-bullseye AS builder

# Set the working directory
WORKDIR /app

# Install dependencies
# Using --no-cache-dir keeps the image size smaller
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and the trained model
COPY src/ src/
COPY models/ models/
COPY process_pdfs.py .

# Stage 2: Create the final, clean image
FROM --platform=linux/amd64 python:3.10-slim-bullseye

WORKDIR /app

# Copy the installed dependencies and application from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /app/src/ /app/src/
COPY --from=builder /app/models/ /app/models/
COPY --from=builder /app/process_pdfs.py .

# Set the command to run when the container starts
CMD ["python", "process_pdfs.py"]
