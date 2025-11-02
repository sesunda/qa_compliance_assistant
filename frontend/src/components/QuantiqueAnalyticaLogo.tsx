import React from 'react';
import { Box } from '@mui/material';

interface QuantiqueAnalyticaLogoProps {
  className?: string;
  size?: 'small' | 'default' | 'large';
}

const QuantiqueAnalyticaLogo: React.FC<QuantiqueAnalyticaLogoProps> = ({ 
  className = "", 
  size = "default" 
}) => {
  const logoHeight = size === 'small' ? 32 : size === 'large' ? 48 : 40;

  return (
    <Box className={className} sx={{ display: 'flex', alignItems: 'center' }}>
      <img 
        src="/quantique-analytica-logo.svg" 
        alt="Quantique Analytica" 
        style={{ 
          height: logoHeight,
          width: 'auto',
          objectFit: 'contain'
        }}
      />
    </Box>
  );
};

export default QuantiqueAnalyticaLogo;