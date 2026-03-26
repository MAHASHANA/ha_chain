// ============================================================
// Ha_Chain Mobile App - TypeScript Type Definitions
// ============================================================

// --- Auth Types ---

export interface User {
  id: string;
  phone: string;
  email?: string;
  firstName: string;
  lastName: string;
  country: string;
  defaultCurrency: CurrencyCode;
  kycStatus: KYCStatus;
  isAgent: boolean;
  createdAt: string;
  avatarUrl?: string;
}

export type KYCStatus = 'none' | 'pending' | 'verified' | 'rejected';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
}

export interface LoginRequest {
  phone: string;
  countryCode: string;
}

export interface VerifyOTPRequest {
  phone: string;
  countryCode: string;
  otp: string;
}

export interface RegisterRequest {
  phone: string;
  countryCode: string;
  firstName: string;
  lastName: string;
  email?: string;
  country: string;
}

// --- Currency Types ---

export type CurrencyCode =
  | 'USD'
  | 'EUR'
  | 'GBP'
  | 'INR'
  | 'PHP'
  | 'NGN'
  | 'KES'
  | 'GHS'
  | 'SOS'
  | 'ETB'
  | 'BDT'
  | 'PKR'
  | 'MXN'
  | 'BRL'
  | 'USDC';

export interface Currency {
  code: CurrencyCode;
  name: string;
  symbol: string;
  flag: string;
  decimals: number;
  minSend: number;
  maxSend: number;
}

export interface ExchangeRate {
  from: CurrencyCode;
  to: CurrencyCode;
  rate: number;
  midMarketRate: number;
  updatedAt: string;
}

// --- Transfer Types ---

export interface TransferQuote {
  id: string;
  sendAmount: number;
  sendCurrency: CurrencyCode;
  receiveAmount: number;
  receiveCurrency: CurrencyCode;
  exchangeRate: number;
  matchedAmount: number;
  matchedPercentage: number;
  unmatchedAmount: number;
  matchedFee: number;
  unmatchedFee: number;
  platformFee: number;
  totalFee: number;
  totalFeePercentage: number;
  estimatedDelivery: string;
  expiresAt: string;
  competitorComparison: CompetitorComparison[];
}

export interface CompetitorComparison {
  name: string;
  fee: number;
  rate: number;
  savings: number;
}

export interface Recipient {
  id: string;
  firstName: string;
  lastName: string;
  phone: string;
  email?: string;
  country: string;
  currency: CurrencyCode;
  deliveryMethod: DeliveryMethod;
  accountDetails?: AccountDetails;
  isSaved: boolean;
}

export type DeliveryMethod = 'mobile_money' | 'bank_transfer' | 'cash_pickup' | 'wallet';

export interface AccountDetails {
  bankName?: string;
  accountNumber?: string;
  routingNumber?: string;
  mobileMoneyProvider?: string;
  mobileMoneyNumber?: string;
  walletAddress?: string;
  upiId?: string;
}

export interface Transfer {
  id: string;
  status: TransferStatus;
  sendAmount: number;
  sendCurrency: CurrencyCode;
  receiveAmount: number;
  receiveCurrency: CurrencyCode;
  exchangeRate: number;
  totalFee: number;
  matchedPercentage: number;
  recipient: Recipient;
  deliveryMethod: DeliveryMethod;
  matchDetails?: MatchDetails;
  createdAt: string;
  completedAt?: string;
  estimatedDelivery: string;
  trackingUrl?: string;
  blockchainTxHash?: string;
}

export type TransferStatus =
  | 'pending'
  | 'matching'
  | 'matched'
  | 'processing'
  | 'sending'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface MatchDetails {
  matchId: string;
  matchedWithUserId: string;
  matchedAmount: number;
  matchedAt: string;
  isFullMatch: boolean;
}

// --- Pool Types ---

export interface PoolStats {
  totalVolume24h: number;
  totalMatches24h: number;
  averageMatchTime: number;
  currencyPools: CurrencyPool[];
  recentMatches: RecentMatch[];
}

export interface CurrencyPool {
  currency: CurrencyCode;
  totalAvailable: number;
  orderCount: number;
  averageOrderSize: number;
  matchRate: number;
}

export interface RecentMatch {
  id: string;
  fromCurrency: CurrencyCode;
  toCurrency: CurrencyCode;
  amount: number;
  matchedAt: string;
  timeAgo: string;
}

export interface UserPoolPosition {
  transferId: string;
  amount: number;
  currency: CurrencyCode;
  matchedPercentage: number;
  matchedAmount: number;
  remainingAmount: number;
  estimatedMatchTime: string;
  queuePosition: number;
}

// --- Investment Types ---

export interface TokenizedAsset {
  id: string;
  name: string;
  description: string;
  assetType: AssetType;
  tokenSymbol: string;
  totalSupply: number;
  pricePerToken: number;
  currency: CurrencyCode;
  apy: number;
  riskLevel: RiskLevel;
  minInvestment: number;
  totalInvested: number;
  investorCount: number;
  maturityDate?: string;
  imageUrl?: string;
}

export type AssetType = 'real_estate' | 'bond' | 'commodity' | 'liquidity_pool' | 'infrastructure';
export type RiskLevel = 'low' | 'medium' | 'high';

export interface Investment {
  id: string;
  asset: TokenizedAsset;
  tokensOwned: number;
  investedAmount: number;
  currentValue: number;
  returnAmount: number;
  returnPercentage: number;
  purchasedAt: string;
}

export interface Portfolio {
  totalInvested: number;
  currentValue: number;
  totalReturn: number;
  totalReturnPercentage: number;
  investments: Investment[];
}

// --- Agent Types ---

export interface AgentProfile {
  id: string;
  userId: string;
  agentCode: string;
  serviceArea: string;
  rating: number;
  totalPayouts: number;
  totalEarnings: number;
  pendingPayouts: PendingPayout[];
  isActive: boolean;
}

export interface PendingPayout {
  id: string;
  transferId: string;
  recipientName: string;
  recipientPhone: string;
  amount: number;
  currency: CurrencyCode;
  deliveryMethod: DeliveryMethod;
  expiresAt: string;
  verificationCode: string;
  status: PayoutStatus;
}

export type PayoutStatus = 'pending' | 'accepted' | 'completed' | 'expired' | 'disputed';

export interface PayoutCompletion {
  payoutId: string;
  verificationCode: string;
  recipientSignature?: string;
  photoProof?: string;
}

// --- Balance Types ---

export interface Balance {
  currency: CurrencyCode;
  available: number;
  pending: number;
  total: number;
}

export interface WalletInfo {
  balances: Balance[];
  usdcBalance: number;
  totalValueUSD: number;
  walletAddress?: string;
}

// --- Navigation Types ---

export type RootStackParamList = {
  Welcome: undefined;
  Login: undefined;
  Register: { phone: string; countryCode: string };
  MainTabs: undefined;
  Send: undefined;
  Recipient: { sendAmount: number; sendCurrency: CurrencyCode; receiveCurrency: CurrencyCode };
  Quote: { quoteId: string };
  Confirm: { quoteId: string; recipientId: string };
  Success: { transferId: string };
  PoolStatus: undefined;
  Assets: undefined;
  Portfolio: undefined;
  AgentDashboard: undefined;
  Payout: { payoutId: string };
  Settings: undefined;
};

export type MainTabParamList = {
  Home: undefined;
  SendTab: undefined;
  Pool: undefined;
  Invest: undefined;
  More: undefined;
};

// --- API Response Types ---

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: ApiError[];
}

export interface ApiError {
  code: string;
  message: string;
  field?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// --- Notification Types ---

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  data?: Record<string, string>;
  read: boolean;
  createdAt: string;
}

export type NotificationType =
  | 'transfer_matched'
  | 'transfer_completed'
  | 'transfer_failed'
  | 'payout_available'
  | 'investment_return'
  | 'kyc_update'
  | 'promotion';
