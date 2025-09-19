#!/bin/bash

# Setup script for Healthcare Cost Navigator environment variables

echo "Setting up environment variables for Healthcare Cost Navigator..."

# Copy the example environment file
if [ ! -f .env ]; then
    cp env.example .env
    echo "✅ Created .env file from env.example"
else
    echo "⚠️  .env file already exists, skipping creation"
fi

echo ""
echo "📝 Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run 'make dev-server' to start the development server"
echo "3. Run 'make download-sample-ny-data' to download sample data"
echo "4. Run 'make run-etl' to load data into the database"
echo ""
echo "🔑 To get an OpenAI API key:"
echo "   Visit: https://platform.openai.com/api-keys"
echo ""
echo "🚀 Happy coding!"
