import React, { useState } from 'react';
import { GET_UPLOAD_URL_ENDPOINT, CHECK_SUMMARY_ENDPOINT } from './config';
import { Upload } from 'lucide-react';
import { Alert, AlertTitle, Box, Button, CircularProgress, Typography, LinearProgress } from '@mui/material';
import axios from 'axios';
import SummaryDisplayComponent from './SummaryDisplayComponent';
import './AudioUploadComponent.css';

const AudioUploadComponent = () => {
  const [file, setFile] = useState(null);
  const [summary, setSummary] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
    setError('');
    setSummary('');
    setUploadProgress(0);
  };

  const pollForSummary = async (uuid) => {
    const pollInterval = 60000; // Poll every 60 seconds
    const maxAttempts = 15; // Poll for up to 15 attempts (15 minutes total)
    let attempts = 0;

    const checkSummary = async () => {
      try {
        // Extract just the UUID part, removing both uploads/ prefix and filename suffix
        const uuidOnly = uuid.replace('uploads/', '').split('-').slice(0, 5).join('-');
        const response = await axios.get(`${CHECK_SUMMARY_ENDPOINT}/check-summary/${uuidOnly}`, {
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        if (response.data.exists) {
          const filename = response.data.key;
          const summaryResponse = await axios.get(`${CHECK_SUMMARY_ENDPOINT}/fetch-summary/${filename}`, {
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest'
            }
          });
          setSummary(summaryResponse.data.content);
          setIsLoading(false);
          setUploadProgress(0);
        } else if (attempts < maxAttempts) {
          attempts += 1;
          setTimeout(checkSummary, pollInterval);
        } else {
          setError('Summary not available after several attempts. Please try again later.');
          setIsLoading(false);
          setUploadProgress(0);
        }
      } catch (err) {
        const errorMessage = err.response?.data?.error || 'An error occurred while checking for the summary. Please try again.';
        setError(errorMessage);
        setIsLoading(false);
        setUploadProgress(0);
        console.error('Summary check error:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status
        });
      }
    };
    
    checkSummary();
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setIsLoading(true);
    setError('');
    setUploadProgress(0);

    try {
      // Get pre-signed URL
      // Validate file type
      if (!file.type.startsWith('audio/') && !file.type.startsWith('video/')) {
        throw new Error('Please select an audio or video file.');
      }

      // Request pre-signed URL using JSON
      const urlResponse = await axios.post(
        `${GET_UPLOAD_URL_ENDPOINT}/get-upload-url`,
        {
          fileName: file.name,
          fileType: file.type
        },
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 10000, // 10 second timeout
          validateStatus: function (status) {
            return status >= 200 && status < 300; // Only accept success status codes
          }
        }
      ).catch(err => {
        if (err.code === 'ECONNABORTED') {
          throw new Error('Request timed out. Please try again.');
        }
        if (err.response?.data?.message) {
          throw new Error(err.response.data.message);
        }
        throw err;
      });

      const { uploadUrl, key } = urlResponse.data;
      if (!uploadUrl || !key) {
        throw new Error('Invalid response from server. Missing upload URL or key.');
      }

      // Upload directly to S3 using pre-signed URL
      await axios.put(uploadUrl, file, {
        headers: {
          'Content-Type': file.type
        },
        timeout: 0, // Disable timeout for upload
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
          
          // Log progress to console for debugging
          if (progress % 20 === 0) { // Log every 20%
            console.log(`Upload progress: ${progress}%`);
          }
        }
      }).catch(err => {
        if (err.response?.status === 403) {
          throw new Error('Upload permission denied. Please try again or contact support.');
        }
        throw err;
      });

      // Extract UUID from the key (format: uploads/uuid-filename)
      const uuid = key.split('/')[1].split('-')[0];

      // Start polling for summary
      pollForSummary(uuid);

    } catch (err) {
      let errorMessage;
      if (err.message) {
        errorMessage = err.message;
      } else if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err.response?.status === 413) {
        errorMessage = 'File is too large. Please select a smaller file.';
      } else {
        errorMessage = 'An error occurred during the upload. Please try again.';
      }
      setError(errorMessage);
      setIsLoading(false);
      setUploadProgress(0);
      console.error('Upload error:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status
      });
    }
  };

  return (
    <Box sx={{ p: 4, maxWidth: 500, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Audio/Video Upload and Summary
      </Typography>

      <Box 
        sx={{ 
          mb: 4,
          '& input': {
            display: 'none'
          }
        }}
      >
        <input
          id="audio-file-input"
          type="file"
          accept="audio/*,video/*"
          onChange={handleFileChange}
        />
        <label htmlFor="audio-file-input">
          <Button
            variant="outlined"
            component="span"
            fullWidth
            sx={{
              height: '56px',
              borderStyle: 'dashed',
              borderWidth: '2px',
              textTransform: 'none'
            }}
          >
            {file ? file.name : 'Click to select an audio/video file'}
          </Button>
        </label>
      </Box>

      <Button
        variant="contained"
        color="primary"
        onClick={handleUpload}
        disabled={isLoading || !file}
        fullWidth
        startIcon={isLoading ? <CircularProgress size={24} /> : <Upload />}
      >
        {isLoading ? `Uploading... ${uploadProgress}%` : 'Upload and Process'}
      </Button>

      {isLoading && (
        <Box sx={{ width: '100%', mt: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 4 }}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      {summary && (
        <SummaryDisplayComponent summary={summary} />
      )}
    </Box>
  );
};

export default AudioUploadComponent;
