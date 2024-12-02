# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 6000 available to the world outside this container
EXPOSE 6000

# Define environment variable
ENV PORT=6000
ENV ARGO_URL="https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
ENV USER="cels"

# Run app.py when the container launches
CMD ["python3", "app.py"]