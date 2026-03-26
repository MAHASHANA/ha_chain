// ============================================================
// Ha_Chain - Transfer Service (Quote, Send, Track)
// ============================================================

import api from './api';
import {
  ApiResponse,
  CurrencyCode,
  ExchangeRate,
  PaginatedResponse,
  PoolStats,
  Recipient,
  Transfer,
  TransferQuote,
  UserPoolPosition,
  WalletInfo,
  TokenizedAsset,
  Portfolio,
  Investment,
} from '../types';

// --- Transfer Quotes ---

export interface GetQuoteParams {
  sendAmount: number;
  sendCurrency: CurrencyCode;
  receiveCurrency: CurrencyCode;
}

export const getQuote = async (params: GetQuoteParams): Promise<TransferQuote> => {
  const { data } = await api.post<ApiResponse<TransferQuote>>('/transfers/quote', params);
  return data.data;
};

export const getQuoteById = async (quoteId: string): Promise<TransferQuote> => {
  const { data } = await api.get<ApiResponse<TransferQuote>>(`/transfers/quote/${quoteId}`);
  return data.data;
};

// --- Sending Transfers ---

export interface SendTransferParams {
  quoteId: string;
  recipientId: string;
  deliveryMethod: string;
  note?: string;
}

export const sendTransfer = async (params: SendTransferParams): Promise<Transfer> => {
  const { data } = await api.post<ApiResponse<Transfer>>('/transfers/send', params);
  return data.data;
};

// --- Transfer Tracking ---

export const getTransfer = async (transferId: string): Promise<Transfer> => {
  const { data } = await api.get<ApiResponse<Transfer>>(`/transfers/${transferId}`);
  return data.data;
};

export const getTransferHistory = async (
  page: number = 1,
  pageSize: number = 20,
): Promise<PaginatedResponse<Transfer>> => {
  const { data } = await api.get<ApiResponse<PaginatedResponse<Transfer>>>('/transfers', {
    params: { page, pageSize },
  });
  return data.data;
};

// --- Exchange Rates ---

export const getExchangeRate = async (
  from: CurrencyCode,
  to: CurrencyCode,
): Promise<ExchangeRate> => {
  const { data } = await api.get<ApiResponse<ExchangeRate>>('/rates', {
    params: { from, to },
  });
  return data.data;
};

// --- Recipients ---

export const getRecipients = async (): Promise<Recipient[]> => {
  const { data } = await api.get<ApiResponse<Recipient[]>>('/recipients');
  return data.data;
};

export const createRecipient = async (
  recipient: Omit<Recipient, 'id' | 'isSaved'>,
): Promise<Recipient> => {
  const { data } = await api.post<ApiResponse<Recipient>>('/recipients', recipient);
  return data.data;
};

// --- Pool & Matching ---

export const getPoolStats = async (): Promise<PoolStats> => {
  const { data } = await api.get<ApiResponse<PoolStats>>('/pool/stats');
  return data.data;
};

export const getUserPoolPositions = async (): Promise<UserPoolPosition[]> => {
  const { data } = await api.get<ApiResponse<UserPoolPosition[]>>('/pool/positions');
  return data.data;
};

// --- Wallet ---

export const getWallet = async (): Promise<WalletInfo> => {
  const { data } = await api.get<ApiResponse<WalletInfo>>('/wallet');
  return data.data;
};

// --- Tokenized Assets ---

export const getAssets = async (): Promise<TokenizedAsset[]> => {
  const { data } = await api.get<ApiResponse<TokenizedAsset[]>>('/assets');
  return data.data;
};

export const getPortfolio = async (): Promise<Portfolio> => {
  const { data } = await api.get<ApiResponse<Portfolio>>('/portfolio');
  return data.data;
};

export const investInAsset = async (
  assetId: string,
  amount: number,
): Promise<Investment> => {
  const { data } = await api.post<ApiResponse<Investment>>(`/assets/${assetId}/invest`, {
    amount,
  });
  return data.data;
};
