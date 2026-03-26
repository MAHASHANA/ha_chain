// ============================================================
// Ha_Chain - Send Screen (THE CORE)
// Currency pair selector, amount, live match estimate,
// fee calculation, competitor comparison
// ============================================================

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton, Divider, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import {
  RootStackParamList,
  CurrencyCode,
  TransferQuote,
  CompetitorComparison,
} from '../../types';
import { getQuote, GetQuoteParams } from '../../services/transfer';
import {
  formatCurrency,
  formatPercentage,
  formatRate,
  formatDelivery,
} from '../../utils/formatting';
import { SEND_CURRENCIES, RECEIVE_CURRENCIES, getCurrency } from '../../utils/constants';
import AmountInput from '../../components/common/AmountInput';
import CurrencySelector from '../../components/common/CurrencySelector';
import MatchStatus from '../../components/send/MatchStatus';
import FeeBreakdown from '../../components/send/FeeBreakdown';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';

type SendScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Send'>;
};

// Mock quote generator for development
const generateMockQuote = (
  sendAmount: number,
  sendCurrency: CurrencyCode,
  receiveCurrency: CurrencyCode,
): TransferQuote => {
  const rates: Record<string, number> = {
    'USD-INR': 83.12,
    'USD-PHP': 56.85,
    'USD-NGN': 950.0,
    'USD-KES': 153.5,
    'USD-GHS': 12.85,
    'USD-BDT': 109.75,
    'USD-PKR': 278.5,
    'USD-MXN': 17.15,
    'USD-BRL': 4.95,
    'USD-ETB': 56.5,
    'USD-SOS': 571.0,
    'EUR-INR': 90.5,
    'EUR-NGN': 1035.0,
    'GBP-INR': 105.3,
    'GBP-NGN': 1195.0,
  };

  const rateKey = `${sendCurrency}-${receiveCurrency}`;
  const reverseKey = `${receiveCurrency}-${sendCurrency}`;
  let rate = rates[rateKey] || rates[reverseKey] ? 1 / (rates[reverseKey] || 1) : 83.12;

  const matchedPct = Math.min(95, Math.max(45, Math.round(60 + Math.random() * 35)));
  const matchedAmount = (sendAmount * matchedPct) / 100;
  const unmatchedAmount = sendAmount - matchedAmount;
  const unmatchedFee = unmatchedAmount * 0.002; // 0.2% on unmatched
  const platformFee = sendAmount > 500 ? 0 : 0.25;
  const totalFee = unmatchedFee + platformFee;

  const receiveAmount = (sendAmount - totalFee) * rate;

  // Competitor comparison
  const competitors: CompetitorComparison[] = [
    {
      name: 'Wise',
      fee: sendAmount * 0.0065,
      rate: rate * 0.997,
      savings: sendAmount * 0.0065 - totalFee,
    },
    {
      name: 'Western Union',
      fee: sendAmount * 0.015 + 4.99,
      rate: rate * 0.98,
      savings: sendAmount * 0.015 + 4.99 - totalFee,
    },
    {
      name: 'Remitly',
      fee: sendAmount * 0.008 + 2.99,
      rate: rate * 0.995,
      savings: sendAmount * 0.008 + 2.99 - totalFee,
    },
  ];

  return {
    id: `q_${Date.now()}`,
    sendAmount,
    sendCurrency,
    receiveAmount: Math.round(receiveAmount * 100) / 100,
    receiveCurrency,
    exchangeRate: rate,
    matchedAmount,
    matchedPercentage: matchedPct,
    unmatchedAmount,
    matchedFee: 0,
    unmatchedFee: Math.round(unmatchedFee * 100) / 100,
    platformFee,
    totalFee: Math.round(totalFee * 100) / 100,
    totalFeePercentage: Math.round((totalFee / sendAmount) * 10000) / 100,
    estimatedDelivery: new Date(Date.now() + 1800000).toISOString(),
    expiresAt: new Date(Date.now() + 120000).toISOString(),
    competitorComparison: competitors,
  };
};

const SendScreen: React.FC<SendScreenProps> = ({ navigation }) => {
  const [sendCurrency, setSendCurrency] = useState<CurrencyCode>('USD');
  const [receiveCurrency, setReceiveCurrency] = useState<CurrencyCode>('INR');
  const [sendAmount, setSendAmount] = useState('');
  const [receiveAmount, setReceiveAmount] = useState('');
  const [quote, setQuote] = useState<TransferQuote | null>(null);
  const [isLoadingQuote, setIsLoadingQuote] = useState(false);
  const [isSearchingMatch, setIsSearchingMatch] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const quoteTimer = useRef<NodeJS.Timeout | null>(null);

  // Debounced quote fetching
  const fetchQuote = useCallback(
    async (amount: number, from: CurrencyCode, to: CurrencyCode) => {
      if (amount <= 0) {
        setQuote(null);
        setReceiveAmount('');
        return;
      }

      setIsLoadingQuote(true);
      setIsSearchingMatch(true);
      setError(null);

      try {
        // Try API first, fall back to mock
        let quoteData: TransferQuote;
        try {
          quoteData = await getQuote({ sendAmount: amount, sendCurrency: from, receiveCurrency: to });
        } catch {
          // Use mock data in development
          quoteData = generateMockQuote(amount, from, to);
        }

        setQuote(quoteData);
        setReceiveAmount(quoteData.receiveAmount.toString());

        // Simulate match searching animation
        setTimeout(() => setIsSearchingMatch(false), 1500);
      } catch (err: any) {
        setError(err?.response?.data?.message || 'Failed to get quote');
        setQuote(null);
      } finally {
        setIsLoadingQuote(false);
      }
    },
    [],
  );

  // Debounce amount changes
  useEffect(() => {
    if (quoteTimer.current) {
      clearTimeout(quoteTimer.current);
    }

    const amount = parseFloat(sendAmount);
    if (!isNaN(amount) && amount > 0) {
      quoteTimer.current = setTimeout(() => {
        fetchQuote(amount, sendCurrency, receiveCurrency);
      }, 500);
    } else {
      setQuote(null);
      setReceiveAmount('');
    }

    return () => {
      if (quoteTimer.current) clearTimeout(quoteTimer.current);
    };
  }, [sendAmount, sendCurrency, receiveCurrency, fetchQuote]);

  const handleSwapCurrencies = () => {
    if (SEND_CURRENCIES.includes(receiveCurrency) && RECEIVE_CURRENCIES.includes(sendCurrency)) {
      const tempSend = sendCurrency;
      setSendCurrency(receiveCurrency);
      setReceiveCurrency(tempSend);
    }
  };

  const handleContinue = () => {
    if (!quote) return;
    navigation.navigate('Quote', { quoteId: quote.id });
  };

  const sendCurrencyInfo = getCurrency(sendCurrency);
  const receiveCurrencyInfo = getCurrency(receiveCurrency);
  const parsedAmount = parseFloat(sendAmount) || 0;
  const isValidAmount =
    parsedAmount >= (sendCurrencyInfo?.minSend || 0) &&
    parsedAmount <= (sendCurrencyInfo?.maxSend || Infinity);

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />

      {/* Header */}
      <View style={styles.header}>
        <IconButton
          icon="arrow-left"
          onPress={() => navigation.goBack()}
          iconColor={colors.text}
        />
        <Text style={styles.headerTitle}>Send Money</Text>
        <View style={{ width: 48 }} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Currency Pair Selector */}
          <View style={styles.currencyPairContainer}>
            <CurrencySelector
              selectedCurrency={sendCurrency}
              onSelect={setSendCurrency}
              label="I have"
              filterCurrencies={SEND_CURRENCIES}
            />

            {/* Swap button */}
            <TouchableOpacity
              style={styles.swapButton}
              onPress={handleSwapCurrencies}
              activeOpacity={0.7}
            >
              <Icon name="swap-vertical" size={22} color={colors.primary} />
            </TouchableOpacity>

            <CurrencySelector
              selectedCurrency={receiveCurrency}
              onSelect={setReceiveCurrency}
              label="They receive"
              filterCurrencies={RECEIVE_CURRENCIES}
            />
          </View>

          {/* Send Amount */}
          <AmountInput
            value={sendAmount}
            onChangeText={setSendAmount}
            currency={sendCurrency}
            label="You send"
            placeholder="0.00"
            error={
              parsedAmount > 0 && !isValidAmount
                ? `Amount must be between ${formatCurrency(
                    sendCurrencyInfo?.minSend || 0,
                    sendCurrency,
                  )} and ${formatCurrency(sendCurrencyInfo?.maxSend || 0, sendCurrency)}`
                : undefined
            }
          />

          {/* Exchange Rate Display */}
          {quote && (
            <View style={styles.rateRow}>
              <Icon name="swap-horizontal" size={16} color={colors.textSecondary} />
              <Text style={styles.rateText}>
                1 {sendCurrency} = {formatRate(quote.exchangeRate)} {receiveCurrency}
              </Text>
              <Text style={styles.midMarketBadge}>Mid-market rate</Text>
            </View>
          )}

          {/* Receive Amount */}
          <AmountInput
            value={receiveAmount}
            onChangeText={() => {}}
            currency={receiveCurrency}
            label="They receive"
            editable={false}
          />

          {/* Loading indicator */}
          {isLoadingQuote && !quote && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color={colors.primary} />
              <Text style={styles.loadingText}>Getting best rate...</Text>
            </View>
          )}

          {/* Match Status (animated) */}
          {quote && (
            <View style={styles.section}>
              <MatchStatus
                matchedPercentage={quote.matchedPercentage}
                isSearching={isSearchingMatch}
                estimatedTime="~45 seconds"
              />
            </View>
          )}

          {/* Fee Breakdown */}
          {quote && (
            <View style={styles.section}>
              <FeeBreakdown quote={quote} />
            </View>
          )}

          {/* Delivery Time */}
          {quote && (
            <Card variant="outlined" padding="small" style={styles.section}>
              <View style={styles.deliveryRow}>
                <Icon name="clock-fast" size={20} color={colors.primary} />
                <View style={styles.deliveryInfo}>
                  <Text style={styles.deliveryTitle}>Estimated Delivery</Text>
                  <Text style={styles.deliveryTime}>
                    {formatDelivery(quote.estimatedDelivery)}
                  </Text>
                </View>
                <View style={styles.deliveryBadge}>
                  <Icon name="lightning-bolt" size={14} color={colors.accent} />
                  <Text style={styles.deliveryBadgeText}>Fast</Text>
                </View>
              </View>
            </Card>
          )}

          {/* Competitor Comparison */}
          {quote && quote.competitorComparison.length > 0 && (
            <View style={styles.section}>
              <Card variant="default" padding="medium">
                <View style={styles.comparisonHeader}>
                  <Icon name="trophy" size={20} color={colors.accent} />
                  <Text style={styles.comparisonTitle}>How we compare</Text>
                </View>

                <View style={styles.comparisonTable}>
                  {/* Ha_Chain row (us) */}
                  <View style={[styles.comparisonRow, styles.comparisonRowHighlight]}>
                    <View style={styles.comparisonNameCol}>
                      <Icon name="swap-horizontal-circle" size={18} color={colors.primary} />
                      <Text style={[styles.comparisonName, { color: colors.primary, fontWeight: '700' }]}>
                        Ha_Chain
                      </Text>
                    </View>
                    <Text style={[styles.comparisonFee, { color: colors.secondary }]}>
                      {formatCurrency(quote.totalFee, quote.sendCurrency)}
                    </Text>
                    <Text style={[styles.comparisonRate, { color: colors.primary }]}>
                      {formatRate(quote.exchangeRate)}
                    </Text>
                  </View>

                  <Divider style={styles.comparisonDivider} />

                  {/* Competitors */}
                  {quote.competitorComparison.map((comp, index) => (
                    <React.Fragment key={comp.name}>
                      <View style={styles.comparisonRow}>
                        <View style={styles.comparisonNameCol}>
                          <Icon name="bank" size={16} color={colors.textTertiary} />
                          <Text style={styles.comparisonName}>{comp.name}</Text>
                        </View>
                        <Text style={styles.comparisonFee}>
                          {formatCurrency(comp.fee, quote.sendCurrency)}
                        </Text>
                        <Text style={styles.comparisonRate}>{formatRate(comp.rate)}</Text>
                      </View>
                      {index < quote.competitorComparison.length - 1 && (
                        <Divider style={styles.comparisonDivider} />
                      )}
                    </React.Fragment>
                  ))}
                </View>

                {/* Savings callout */}
                <View style={styles.savingsCallout}>
                  <Icon name="piggy-bank" size={20} color={colors.secondary} />
                  <Text style={styles.savingsText}>
                    You save up to{' '}
                    <Text style={styles.savingsAmount}>
                      {formatCurrency(
                        Math.max(...quote.competitorComparison.map((c) => c.savings)),
                        quote.sendCurrency,
                      )}
                    </Text>{' '}
                    with Ha_Chain
                  </Text>
                </View>
              </Card>
            </View>
          )}

          {/* Error */}
          {error && (
            <View style={styles.errorContainer}>
              <Icon name="alert-circle" size={20} color={colors.error} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Bottom spacer */}
          <View style={{ height: 100 }} />
        </ScrollView>

        {/* Fixed bottom CTA */}
        <View style={styles.bottomCta}>
          <View style={styles.bottomSummary}>
            {quote ? (
              <>
                <Text style={styles.bottomSummaryLabel}>Total to pay</Text>
                <Text style={styles.bottomSummaryAmount}>
                  {formatCurrency(quote.sendAmount + quote.totalFee, quote.sendCurrency)}
                </Text>
              </>
            ) : (
              <Text style={styles.bottomSummaryLabel}>Enter amount to continue</Text>
            )}
          </View>
          <Button
            title="Continue"
            onPress={handleContinue}
            variant="primary"
            size="large"
            disabled={!quote || !isValidAmount || isLoadingQuote}
            loading={isLoadingQuote}
            icon="arrow-right"
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  flex: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  headerTitle: {
    ...typography.headlineMedium,
    color: colors.text,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.xxl,
    paddingTop: spacing.xl,
  },
  currencyPairContainer: {
    position: 'relative',
    marginBottom: spacing.sm,
  },
  swapButton: {
    position: 'absolute',
    right: 16,
    top: '50%',
    marginTop: -20,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
    ...shadows.medium,
  },
  rateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.xs,
  },
  rateText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  midMarketBadge: {
    ...typography.labelSmall,
    color: colors.secondary,
    backgroundColor: colors.secondaryBg,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
    marginLeft: spacing.sm,
    overflow: 'hidden',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.xl,
  },
  loadingText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
  },
  section: {
    marginBottom: spacing.lg,
  },
  deliveryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.sm,
  },
  deliveryInfo: {
    flex: 1,
    marginLeft: spacing.md,
  },
  deliveryTitle: {
    ...typography.labelMedium,
    color: colors.textSecondary,
  },
  deliveryTime: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  deliveryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.accentBg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.round,
  },
  deliveryBadgeText: {
    ...typography.labelSmall,
    color: colors.accentDark,
    marginLeft: 2,
  },
  comparisonHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  comparisonTitle: {
    ...typography.headlineSmall,
    color: colors.text,
    marginLeft: spacing.sm,
  },
  comparisonTable: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
  },
  comparisonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
  },
  comparisonRowHighlight: {
    backgroundColor: colors.primaryBg,
  },
  comparisonNameCol: {
    flex: 1.2,
    flexDirection: 'row',
    alignItems: 'center',
  },
  comparisonName: {
    ...typography.labelMedium,
    color: colors.text,
    marginLeft: spacing.sm,
  },
  comparisonFee: {
    flex: 0.8,
    ...typography.labelMedium,
    color: colors.text,
    textAlign: 'center',
  },
  comparisonRate: {
    flex: 0.8,
    ...typography.labelMedium,
    color: colors.textSecondary,
    textAlign: 'right',
  },
  comparisonDivider: {
    backgroundColor: colors.borderLight,
  },
  savingsCallout: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.secondaryBg,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginTop: spacing.lg,
  },
  savingsText: {
    ...typography.bodyMedium,
    color: colors.text,
    marginLeft: spacing.sm,
    flex: 1,
  },
  savingsAmount: {
    ...typography.labelLarge,
    color: colors.secondary,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.errorBg,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  errorText: {
    ...typography.bodyMedium,
    color: colors.error,
    marginLeft: spacing.sm,
    flex: 1,
  },
  bottomCta: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.xxl,
    paddingVertical: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    ...shadows.medium,
  },
  bottomSummary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  bottomSummaryLabel: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  bottomSummaryAmount: {
    ...typography.headlineMedium,
    color: colors.text,
  },
});

export default SendScreen;
