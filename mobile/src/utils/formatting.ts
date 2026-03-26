// ============================================================
// Ha_Chain - Formatting Utilities
// ============================================================

import { CurrencyCode } from '../types';
import { getCurrency } from './constants';

/**
 * Format a number as currency with the appropriate symbol
 */
export const formatCurrency = (
  amount: number,
  currencyCode: CurrencyCode,
  options?: { showSymbol?: boolean; compact?: boolean },
): string => {
  const { showSymbol = true, compact = false } = options || {};
  const currency = getCurrency(currencyCode);
  const symbol = currency?.symbol || '';
  const decimals = currency?.decimals ?? 2;

  if (compact && amount >= 1_000_000) {
    const formatted = (amount / 1_000_000).toFixed(1);
    return showSymbol ? `${symbol}${formatted}M` : `${formatted}M`;
  }

  if (compact && amount >= 1_000) {
    const formatted = (amount / 1_000).toFixed(1);
    return showSymbol ? `${symbol}${formatted}K` : `${formatted}K`;
  }

  const formatted = amount.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  return showSymbol ? `${symbol}${formatted}` : formatted;
};

/**
 * Format a percentage with specified decimal places
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format a phone number for display
 */
export const formatPhone = (phone: string, countryCode?: string): string => {
  const clean = phone.replace(/\D/g, '');
  if (clean.length === 10) {
    return `(${clean.slice(0, 3)}) ${clean.slice(3, 6)}-${clean.slice(6)}`;
  }
  return phone;
};

/**
 * Format a relative time string (e.g., "2 minutes ago")
 */
export const formatTimeAgo = (dateString: string): string => {
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

/**
 * Format estimated delivery time
 */
export const formatDelivery = (isoString: string): string => {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins <= 0) return 'Now';
  if (diffMins < 60) return `${diffMins} min`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours`;
  return `${Math.floor(diffMins / 1440)} days`;
};

/**
 * Format exchange rate for display
 */
export const formatRate = (rate: number): string => {
  if (rate >= 100) return rate.toFixed(2);
  if (rate >= 1) return rate.toFixed(4);
  return rate.toFixed(6);
};

/**
 * Abbreviate large numbers
 */
export const abbreviateNumber = (num: number): string => {
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
};

/**
 * Mask sensitive info like account numbers
 */
export const maskString = (str: string, visibleChars: number = 4): string => {
  if (str.length <= visibleChars) return str;
  const masked = '*'.repeat(str.length - visibleChars);
  return masked + str.slice(-visibleChars);
};
