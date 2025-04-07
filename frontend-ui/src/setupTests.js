// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock the config file
jest.mock('./config', () => ({
  API_ENDPOINT: 'https://test-api.example.com/Prod'
}));

// Mock MUI components that might cause issues
jest.mock('@mui/material', () => ({
  ...jest.requireActual('@mui/material'),
  CircularProgress: () => 'CircularProgress',
  LinearProgress: () => 'LinearProgress'
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Upload: () => 'UploadIcon'
}));

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});
