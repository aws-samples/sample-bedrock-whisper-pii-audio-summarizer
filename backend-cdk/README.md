# Bedrock Whisper PII Audio Summarizer CDK Infrastructure

This project contains the AWS CDK infrastructure code for the Audio Summarizer application. It deploys a complete serverless stack including Lambda functions, API Gateway, S3 buckets, and CloudFront distribution.

## Infrastructure Components

- **S3 Buckets**:
  - `frontend-uploads-{env}`: For storing uploaded audio/video files
  - `frontend-summaries-{env}`: For storing generated summaries
  - `frontend-ui-{env}`: For hosting the React frontend

- **Lambda Functions**:
  - `whisper-transcription.py`: Transcribes audio using Whisper model
  - `bedrock-summary.py`: Generates summaries with PII redaction using Bedrock Guardrails

- **API Gateway**: RESTful API with endpoints:
  - POST `/get-upload-url`: Generate presigned URLs for file uploads
  - GET `/check-summary/{uuid}`: Check summary generation status
  - GET `/fetch-summary/{filename}`: Retrieve generated summaries

- **CloudFront**: Distribution for serving the UI with proper caching and HTTPS

## Deployment Instructions

### Pre-Deployment Preparation

1. Install dependencies:
```bash
npm install

# Install TypeScript and ts-node locally if you encounter module issues
npm install typescript ts-node @types/node
```

2. Important: Check bucket name prefixes
   
   The repository has been renamed from "genaicapstone" to "sample-bedrock-whisper-pii-audio-summarizer". You may need to modify S3 bucket prefix references in the CDK code:
   
   * Search for "genaicapstone-" in `.ts` files and replace with "frontend-"
   * Common locations where this might need to be updated:
     * Stack definition file in `lib/` directory
     * Resource definition files related to S3 buckets

   Example of what to look for in bucket definitions:
   ```typescript
   // BEFORE:
   new s3.Bucket(this, 'UploadsBucket', {
     bucketName: `genaicapstone-uploads-${props.uniqueId}`,
     // ...
   });
   
   // AFTER:
   new s3.Bucket(this, 'UploadsBucket', {
     bucketName: `frontend-uploads-${props.uniqueId}`,
     // ...
   });
   ```

3. Bootstrap CDK (first time only):
```bash
# Use this bootstrap command format with your account and region
cdk bootstrap aws://$(aws sts get-caller-identity --query 'Account' --output text)/$(aws configure get region)
```

4. Deploy the stack:
```bash
# If you encounter TypeScript errors, try using npx
npx cdk deploy
```

## Troubleshooting

### Common CDK Deployment Issues

1. **Module Not Found Errors**:
   ```
   Error: Cannot find module './util'
   ```
   **Solution**: Install TypeScript and ts-node locally:
   ```bash
   npm install typescript ts-node @types/node
   ```

2. **AWS Credentials Issues**:
   ```
   Unable to resolve AWS account to use
   ```
   **Solution**: Configure AWS credentials:
   ```bash
   aws configure
   ```

3. **TypeScript Version Conflicts**:
   **Solution**: Use npx to run CDK with local dependencies:
   ```bash
   npx cdk deploy
   ```

4. **Permission Errors**:
   If you see permission errors during deployment, ensure your AWS account has the necessary permissions for creating resources.

4. **CDK will automatically display outputs in the terminal** after deployment completes:
   ```
   ✅ YourStackName
   
   Outputs:
   YourStackName.ApiEndpoint = https://xxxxxxxxxxxx.execute-api.region.amazonaws.com/prod/
   YourStackName.CloudFrontURL = d1234abcdef.cloudfront.net
   ```

5. Copy these output values directly from your terminal and use them in your frontend configuration:
   ```javascript
   // In frontend-ui/src/config.js
   export const API_ENDPOINT = 'https://xxxxxxxxxxxx.execute-api.region.amazonaws.com/prod/'; // The ApiEndpoint value from CDK output
   ```

6. Alternative: If you need to retrieve these values later, you can use the AWS CLI:
   ```bash
   # Get API Gateway endpoint
   API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name YOUR_STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)
   echo $API_ENDPOINT
   
   # Get CloudFront URL
   CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name YOUR_STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" --output text)
   echo $CLOUDFRONT_URL
   ```

## Configuration

- The stack uses a `UniqueId` parameter (default: 'dev1') to namespace resources
- CORS is configured to allow localhost and CloudFront origins
- Lambda function timeout is set to 900 seconds
- CloudFront is configured for Single Page Application hosting

## Whisper Endpoint Configuration

The application uses a SageMaker Whisper endpoint deployed from the AWS Bedrock Marketplace for audio transcription. The endpoint name can be configured in two ways:

1. **Environment Variable**: The Lambda function looks for a `WHISPER_ENDPOINT` environment variable
   - This is defined in the CDK stack (`audio-summarizer-stack.ts`)
   - Modify this value before deployment to use your own SageMaker Whisper endpoint

```typescript
// In audio-summarizer-stack.ts
environment: {
  // Other environment variables...
  WHISPER_ENDPOINT: 'your-whisper-endpoint-name' // Change this to your endpoint name
}
```

2. **Fallback Value**: If the environment variable is not set, it will use the default value ('endpoint-quick-start-n6adv')

When creating your own SageMaker Whisper endpoint, make sure it:
- Is deployed from AWS Bedrock Marketplace or other sources with OpenAI Whisper compatibility
- Is deployed in the 'us-east-1' region (or update the region in the Lambda code)
- Uses a model compatible with the Whisper API format
- Has the correct IAM permissions to be invoked by the Lambda function

## Security Features

### PII Redaction with AWS Bedrock Guardrails

The infrastructure includes security features to protect sensitive information in processed audio transcriptions:

- **Bedrock Guardrail Integration**: The `bedrock-summary.py` Lambda function utilizes AWS Bedrock Guardrails to automatically detect and redact sensitive information.

- **IAM Permissions**: The Lambda execution role includes permissions to call the Bedrock Guardrail API:
  ```json
  {
    "Action": "bedrock:ApplyGuardrail",
    "Resource": "arn:aws:bedrock:{REGION}:{ACCOUNT_ID}:guardrail/{GUARDRAIL_ID}",
    "Effect": "Allow"
  }
  ```

- **Configuration**: 
  - Guardrail ID is configured in the Lambda function code
  - You must create your own Guardrail in the AWS Bedrock console and update the ARN in your Lambda
  - API Parameters: Uses `source="OUTPUT"` for proper redaction flow

- **Creating a Bedrock Guardrail**:
  1. Follow the official [AWS Documentation for Creating Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-create.html)
  2. For PII detection and redaction, use the [Bedrock Guardrails for PII](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails-pii.html) guide
  3. Configure your guardrail with the following key settings:
     - Enable PII detection and handling
     - Set PII action to "Redact"
     - Add all relevant PII types (names, addresses, phone numbers, etc.)
     - Deploy the guardrail and note the ARN
  4. Update the Lambda function with your guardrail ARN
  
- **Redaction Coverage**: The guardrail is configured to redact various PII types including:
  - Names and identities
  - Phone numbers
  - Email addresses
  - Physical addresses
  - Financial information
  - Other sensitive personal information

## Useful Commands

* `npm run build`   Compile TypeScript to JavaScript
* `npm run watch`   Watch for changes and compile
* `npm run test`    Run the jest unit tests
* `cdk deploy`      Deploy this stack to AWS
* `cdk diff`        Compare deployed stack with current state
* `cdk synth`       Emit the synthesized CloudFormation template
