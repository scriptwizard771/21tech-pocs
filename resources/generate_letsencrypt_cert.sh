#!/bin/bash

# Let's Encrypt SSL Certificate Generation Script
# Usage: ./generate_letsencrypt_cert.sh your-domain.com

DOMAIN=${1:-54.219.76.120}
EMAIL="admin@example.com"  # Change this to your email

echo "Generating Let's Encrypt SSL certificate for domain: $DOMAIN"

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot
fi

# Generate certificate (standalone mode - requires port 80 to be free)
sudo certbot certonly --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# Copy certificates to Django project
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Copying certificates to Django project..."
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./cert.pem
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./key.pem
    sudo chown $(whoami):$(whoami) ./cert.pem ./key.pem
    echo "SSL certificates generated successfully!"
else
    echo "Certificate generation failed!"
    exit 1
fi 