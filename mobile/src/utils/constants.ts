// ============================================================
// Ha_Chain - Constants
// ============================================================

import { Currency, CurrencyCode } from '../types';

export const API_BASE_URL = __DEV__
  ? 'http://localhost:3000/api/v1'
  : 'https://api.hachain.io/api/v1';

export const WS_BASE_URL = __DEV__
  ? 'ws://localhost:3000/ws'
  : 'wss://api.hachain.io/ws';

export const STORAGE_KEYS = {
  ACCESS_TOKEN: '@ha_chain/access_token',
  REFRESH_TOKEN: '@ha_chain/refresh_token',
  USER: '@ha_chain/user',
  ONBOARDED: '@ha_chain/onboarded',
} as const;

export const QUOTE_EXPIRY_SECONDS = 120;

export const SUPPORTED_CURRENCIES: Currency[] = [
  { code: 'USD', name: 'US Dollar', symbol: '$', flag: '🇺🇸', decimals: 2, minSend: 10, maxSend: 50000 },
  { code: 'EUR', name: 'Euro', symbol: '€', flag: '🇪🇺', decimals: 2, minSend: 10, maxSend: 50000 },
  { code: 'GBP', name: 'British Pound', symbol: '£', flag: '🇬🇧', decimals: 2, minSend: 10, maxSend: 50000 },
  { code: 'INR', name: 'Indian Rupee', symbol: '₹', flag: '🇮🇳', decimals: 2, minSend: 500, maxSend: 4000000 },
  { code: 'PHP', name: 'Philippine Peso', symbol: '₱', flag: '🇵🇭', decimals: 2, minSend: 500, maxSend: 2500000 },
  { code: 'NGN', name: 'Nigerian Naira', symbol: '₦', flag: '🇳🇬', decimals: 2, minSend: 5000, maxSend: 50000000 },
  { code: 'KES', name: 'Kenyan Shilling', symbol: 'KSh', flag: '🇰🇪', decimals: 2, minSend: 1000, maxSend: 7000000 },
  { code: 'GHS', name: 'Ghanaian Cedi', symbol: '₵', flag: '🇬🇭', decimals: 2, minSend: 50, maxSend: 500000 },
  { code: 'SOS', name: 'Somali Shilling', symbol: 'Sh', flag: '🇸🇴', decimals: 2, minSend: 5000, maxSend: 30000000 },
  { code: 'ETB', name: 'Ethiopian Birr', symbol: 'Br', flag: '🇪🇹', decimals: 2, minSend: 500, maxSend: 5000000 },
  { code: 'BDT', name: 'Bangladeshi Taka', symbol: '৳', flag: '🇧🇩', decimals: 2, minSend: 1000, maxSend: 5000000 },
  { code: 'PKR', name: 'Pakistani Rupee', symbol: 'Rs', flag: '🇵🇰', decimals: 2, minSend: 2000, maxSend: 15000000 },
  { code: 'MXN', name: 'Mexican Peso', symbol: '$', flag: '🇲🇽', decimals: 2, minSend: 200, maxSend: 900000 },
  { code: 'BRL', name: 'Brazilian Real', symbol: 'R$', flag: '🇧🇷', decimals: 2, minSend: 50, maxSend: 250000 },
  { code: 'USDC', name: 'USD Coin', symbol: '$', flag: '💵', decimals: 6, minSend: 10, maxSend: 100000 },
];

export const getCurrency = (code: CurrencyCode): Currency | undefined =>
  SUPPORTED_CURRENCIES.find(c => c.code === code);

export const SEND_CURRENCIES: CurrencyCode[] = ['USD', 'EUR', 'GBP', 'USDC'];
export const RECEIVE_CURRENCIES: CurrencyCode[] = [
  'INR', 'PHP', 'NGN', 'KES', 'GHS', 'SOS', 'ETB', 'BDT', 'PKR', 'MXN', 'BRL',
  'USD', 'EUR', 'GBP',
];

export const COMPETITORS = {
  WISE: 'Wise',
  WESTERN_UNION: 'Western Union',
  REMITLY: 'Remitly',
} as const;
