# Start with a base image known to be compatible with AMD64
FROM ubuntu:latest

# Install necessary packages
RUN apt-get update && apt-get install -y \
    wget \
    openjdk-11-jre-headless \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /zap

# Replace the URL below with the actual download link for ZAP
RUN wget -q https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2.14.0_aarch64.dmg -O zap.tar.gz \
    && tar -xzf zap.tar.gz --strip-components=1 \
    && rm zap.tar.gz

# Expose the port ZAP will run on
EXPOSE 8080

# Define the entry point
ENTRYPOINT ["./zap.sh"]

# Default command to run on startup
CMD ["-daemon", "-host", "0.0.0.0", "-port", "8080", "-config", "api.disablekey=true"]
