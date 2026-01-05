#!/bin/bash

# HealNet Setup Script
# Automates the setup process for the backend

echo "=================================="
echo "🏥 HealNet Backend Setup"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/Scripts/activate 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Virtual environment activated"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please update it with your API keys."
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
    echo "   - Twilio Account SID & Auth Token"
    echo "   - Gemini API Key"
    echo "   - Google Maps API Key"
    echo "   - Google Cloud Service Account JSON path"
else
    echo "✅ .env file already exists"
fi

echo ""

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from app import init_db; init_db()"

if [ $? -eq 0 ]; then
    echo "✅ Database initialized"
else
    echo "⚠️  Database may already be initialized"
fi

echo ""

# Check if ngrok is installed
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is installed"
else
    echo "⚠️  ngrok is not installed. Install it from https://ngrok.com/download"
    echo "   You'll need ngrok to expose your local server for Twilio webhooks."
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Update .env file with your API keys"
echo "2. Start the FastAPI server:"
echo "   python run.py"
echo ""
echo "3. In another terminal, start ngrok:"
echo "   ngrok http 8000"
echo ""
echo "4. Copy the ngrok HTTPS URL and set it as your Twilio webhook:"
echo "   https://your-ngrok-url.ngrok.io/api/v1/whatsapp"
echo ""
echo "5. Send a WhatsApp message to test!"
echo ""
echo "📚 For detailed instructions, see README.md"
echo ""