import React from 'react';
import { Button, ButtonProps } from '@mui/material';

/**
 * Primary Button Component
 * Uses the main brand color (#006D77)
 * For primary actions like submit, save, create
 */
export const PrimaryButton: React.FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <Button
      variant="contained"
      color="primary"
      sx={{
        backgroundColor: '#006D77',
        color: '#FFFFFF',
        fontWeight: 600,
        fontSize: '0.875rem',
        padding: '8px 20px',
        borderRadius: '8px',
        textTransform: 'none',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        '&:hover': {
          backgroundColor: '#005864',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          transform: 'translateY(-1px)',
        },
        '&:active': {
          transform: 'translateY(0)',
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        },
        '&:disabled': {
          backgroundColor: '#9CA3AF',
          color: '#FFFFFF',
        },
        transition: 'all 200ms ease-in-out',
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
};

/**
 * Secondary Button Component
 * Uses the secondary soft teal color (#83C5BE)
 * For secondary actions like cancel, back
 */
export const SecondaryButton: React.FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <Button
      variant="contained"
      sx={{
        backgroundColor: '#83C5BE',
        color: '#1A1A1A',
        fontWeight: 600,
        fontSize: '0.875rem',
        padding: '8px 20px',
        borderRadius: '8px',
        textTransform: 'none',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        '&:hover': {
          backgroundColor: '#5FA8A0',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          transform: 'translateY(-1px)',
        },
        '&:active': {
          transform: 'translateY(0)',
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        },
        '&:disabled': {
          backgroundColor: '#9CA3AF',
          color: '#FFFFFF',
        },
        transition: 'all 200ms ease-in-out',
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
};

/**
 * Accent Button Component
 * Uses the accent warm red color (#FF6B6B)
 * For attention-grabbing or destructive actions like delete
 */
export const AccentButton: React.FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <Button
      variant="contained"
      sx={{
        backgroundColor: '#FF6B6B',
        color: '#FFFFFF',
        fontWeight: 600,
        fontSize: '0.875rem',
        padding: '8px 20px',
        borderRadius: '8px',
        textTransform: 'none',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        '&:hover': {
          backgroundColor: '#E65555',
          boxShadow: '0 4px 14px 0 rgba(255, 107, 107, 0.15)',
          transform: 'translateY(-1px)',
        },
        '&:active': {
          transform: 'translateY(0)',
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        },
        '&:disabled': {
          backgroundColor: '#9CA3AF',
          color: '#FFFFFF',
        },
        transition: 'all 200ms ease-in-out',
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
};

/**
 * Outline Button Component
 * Transparent with primary border
 * For tertiary actions
 */
export const OutlineButton: React.FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <Button
      variant="outlined"
      sx={{
        backgroundColor: 'transparent',
        color: '#006D77',
        borderColor: '#006D77',
        borderWidth: '2px',
        fontWeight: 600,
        fontSize: '0.875rem',
        padding: '6px 18px',
        borderRadius: '8px',
        textTransform: 'none',
        '&:hover': {
          backgroundColor: '#006D77',
          borderColor: '#006D77',
          color: '#FFFFFF',
          borderWidth: '2px',
        },
        '&:active': {
          backgroundColor: '#005864',
        },
        '&:disabled': {
          borderColor: '#9CA3AF',
          color: '#9CA3AF',
        },
        transition: 'all 200ms ease-in-out',
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
};

/**
 * Text Button Component
 * Minimal styling for inline actions
 */
export const TextButton: React.FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <Button
      variant="text"
      sx={{
        color: '#006D77',
        fontWeight: 600,
        fontSize: '0.875rem',
        padding: '6px 12px',
        borderRadius: '6px',
        textTransform: 'none',
        '&:hover': {
          backgroundColor: 'rgba(0, 109, 119, 0.08)',
        },
        '&:active': {
          backgroundColor: 'rgba(0, 109, 119, 0.12)',
        },
        '&:disabled': {
          color: '#9CA3AF',
        },
        transition: 'all 200ms ease-in-out',
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
};

/**
 * Icon Button Container
 * For buttons with only icons
 */
export const IconButtonStyled: React.FC<ButtonProps> = ({ children, ...props }) => {
  return (
    <Button
      sx={{
        minWidth: 'auto',
        width: '40px',
        height: '40px',
        padding: '8px',
        borderRadius: '8px',
        color: '#006D77',
        '&:hover': {
          backgroundColor: 'rgba(0, 109, 119, 0.08)',
        },
        transition: 'all 200ms ease-in-out',
        ...props.sx,
      }}
      {...props}
    >
      {children}
    </Button>
  );
};

export default {
  PrimaryButton,
  SecondaryButton,
  AccentButton,
  OutlineButton,
  TextButton,
  IconButtonStyled,
};
