# Audio/Video Summarizer Frontend

React-based frontend application for uploading audio/video files and displaying their AI-generated summaries.

## Features

- Upload audio and video files
- Real-time upload progress tracking
- Automatic summary generation
- Summary display interface
- Material-UI components for modern design
- Error handling and user feedback

## Quick Start

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The application will automatically open in your browser at http://localhost:3000.

## Project Structure

```
src/
├── App.js                    # Main application component
├── AudioUploadComponent.js   # File upload and processing component
├── SummaryDisplayComponent.js# Summary display interface
├── TextInputComponent.js     # Text input interface
├── config.js                # API configuration
└── styles/                  # Component-specific CSS files
```

## Components

### AudioUploadComponent
- Handles file selection and upload
- Manages upload progress state
- Communicates with backend API
- Polls for summary completion

### SummaryDisplayComponent
- Displays generated summaries
- Formats and styles summary content
- Handles summary visibility state

### TextInputComponent
- Provides text input interface
- Manages input validation
- Handles text submission

## Configuration

The application is pre-configured to connect to the AWS Lambda backend. The API endpoint is automatically set in `src/config.js`.

## Error Handling

The application includes comprehensive error handling for:
- File type validation
- Upload failures
- Network issues
- API errors
- Summary generation failures

## Testing

Run the test suite:
```bash
npm test
```

Tests cover:
- Component rendering
- File upload functionality
- API interactions
- Error scenarios

## Build

Create a production build:
```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Troubleshooting

### Common Frontend Issues

1. **Module Not Found Errors**:
   ```
   Error: Cannot find module '@babel/plugin-proposal-private-property-in-object'
   ```
   **Solution**: Install missing dependencies explicitly:
   ```bash
   npm install --save-dev @babel/plugin-proposal-private-property-in-object
   ```

2. **Environment Configuration Issues**:
   If the application fails to connect to backend resources, check:
   - Your `.env` file exists and has correct values
   - Your `src/config.js` file is properly configured with AWS resources
   - CORS is enabled on your API Gateway

3. **Node Version Conflicts**:
   The application works best with Node.js LTS versions (14.x, 16.x, 18.x).
   If you have issues with newer Node versions, try using nvm to switch:
   ```bash
   nvm use 18
   npm install
   npm start
   ```

4. **API Connection Issues**:
   If you see errors connecting to the API Gateway, ensure:
   - The API is deployed and active
   - The endpoint URL in your config has the correct stage (e.g., `/prod`)
   - Your AWS region matches between frontend config and backend deployment

## Development

The application uses:
- React 18 for UI components
- Material-UI for styling
- Axios for API requests
- Jest for testing

All necessary development dependencies are included in package.json.
