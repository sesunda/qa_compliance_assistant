/**
 * Utility functions for date/time formatting in Singapore timezone
 */

/**
 * Format date/time to Singapore timezone (SGT = UTC+8)
 * @param date - Date string or Date object
 * @param format - 'datetime' | 'date' | 'time'
 * @returns Formatted date string in SGT
 */
export function formatSGT(date: string | Date, format: 'datetime' | 'date' | 'time' = 'datetime'): string {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  // Check if date is valid
  if (isNaN(dateObj.getTime())) return '';
  
  const options: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Singapore',
  };
  
  if (format === 'datetime' || format === 'date') {
    options.year = 'numeric';
    options.month = '2-digit';
    options.day = '2-digit';
  }
  
  if (format === 'datetime' || format === 'time') {
    options.hour = '2-digit';
    options.minute = '2-digit';
    options.second = '2-digit';
    options.hour12 = false; // 24-hour format
  }
  
  const formatted = dateObj.toLocaleString('en-SG', options);
  
  // Add SGT suffix for clarity
  if (format === 'datetime') {
    return `${formatted} SGT`;
  } else if (format === 'time') {
    return `${formatted} SGT`;
  }
  
  return formatted;
}

/**
 * Format date only (DD/MM/YYYY format for Singapore)
 */
export function formatDateSGT(date: string | Date): string {
  return formatSGT(date, 'date');
}

/**
 * Format time only (HH:mm:ss format)
 */
export function formatTimeSGT(date: string | Date): string {
  return formatSGT(date, 'time');
}

/**
 * Format datetime (DD/MM/YYYY, HH:mm:ss SGT)
 */
export function formatDateTimeSGT(date: string | Date): string {
  return formatSGT(date, 'datetime');
}

/**
 * Get current time in Singapore timezone
 */
export function nowSGT(): Date {
  return new Date();
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return '';
  
  const now = new Date();
  const diffMs = now.getTime() - dateObj.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) {
    return 'just now';
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  } else {
    return formatDateSGT(dateObj);
  }
}
