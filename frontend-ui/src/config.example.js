/**
 * Example configuration file for frontend
 * Copy this file to config.js and update the values with your actual AWS resources
 */

const config = {
  // API Gateway endpoint from CDK output
  apiEndpoint: 'https://your-api-id.execute-api.us-west-1.amazonaws.com/prod',
  
  // AWS region where your resources are deployed
  region: 'us-west-1',
  
  // S3 bucket names from CDK output
  uploadBucket: 'frontend-uploads-dev',
  summariesBucket: 'frontend-summaries-dev',
  
  // Maximum file size in MB
  maxFileSizeMB: 100,
  
  // Supported file formats
  supportedFormats: ['.mp3', '.wav', '.mp4', '.m4a', '.mpeg', '.mpga', '.webm'],
};

export default config;
