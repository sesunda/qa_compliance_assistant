/**
 * Datetime utilities for Singapore Time (SGT) conversion and formatting
 * Singapore is UTC+8 with no daylight saving time
 */

/**
 * Convert UTC datetime string to Singapore Time (SGT)
 * @param utcDateString - ISO datetime string from backend (in UTC)
 * @returns Date object in Singapore timezone
 */
export const toSingaporeTime = (utcDateString: string | null | undefined): Date | null => {
  if (!utcDateString) return null;
  
  try {
    const date = new Date(utcDateString);
    if (isNaN(date.getTime())) return null;
    return date;
  } catch {
    return null;
  }
};

/**
 * Format datetime to Singapore Time string
 * @param utcDateString - ISO datetime string from backend (in UTC)
 * @param options - Intl.DateTimeFormatOptions for customization
 * @returns Formatted datetime string in SGT, or fallback string
 */
export const formatSingaporeDateTime = (
  utcDateString: string | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string => {
  if (!utcDateString) return '—';
  
  const date = toSingaporeTime(utcDateString);
  if (!date) return '—';
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: 'Asia/Singapore',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    ...options,
  };
  
  try {
    return new Intl.DateTimeFormat('en-SG', defaultOptions).format(date);
  } catch {
    return date.toLocaleString();
  }
};

/**
 * Format date only (no time) in Singapore timezone
 */
export const formatSingaporeDate = (utcDateString: string | null | undefined): string => {
  return formatSingaporeDateTime(utcDateString, {
    hour: undefined,
    minute: undefined,
    hour12: undefined,
  });
};

/**
 * Format time only (no date) in Singapore timezone
 */
export const formatSingaporeTime = (utcDateString: string | null | undefined): string => {
  return formatSingaporeDateTime(utcDateString, {
    year: undefined,
    month: undefined,
    day: undefined,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
};

/**
 * Format relative time (e.g., "2 hours ago", "3 days ago")
 */
export const formatRelativeTime = (utcDateString: string | null | undefined): string => {
  if (!utcDateString) return '—';
  
  const date = toSingaporeTime(utcDateString);
  if (!date) return '—';
  
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  
  // For older dates, show full date
  return formatSingaporeDateTime(utcDateString);
};

/**
 * Get current Singapore time
 */
export const getCurrentSingaporeTime = (): Date => {
  return new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Singapore' }));
};
