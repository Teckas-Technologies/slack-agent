#!/bin/bash
# Generate self-signed SSL certificate for development/VM deployment
# For production, use Let's Encrypt or a trusted CA certificate

CERT_DIR="./ssl_certs"
DAYS_VALID=365

echo "Generating self-signed SSL certificate..."

# Create directory for certificates
mkdir -p "$CERT_DIR"

# Generate private key and certificate
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days $DAYS_VALID \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set proper permissions
chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo "✅ SSL certificates generated successfully!"
echo "   Certificate: $CERT_DIR/cert.pem"
echo "   Private Key: $CERT_DIR/key.pem"
echo "   Valid for: $DAYS_VALID days"
echo ""
echo "⚠️  NOTE: This is a SELF-SIGNED certificate for development/testing."
echo "   Browsers will show security warnings."
echo "   For production, use Let's Encrypt or a trusted CA certificate."
