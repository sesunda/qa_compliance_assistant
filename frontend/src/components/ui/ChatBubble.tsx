import React from 'react';
import { Box, Avatar, Typography, Paper } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';

interface ChatBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date | string;
  avatar?: string;
  userName?: string;
}

/**
 * ChatBubble Component
 * Displays chat messages with distinct styling for user and assistant
 */
export const ChatBubble: React.FC<ChatBubbleProps> = ({
  role,
  content,
  timestamp,
  avatar,
  userName = 'You',
}) => {
  const isUser = role === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        gap: 2,
        mb: 3,
        maxWidth: '100%',
      }}
    >
      {/* Avatar */}
      <Avatar
        sx={{
          width: 36,
          height: 36,
          backgroundColor: isUser ? '#006D77' : '#83C5BE',
          color: isUser ? '#FFFFFF' : '#1A1A1A',
          flexShrink: 0,
        }}
      >
        {isUser ? (
          avatar ? (
            <img src={avatar} alt={userName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <PersonIcon fontSize="small" />
          )
        ) : (
          <SmartToyIcon fontSize="small" />
        )}
      </Avatar>

      {/* Message Content */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
          maxWidth: '75%',
          flex: 1,
        }}
      >
        {/* Name and Timestamp */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            mb: 0.5,
            flexDirection: isUser ? 'row-reverse' : 'row',
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: '#4F4F4F',
              fontWeight: 600,
              fontSize: '0.75rem',
            }}
          >
            {isUser ? userName : 'AI Assistant'}
          </Typography>
          {timestamp && (
            <Typography
              variant="caption"
              sx={{
                color: '#9CA3AF',
                fontSize: '0.7rem',
              }}
            >
              {typeof timestamp === 'string' ? timestamp : timestamp.toLocaleTimeString()}
            </Typography>
          )}
        </Box>

        {/* Message Bubble */}
        <Paper
          elevation={0}
          sx={{
            padding: '12px 16px',
            borderRadius: '12px',
            backgroundColor: isUser ? '#006D77' : '#FFFFFF',
            color: isUser ? '#FFFFFF' : '#1A1A1A',
            border: isUser ? 'none' : '1px solid rgba(0, 0, 0, 0.08)',
            boxShadow: isUser
              ? '0 2px 8px rgba(0, 109, 119, 0.15)'
              : '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
            maxWidth: '100%',
            wordWrap: 'break-word',
            transition: 'all 200ms ease-in-out',
            '&:hover': {
              boxShadow: isUser
                ? '0 4px 12px rgba(0, 109, 119, 0.2)'
                : '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              borderColor: isUser ? 'none' : 'rgba(0, 0, 0, 0.12)',
            },
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontSize: '0.875rem',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
              '& a': {
                color: isUser ? '#B8D8D3' : '#006D77',
                textDecoration: 'underline',
                '&:hover': {
                  color: isUser ? '#83C5BE' : '#005864',
                },
              },
              '& code': {
                backgroundColor: isUser ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 109, 119, 0.1)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '0.8125rem',
                fontFamily: '"Fira Code", "Consolas", monospace',
              },
              '& pre': {
                backgroundColor: isUser ? 'rgba(255, 255, 255, 0.1)' : '#F8FAFB',
                padding: '12px',
                borderRadius: '6px',
                overflow: 'auto',
                marginTop: '8px',
                marginBottom: '8px',
              },
            }}
          >
            {content}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

/**
 * SystemMessage Component
 * For system notifications and status updates
 */
export const SystemMessage: React.FC<{ content: string; timestamp?: Date | string }> = ({
  content,
  timestamp,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        my: 2,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          padding: '8px 16px',
          borderRadius: '20px',
          backgroundColor: '#EDF6F9',
          border: '1px solid rgba(0, 109, 119, 0.2)',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Typography
          variant="caption"
          sx={{
            color: '#4F4F4F',
            fontSize: '0.75rem',
            fontWeight: 500,
          }}
        >
          {content}
        </Typography>
        {timestamp && (
          <Typography
            variant="caption"
            sx={{
              color: '#9CA3AF',
              fontSize: '0.7rem',
            }}
          >
            {typeof timestamp === 'string' ? timestamp : timestamp.toLocaleTimeString()}
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

/**
 * TypingIndicator Component
 * Shows when AI is thinking/responding
 */
export const TypingIndicator: React.FC = () => {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 2,
        mb: 3,
      }}
    >
      <Avatar
        sx={{
          width: 36,
          height: 36,
          backgroundColor: '#83C5BE',
          color: '#1A1A1A',
        }}
      >
        <SmartToyIcon fontSize="small" />
      </Avatar>

      <Paper
        elevation={0}
        sx={{
          padding: '12px 16px',
          borderRadius: '12px',
          backgroundColor: '#FFFFFF',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Box
          sx={{
            display: 'flex',
            gap: 0.5,
            alignItems: 'center',
          }}
        >
          {[0, 1, 2].map((i) => (
            <Box
              key={i}
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: '#83C5BE',
                animation: 'typing 1.4s infinite',
                animationDelay: `${i * 0.2}s`,
                '@keyframes typing': {
                  '0%, 60%, 100%': {
                    transform: 'translateY(0)',
                    opacity: 0.7,
                  },
                  '30%': {
                    transform: 'translateY(-10px)',
                    opacity: 1,
                  },
                },
              }}
            />
          ))}
        </Box>
        <Typography
          variant="caption"
          sx={{
            color: '#4F4F4F',
            fontSize: '0.75rem',
            ml: 1,
          }}
        >
          AI is thinking...
        </Typography>
      </Paper>
    </Box>
  );
};

export default ChatBubble;
