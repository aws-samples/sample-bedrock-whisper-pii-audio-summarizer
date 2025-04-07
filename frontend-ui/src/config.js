// Get the current hostname
const hostname = window.location.hostname;

// Determine if we're running in production (CloudFront) or locally
const isProduction = !hostname.includes('localhost') && !hostname.includes('127.0.0.1');

// API endpoints configuration
export const API_GATEWAY_ENDPOINT = isProduction
  ? 'https://xxxxxxxxxxxx.execute-api.us-west-2.amazonaws.com/prod'  // Replace with your actual API Gateway endpoint
  : 'http://localhost:3000';  // Local development

// CloudFront URL for production
export const CLOUDFRONT_URL = 'https://xxxxxxxxxx.cloudfront.net';  // Replace with your actual CloudFront URL

// Use API Gateway for upload URL and CloudFront for summary endpoints
export const GET_UPLOAD_URL_ENDPOINT = API_GATEWAY_ENDPOINT;  // Direct to API Gateway
export const CHECK_SUMMARY_ENDPOINT = isProduction ? CLOUDFRONT_URL : API_GATEWAY_ENDPOINT;  // Through CloudFront in production

// Log the current environment for debugging
console.log(`Running in ${isProduction ? 'production' : 'development'} mode`);
console.log(`Using Upload URL endpoint: ${GET_UPLOAD_URL_ENDPOINT}`);
console.log(`Using Check Summary endpoint: ${CHECK_SUMMARY_ENDPOINT}`);
