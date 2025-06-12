#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Make sure prisma is installed and in PATH
pip install prisma --upgrade

# Generate Prisma client with explicit path
python -m prisma generate

# Output directory contents for debugging
echo "Build directory contents:"
ls -la

echo "Build completed successfully!" 