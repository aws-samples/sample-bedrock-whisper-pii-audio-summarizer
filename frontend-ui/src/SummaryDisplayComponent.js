import React from 'react';
import { Box, Paper, Typography, Fade } from '@mui/material';
import { FileText } from 'lucide-react';

const SummaryDisplayComponent = ({ summary }) => {
  return (
    <Fade in={true} timeout={800}>
      <Box sx={{ mt: 4 }}>
        <Paper 
          elevation={3} 
          sx={{ 
            p: 3,
            background: 'linear-gradient(to right bottom, #ffffff, #f8f9fa)',
            borderRadius: 2,
            position: 'relative'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <FileText size={24} style={{ marginRight: '12px', color: '#1976d2' }} />
            <Typography 
              variant="h6" 
              component="h2"
              sx={{ 
                color: '#1976d2',
                fontWeight: 500
              }}
            >
              Generated Summary
            </Typography>
          </Box>
          
          <Typography
            variant="body1"
            sx={{
              whiteSpace: 'pre-wrap',
              lineHeight: 1.8,
              color: 'text.primary',
              fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
              fontSize: '1rem',
              letterSpacing: '0.00938em',
              backgroundColor: 'rgba(0, 0, 0, 0.02)',
              p: 2,
              borderRadius: 1,
              border: '1px solid rgba(0, 0, 0, 0.08)'
            }}
          >
            {summary}
          </Typography>
        </Paper>
      </Box>
    </Fade>
  );
};

export default SummaryDisplayComponent;
