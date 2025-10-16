# Use a standard Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the wrapper files into the container
COPY ./a2a_wrapper/ /app/

# Copy your agent's client logic into the container so it can be called
# You may need to adjust this path depending on what files are needed
COPY ./client/ /app/client/

# Install Python dependencies
# You'll need to add your agent's dependencies to requirements.txt
RUN pip install fastapi "uvicorn[standard]"
# RUN pip install -r client/requirements.txt # Uncomment if you have a requirements file

# Expose the port the server will run on
EXPOSE 8001

# Command to run the A2A wrapper server
CMD ["python", "main.py"]