# Known Issues and Solutions

This document summarizes the common issues you might encounter when setting up and running this project, along with their solutions.

## Environment Requirements

### Node.js Version Compatibility

- **Issue**: The application may encounter module resolution errors with newer Node.js versions (v18+).
- **Solution**: Use Node.js LTS versions (preferably v16.x or v18.x) for best compatibility. If using nvm:
  ```bash
  nvm install 18
  nvm use 18
  ```

### AWS CDK Deployment Issues

- **Issue**: TypeScript module resolution errors when running CDK commands.
- **Solution**: Install TypeScript dependencies locally and use npx:
  ```bash
  npm install typescript ts-node @types/node
  npx cdk synth
  npx cdk deploy
  ```

- **Issue**: Permission errors with global npm installations.
- **Solution**: Use sudo for global installations or install locally:
  ```bash
  # Global installation with sudo
  sudo npm install -g aws-cdk
  
  # Or local installation alternative
  npm install aws-cdk --save-dev
  npx cdk deploy
  ```

- **Issue**: CloudFront URL (e.g., "dfkwm5303lopi.cloudfront.net") shows "Access Denied" after deployment.
- **Solution**: This can be caused by several factors:
  1. **Frontend not deployed yet**: Build and deploy the frontend files to the UI S3 bucket
     ```bash
     cd frontend-ui
     npm run build
     aws s3 sync build/ s3://YOUR-UI-BUCKET-NAME/
     ```
  2. **CloudFront distribution still deploying**: CloudFront distributions can take 10-15 minutes to fully deploy
  3. **S3 bucket policy issues**: Verify the Origin Access Identity is correctly set up between CloudFront and S3

## Backend Setup

- **Issue**: AWS Bedrock access not enabled in your account.
- **Solution**: Ensure you have enabled AWS Bedrock in your AWS account and have appropriate permissions before deployment.

- **Issue**: CDK bootstrap command fails.
- **Solution**: Check your AWS credentials and ensure you have rights to create resources in the specified account/region.

- **Issue**: S3 bucket naming prefixes may use "genaicapstone-" or "frontend-" prefix.
- **Solution**: As a new user, you can use either prefix - just ensure consistency between your CDK deployment and frontend configuration. The CDK deployment will output the exact bucket names created, which you should then use in your frontend configuration.

## Frontend Setup

- **Issue**: React application fails to start with missing module errors.
- **Solution**: Install specific dependencies that might be missing:
  ```bash
  npm install --save-dev @babel/plugin-proposal-private-property-in-object
  ```

- **Issue**: Frontend cannot connect to backend API.
- **Solution**: Ensure you've correctly updated the config files with your deployed AWS resources.

## Testing Workflow

If you encounter persistent issues with the full stack deployment, you can test components separately:

1. **Test Frontend UI Only**:
   ```bash
   cd frontend-ui
   npm start
   ```
   This will start the UI without backend connectivity.

2. **Test Backend Lambda Functions Individually**:
   Use the test scripts in the `tests/` directory with appropriate parameters.

3. **Test AWS Bedrock Guardrails Directly**:
   Use the AWS Console to test your guardrail configuration.

## Recommended Setup Process

For the smoothest experience:

1. Start with a fresh Node.js LTS installation
2. Follow the setup.sh script instructions
3. Address any issues using this document
4. Proceed with deployment once prerequisites are resolved

If you discover other issues or have additional solutions, please contribute them to this document.
