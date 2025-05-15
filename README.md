# Sample Bedrock Whisper PII Audio Summarizer

This project provides a simple audio upload interface with automatic transcription, PII redaction, and summary generation. It creates a modern web application that handles WAV file uploads, processes them with AWS Bedrock and Whisper AI, and presents summarized content with sensitive information safely redacted.

## Project Structure

- `frontend-ui/` - React frontend application for user interface
- `backend-cdk/` - AWS CDK infrastructure and Lambda backend
- `utils/` - Utility scripts for audio conversion and PII redaction
- `tests/` - Test scripts for verifying functionality

## User Flow

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│                │     │                │     │                │
│  Upload Audio  │────▶│  Processing &  │────▶│    Display     │
│  or Video File │     │   Redaction    │     │    Summary     │
│                │     │                │     │                │
└────────────────┘     └────────────────┘     └────────────────┘
```

1. User uploads an audio/video file through the interface
2. File is processed in AWS backend:
   - Audio extraction (if video)
   - Transcription with Whisper AI
   - PII redaction with Bedrock Guardrails
   - Summary generation
3. Results displayed in UI with redacted content

## File Requirements

### WAV Format Required

The application currently only accepts audio files in WAV format. If you have MP4 or other formats, you'll need to convert them first.

### Converting MP4 to WAV

You can convert MP4 files to WAV format using FFmpeg:

```bash
# Install FFmpeg (if not already installed)
# macOS
brew install ffmpeg

# Ubuntu/Debian
# sudo apt-get install ffmpeg

# Convert MP4 to WAV
ffmpeg -i input-file.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 2 output-file.wav
```

Alternatively, you can use the included utility script:

```bash
python utils/convert_audio.py input-file.mp4 output-file.wav
```

## Features

### Simple User Interface

- **Easy Upload**: Drag and drop or click to upload WAV audio files
- **Real-time Progress**: Monitor transcription and summary generation
- **Clean Results Display**: View the final summary with sensitive information redacted

### Privacy Protection

- **Automatic PII Redaction**: Personally Identifiable Information is automatically detected and redacted
- **Protected Content Types**:
  - Names and personal identities
  - Phone numbers
  - Email addresses
  - Physical addresses
  - Financial information
  - Other sensitive information

- **AWS Bedrock Guardrails**: The application uses [AWS Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) for enterprise-grade PII detection and redaction
  - See the [backend-cdk README](backend-cdk/README.md) for detailed configuration instructions

### AWS Integration

- Uses AWS Bedrock for secure and accurate PII redaction
- Leverages Whisper AI for high-quality audio transcription
- Serverless architecture for scalability and performance

## Complete Deployment Guide

This section provides detailed step-by-step instructions for deploying both the backend and frontend components, and then testing the application.

> **Note**: This repository does not include any sample audio files. You will need to provide your own WAV files for testing and usage.

### Prerequisites

- AWS CLI installed and configured with appropriate permissions
  ```bash
  aws configure
  ```
- Node.js 14.x or later installed
- AWS CDK CLI installed globally
  ```bash
  npm install -g aws-cdk
  ```
- Python 3.8+ for utility scripts

### Step 1: Clone and Prepare the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/sample-bedrock-whisper-pii-audio-summarizer.git

# Navigate to the project directory
cd sample-bedrock-whisper-pii-audio-summarizer
```

### Step 2: Deploy the Backend Infrastructure

```bash
# Navigate to the backend CDK directory
cd backend-cdk

# Install dependencies
npm install

# Bootstrap CDK (only needed once per AWS account/region)
cdk bootstrap aws://$(aws sts get-caller-identity --query 'Account' --output text)/$(aws configure get region)

# Deploy the stack
cdk deploy
```

**Important**: After deployment completes, CDK will output several values. Make note of:
- `ApiEndpoint` - Your API Gateway URL (e.g., `https://xxxxxxxxxxxx.execute-api.us-west-2.amazonaws.com/prod/`)
- `CloudFrontURL` - Your CloudFront distribution URL (e.g., `xxxxxxxxxx.cloudfront.net`)
- The S3 bucket name for frontend hosting (e.g., `frontend-ui-websitebucketXXXXXXXX`)

The backend deployment creates:
- S3 buckets for storing uploads and processed results
- Lambda functions for audio processing and PII redaction
- API Gateway endpoints for handling requests
- IAM roles and policies for secure access
- CloudFront distribution for hosting the frontend

**Configuring the Whisper Endpoint**:

By default, the application uses a SageMaker Whisper endpoint named 'endpoint-quick-start-n6adv' deployed from AWS Bedrock Marketplace. To use your own endpoint:

1. Open `backend-cdk/lib/audio-summarizer-stack.ts`
2. Find the WhisperTranscriptionFunction declaration and update the WHISPER_ENDPOINT value:
   ```typescript
   environment: {
     // Other variables...
     WHISPER_ENDPOINT: 'your-custom-endpoint-name' // Change this line
   }
   ```
3. Save the file before deploying

See the [backend-cdk README](backend-cdk/README.md#whisper-endpoint-configuration) for more details on configuring the Whisper endpoint.

**Configuring the Bedrock Guardrail**:

The application uses AWS Bedrock Guardrails for PII detection and redaction. By default, it uses a pre-configured guardrail, but you can use your own:

1. Open `backend-cdk/lib/audio-summarizer-stack.ts`
2. Find the BedrockSummaryFunction declaration and update the GUARDRAIL_ID value:
   ```typescript
   environment: {
     // Other variables...
     GUARDRAIL_ID: 'arn:aws:bedrock:REGION:ACCOUNT_ID:guardrail/YOUR_GUARDRAIL_ID' // Change this line
   }
   ```
3. Save the file before deploying

See the [backend-cdk README](backend-cdk/README.md#pii-redaction-with-aws-bedrock-guardrails) for more details on creating and configuring Bedrock guardrails.

### Step 3: Configure and Deploy the Frontend

```bash
# Navigate to the frontend directory
cd ../frontend-ui

# Install dependencies
npm install
```

**Update the frontend configuration**:

Edit the `src/config.js` file to point to your API Gateway endpoint:

```javascript
// Replace with your actual API endpoint from the CDK output
export const API_GATEWAY_ENDPOINT = 'https://xxxxxxxxxxxx.execute-api.us-west-2.amazonaws.com/prod';
```

**Build and deploy the frontend**:

```bash
# Build the production version of the app
npm run build

# Upload to the S3 bucket (replace with the actual bucket name from CDK output)
aws s3 sync build/ s3://frontend-ui-websitebucketXXXXXXXX/

# Invalidate CloudFront cache to see the changes immediately
# Replace DISTRIBUTION_ID with your CloudFront distribution ID
aws cloudfront create-invalidation --distribution-id DISTRIBUTION_ID --paths "/*"
```

### Step 4: Verify and Test the Deployment

1. **Access the application**:
   - Open your web browser and navigate to your CloudFront URL
   - Example: `https://xxxxxxxxxx.cloudfront.net`

2. **Test with a WAV file**:
   - Prepare a WAV file for testing, or convert an MP4 to WAV using the conversion instructions
   - Click the upload button in the web interface
   - Select your WAV file and upload it
   - You should see the upload progress followed by processing status

3. **Verify successful processing**:
   - After processing completes (typically 1-3 minutes), you should see:
     - The transcription of the audio file
     - A summary of the content
     - Any PII should be automatically redacted

4. **Check CloudWatch logs if issues occur**:
   ```bash
   # View Lambda function logs (replace FUNCTION_NAME with your actual function name)
   aws logs get-log-events --log-group-name /aws/lambda/FUNCTION_NAME --log-stream-name $(aws logs describe-log-streams --log-group-name /aws/lambda/FUNCTION_NAME --order-by LastEventTime --descending --limit 1 --query 'logStreams[0].logStreamName' --output text)
   ```

### Troubleshooting Deployment Issues

- **CloudFormation Errors**: Check the AWS CloudFormation console for stack deployment errors
- **S3 Upload Issues**: Verify you have the correct permissions and bucket name
- **Frontend Not Updated**: Try a hard refresh (Ctrl+Shift+R) or check CloudFront invalidation status
- **Lambda Function Failures**: Check CloudWatch logs for error messages
- **API Gateway Configuration**: Ensure CORS settings are properly configured

## Testing the Deployed Application

1. **Access the Application**
   - Open your browser and navigate to the CloudFront URL from the deployment outputs
   - Example: `https://xxxxxxxxxx.cloudfront.net`

2. **Upload a WAV File**
   - Click the upload button or drag and drop a WAV file into the upload area
   - Files must be in WAV format (see conversion instructions above if needed)
   - For testing, use a short audio clip (30-60 seconds) containing speech

3. **Monitor Processing**
   - The application will show a progress indicator while your file is being processed
   - This includes uploading, transcription, PII redaction, and summary generation
   - Processing typically takes 1-3 minutes depending on the file size

4. **View Results**
   - Once processing is complete, the summary will be displayed
   - All sensitive information will be automatically redacted
   - You should see the transcribed text and a summary of the content

## Troubleshooting

- **File Not Uploading**: Ensure your file is in WAV format and under the size limit (100MB)
- **Processing Errors**: Check the browser console for error messages
- **CORS Issues**: If experiencing CORS errors, make sure:
  - The Lambda function returns the correct CORS headers
  - API Gateway has CORS enabled
  - CloudFront distribution is properly configured
  - Try running `cdk deploy` again to update the configuration
- **Missing Summary**: Processing large files may take several minutes. If no summary appears after 5 minutes, refresh the page and check the summary status again
- **API Gateway Errors**: Verify that your API Gateway endpoint is correctly set in the frontend config.js file
- **Deployment Failures**: Check CloudFormation in the AWS Console for detailed error messages

For detailed deployment instructions and architecture information, see:
- [Frontend README](frontend-ui/README.md)
- [Backend CDK README](backend-cdk/README.md)

## Development

### Local Development

1. Start the frontend:
```bash
cd frontend-ui
npm install
npm start
```

2. The frontend will automatically use:
- Local API (http://localhost:3000) for development
- Deployed API endpoint for production

## Complementary Tools

### Utility Scripts

The `utils/` directory contains supporting scripts that complement the UI functionality:

1. **Audio Conversion Utility** (`utils/convert_audio.py`):
   ```bash
   # Convert an MP4 file to WAV format
   python utils/convert_audio.py --input video.mp4 --output audio.wav
   
   # Upload converted audio to S3
   python utils/convert_audio.py --input audio.wav --upload --bucket YOUR_BUCKET_NAME
   ```
   This utility helps prepare audio files for processing if your source files need conversion.

2. **PII Redaction Utility** (`utils/pii_redaction_utility.py`):
   ```bash
   # Test PII redaction on a sample text
   python utils/pii_redaction_utility.py --text "My name is John Doe and my phone is 555-123-4567"
   
   # Process a transcript file
   python utils/pii_redaction_utility.py --file transcript.txt --output redacted.txt
   ```
   This allows you to test PII redaction separately from the main UI flow and verify redaction patterns.

### Test Scripts

The `tests/` directory contains scripts for testing different components of the system:

1. **Bedrock Guardrail Testing** (`tests/test_lambda_guardrail.py`):
   ```bash
   # Test the guardrail with example text
   python tests/test_lambda_guardrail.py --source OUTPUT
   ```
   Validates that your Bedrock guardrail is properly configured for PII redaction.

2. **Phone Redaction Testing** (`tests/test_phone_redaction.py`):
   ```bash
   # Test phone number redaction with various formats
   python tests/test_phone_redaction.py \
     --guardrail-id YOUR_GUARDRAIL_ARN \
     --region us-east-1 \
     --version DRAFT
   ```
   Ensures that all phone number formats are properly redacted using your configured Bedrock guardrail.

3. **Step Function Testing** (`tests/test_step_function.py`):
   ```bash
   # Test the AWS Step Function execution with your own audio file
   python tests/test_step_function.py \
     --file YOUR_AUDIO_FILE.wav \
     --region us-west-1 \
     --state-machine VoiceProcessingStateMachine \
     --upload-bucket YOUR_UPLOAD_BUCKET_NAME
   ```
   Tests the entire backend processing workflow independent of the UI.
   
   > **Important**: You must provide your own audio file for testing and specify your own AWS resources. No sample files or hardcoded AWS resource identifiers are included in this repository.

### Integration with UI Flow

These tools complement the UI in the following ways:

- **Pre-processing**: Use the conversion utility to prepare files before upload
- **Quality Assurance**: Verify PII redaction before deploying to production
- **Troubleshooting**: Isolate and test specific components when issues occur
- **Batch Processing**: Process multiple files outside the UI for bulk operations

## Quick Start Guide

Follow these steps to get the application running quickly:

### Prerequisites

- Node.js 18.x or later
- AWS CLI installed and configured
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- TypeScript (`npm install -g typescript`)
- Python 3.8+ for utility and test scripts
- AWS Account with permissions to create resources
- AWS Bedrock access enabled in your account

### First-Time Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/sample-bedrock-whisper-pii-audio-summarizer.git
   cd sample-bedrock-whisper-pii-audio-summarizer
   ```

2. **Configure AWS Credentials**

   Ensure your AWS credentials are properly configured:
   ```bash
   aws configure
   ```
   Enter your AWS Access Key ID, Secret Access Key, default region (e.g., us-west-1), and output format (json).

3. **Create Required Environment Files**

   For the frontend:
   ```bash
   # Create a .env file in the frontend-ui directory
   cat > frontend-ui/.env << EOL
   REACT_APP_API_ENDPOINT=http://localhost:3000/dev
   REACT_APP_REGION=us-west-1
   REACT_APP_UPLOAD_BUCKET=frontend-uploads-dev
   REACT_APP_SUMMARIES_BUCKET=frontend-summaries-dev
   EOL
   ```
   
   > Note: After deploying the backend, you will replace these values with the actual AWS resources.

4. **Create AWS Bedrock Guardrail**

   - Follow the [AWS Bedrock Guardrail creation instructions](backend-cdk/README.md#creating-bedrock-guardrails) to set up PII redaction.

### Deploy Backend

```bash
# Navigate to backend directory
cd backend-cdk

# Install dependencies
npm install

# Install TypeScript dependencies locally to avoid module resolution issues
npm install typescript ts-node @types/node

# Bootstrap CDK in your AWS account
cdk bootstrap aws://$(aws sts get-caller-identity --query 'Account' --output text)/$(aws configure get region)

# Synthesize the template to see what resources will be created (optional)
npx cdk synth

# Deploy the stack
npx cdk deploy
```

> **Note on S3 bucket naming**: The CDK code may use either "genaicapstone-" or "frontend-" as bucket prefixes. As a new user, you can use either naming convention - just make sure your frontend configuration matches the bucket names output from the CDK deployment.

After deployment completes, note the following outputs:
- API Gateway URL
- CloudFront Distribution URL
- S3 bucket names

### Configure and Run Frontend

```bash
# Navigate to frontend directory
cd ../frontend-ui

# Install dependencies
npm install

# Update .env file with the values from CDK output
# Edit frontend-ui/.env with your actual endpoints

# Start the frontend
npm start
```

### Verify Installation

1. Open your browser to `http://localhost:3000`
2. Upload an audio file (.mp3, .wav, .mp4)
3. The file should be processed and a summary displayed

### Troubleshooting

- **CDK Deployment Errors**: Ensure you have proper AWS permissions and that AWS Bedrock is enabled in your account.
- **Frontend Connection Issues**: Check that the API Gateway URL in your .env file matches the CDK output.
- **Processing Errors**: Review CloudWatch logs for the Lambda functions to identify issues.

Refer to the [backend README](backend-cdk/README.md) and [frontend README](frontend-ui/README.md) for more detailed configuration options.
