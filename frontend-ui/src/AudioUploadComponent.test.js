import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AudioUploadComponent from './AudioUploadComponent';

// Create mock axios module
const mockAxios = {
  post: jest.fn(),
  put: jest.fn(),
  get: jest.fn()
};

// Mock the entire axios module
jest.mock('axios', () => mockAxios);

// Mock axios
jest.mock('axios');

// Mock UUID generation to have predictable IDs in tests
jest.mock('uuid', () => ({
  v4: () => 'test-uuid'
}));

describe('AudioUploadComponent', () => {
  const mockFile = new File(['test file content'], 'test-video.mp4', { type: 'video/mp4' });
  const mockPresignedUrl = 'https://test-bucket.s3.amazonaws.com/presigned-url';
  
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
  });

  it('handles the complete upload flow successfully', async () => {
    // Mock the pre-signed URL request
    axios.post.mockResolvedValueOnce({
      data: {
        uploadUrl: mockPresignedUrl,
        key: 'test-uuid_test-video.mp4'
      }
    });

    // Mock the direct S3 upload
    axios.put.mockResolvedValueOnce({});

    // Mock the summary polling requests
    axios.get
      // First check returns no summary
      .mockResolvedValueOnce({ data: { exists: false } })
      // Second check finds the summary
      .mockResolvedValueOnce({ data: { exists: true, key: 'summary-123' } })
      // Get summary content
      .mockResolvedValueOnce({ data: { content: 'Test summary content' } });

    // Render the component
    render(<AudioUploadComponent />);

    // Verify initial state
    expect(screen.getByText('Upload and Process')).toBeInTheDocument();
    expect(screen.queryByText(/Uploading\.\.\./)).not.toBeInTheDocument();

    // Simulate file selection
    const fileInput = screen.getByRole('textbox', { type: 'file' });
    fireEvent.change(fileInput, { target: { files: [mockFile] } });

    // Click upload button
    const uploadButton = screen.getByText('Upload and Process');
    fireEvent.click(uploadButton);

    // Verify loading state
    await waitFor(() => {
      expect(screen.getByText(/Uploading\.\.\./)).toBeInTheDocument();
    });

    // Verify pre-signed URL request
    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/get-upload-url'),
      {
        fileName: 'test-video.mp4',
        fileType: 'video/mp4'
      },
      expect.any(Object)
    );

    // Verify S3 upload request
    await waitFor(() => {
      expect(axios.put).toHaveBeenCalledWith(
        mockPresignedUrl,
        mockFile,
        expect.any(Object)
      );
    });

    // Verify summary polling started
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/check-summary/test-uuid')
      );
    });

    // Verify summary fetch
    await waitFor(() => {
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/fetch-summary/summary-123')
      );
    });

    // Verify summary display
    await waitFor(() => {
      expect(screen.getByText('Display Summarization')).toBeInTheDocument();
    });

    // Click to display summary
    const displayButton = screen.getByText('Display Summarization');
    fireEvent.click(displayButton);

    // Verify summary content
    await waitFor(() => {
      expect(screen.getByText('Test summary content')).toBeInTheDocument();
    });
  });

  it('handles upload errors appropriately', async () => {
    // Mock pre-signed URL request failure
    axios.post.mockRejectedValueOnce({
      response: {
        data: { error: 'Failed to generate upload URL' }
      }
    });

    // Render the component
    render(<AudioUploadComponent />);

    // Simulate file selection
    const fileInput = screen.getByRole('textbox', { type: 'file' });
    fireEvent.change(fileInput, { target: { files: [mockFile] } });

    // Click upload button
    const uploadButton = screen.getByText('Upload and Process');
    fireEvent.click(uploadButton);

    // Verify error state
    await waitFor(() => {
      expect(screen.getByText('Failed to generate upload URL')).toBeInTheDocument();
    });
  });

  it('handles S3 upload errors appropriately', async () => {
    // Mock successful pre-signed URL request
    axios.post.mockResolvedValueOnce({
      data: {
        uploadUrl: mockPresignedUrl,
        key: 'test-uuid_test-video.mp4'
      }
    });

    // Mock S3 upload failure
    axios.put.mockRejectedValueOnce(new Error('S3 upload failed'));

    // Render the component
    render(<AudioUploadComponent />);

    // Simulate file selection
    const fileInput = screen.getByRole('textbox', { type: 'file' });
    fireEvent.change(fileInput, { target: { files: [mockFile] } });

    // Click upload button
    const uploadButton = screen.getByText('Upload and Process');
    fireEvent.click(uploadButton);

    // Verify error state
    await waitFor(() => {
      expect(screen.getByText('An error occurred during the upload. Please try again.')).toBeInTheDocument();
    });
  });

  it('handles summary polling timeout appropriately', async () => {
    // Mock successful pre-signed URL request
    axios.post.mockResolvedValueOnce({
      data: {
        uploadUrl: mockPresignedUrl,
        key: 'test-uuid_test-video.mp4'
      }
    });

    // Mock successful S3 upload
    axios.put.mockResolvedValueOnce({});

    // Mock summary polling always returning not found
    axios.get.mockResolvedValue({ data: { exists: false } });

    // Render the component
    render(<AudioUploadComponent />);

    // Simulate file selection
    const fileInput = screen.getByRole('textbox', { type: 'file' });
    fireEvent.change(fileInput, { target: { files: [mockFile] } });

    // Click upload button
    const uploadButton = screen.getByText('Upload and Process');
    fireEvent.click(uploadButton);

    // Verify timeout error after polling
    await waitFor(() => {
      expect(screen.getByText('Summary not available after several attempts. Please try again later.')).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('updates progress bar during upload', async () => {
    // Mock successful pre-signed URL request
    axios.post.mockResolvedValueOnce({
      data: {
        uploadUrl: mockPresignedUrl,
        key: 'test-uuid_test-video.mp4'
      }
    });

    // Mock S3 upload with progress
    axios.put.mockImplementationOnce(() => {
      return new Promise((resolve) => {
        // Simulate upload progress events
        if (axios.put.mock.calls[0][2].onUploadProgress) {
          axios.put.mock.calls[0][2].onUploadProgress({ loaded: 50, total: 100 });
          axios.put.mock.calls[0][2].onUploadProgress({ loaded: 100, total: 100 });
        }
        resolve({});
      });
    });

    // Render the component
    render(<AudioUploadComponent />);

    // Simulate file selection
    const fileInput = screen.getByRole('textbox', { type: 'file' });
    fireEvent.change(fileInput, { target: { files: [mockFile] } });

    // Click upload button
    const uploadButton = screen.getByText('Upload and Process');
    fireEvent.click(uploadButton);

    // Verify progress updates
    await waitFor(() => {
      expect(screen.getByText('Uploading... 50%')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Uploading... 100%')).toBeInTheDocument();
    });
  });
});
