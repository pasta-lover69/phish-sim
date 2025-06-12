#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Generate Prisma client
prisma generate

echo "Build completed successfully!" 