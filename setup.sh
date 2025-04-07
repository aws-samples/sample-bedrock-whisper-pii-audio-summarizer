#!/bin/bash
# Setup script for sample-bedrock-whisper-pii-audio-summarizer
# This script helps first-time users set up the application correctly

echo "=== Sample Bedrock Whisper PII Audio Summarizer Setup ==="
echo "This script will help you set up your environment for running this application."

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first: https://aws.amazon.com/cli/"
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18.x or later: https://nodejs.org/"
    exit 1
fi

# Check for CDK
if ! command -v cdk &> /dev/null; then
    echo "⚠️ AWS CDK is not installed. Installing it globally..."
    npm install -g aws-cdk
fi

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

echo "✅ All prerequisites checked."

# AWS Configuration Check
echo ""
echo "=== AWS Configuration ==="
echo "Checking your AWS configuration..."

if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️ AWS credentials not configured or invalid."
    echo "Please run 'aws configure' and enter your AWS credentials:"
    aws configure
else
    echo "✅ AWS credentials are configured."
    ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
    REGION=$(aws configure get region)
    echo "   Account ID: $ACCOUNT_ID"
    echo "   Region: $REGION"
fi

# Install backend dependencies
echo ""
echo "=== Setting up backend ==="
echo "Installing CDK backend dependencies..."
cd backend-cdk
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies."
    exit 1
fi
echo "✅ Backend dependencies installed."

# Install frontend dependencies
echo ""
echo "=== Setting up frontend ==="
echo "Installing React frontend dependencies..."
cd ../frontend-ui
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies."
    exit 1
fi
echo "✅ Frontend dependencies installed."

# Check if frontend config exists
if [ ! -f "src/config.js" ] && [ -f "src/config.example.js" ]; then
    echo "Creating frontend configuration file from example..."
    cp src/config.example.js src/config.js
    echo "✅ Created frontend configuration file. Please edit src/config.js with your actual values after deployment."
fi

# Create example .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating example .env file for frontend..."
    cat > .env << EOL
REACT_APP_API_ENDPOINT=http://localhost:3000/dev
REACT_APP_REGION=${REGION:-us-west-1}
REACT_APP_UPLOAD_BUCKET=frontend-uploads-dev
REACT_APP_SUMMARIES_BUCKET=frontend-summaries-dev
EOL
    echo "✅ Created example .env file. Please update with actual values after backend deployment."
fi

# Back to the root directory
cd ..

echo ""
echo "=== Setup Complete ==="
echo ""
echo "🚀 Next steps:"
echo "1. Create an AWS Bedrock guardrail following instructions in backend-cdk/README.md"
echo "2. Deploy the backend stack:"
echo "   cd backend-cdk && cdk deploy"
echo "3. Update the frontend configuration with values from the CDK output"
echo "4. Start the frontend:"
echo "   cd frontend-ui && npm start"
echo ""
echo "See README.md for detailed instructions."
