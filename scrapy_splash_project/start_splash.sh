#!/bin/bash

echo "Starting Splash container..."
docker-compose up -d

echo ""
echo "Waiting for Splash to be ready..."
sleep 3

echo ""
echo "Testing Splash connection..."
curl -s http://localhost:8050 > /dev/null

if [ $? -eq 0 ]; then
    echo "✓ Splash is running at http://localhost:8050"
    echo ""
    echo "You can now run spiders:"
    echo "  scrapy crawl example -o quotes.json"
    echo "  scrapy crawl advanced -o advanced.json"
    echo ""
    echo "To stop Splash: docker-compose down"
else
    echo "✗ Failed to connect to Splash"
    echo "Check logs with: docker-compose logs splash"
fi
