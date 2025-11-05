import React from 'react';
import { Box } from '@mui/material';

interface QuantiqueAnalyticaLogoProps {
  className?: string;
  size?: 'small' | 'default' | 'large' | 'xlarge';
}

const QuantiqueAnalyticaLogo: React.FC<QuantiqueAnalyticaLogoProps> = ({ 
  className = "", 
  size = "default" 
}) => {
  // Responsive heights based on size prop
  const logoHeight = size === 'small' ? 40 : size === 'large' ? 80 : size === 'xlarge' ? 180 : 60;

  return (
    <Box className={className} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <img 
        src="/assets/logo.png" 
        alt="Quantique Analytica" 
        style={{ 
          height: logoHeight,
          width: 'auto',
          objectFit: 'contain',
          maxWidth: '100%',
          imageRendering: 'high-quality',
          WebkitFontSmoothing: 'antialiased'
        }}
      />
    </Box>
  );
};

export default QuantiqueAnalyticaLogo;