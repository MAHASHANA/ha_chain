// ============================================================
// Ha_Chain - Quote Screen (Fee breakdown & confirmation)
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton, Divider } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { colors, spacing, typography, borderRadius } from '../../theme';
import { RootStackParamList, TransferQuote } from '../../types';
import { getQuoteById } from '../../services/transfer';
import {
  formatCurrency,
  formatPercentage,
  formatRate,
  formatDelivery,
} from '../../utils/formatting';
import FeeBreakdown from '../../components/send/FeeBreakdown';
import MatchStatus from '../../components/send/MatchStatus';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';

type QuoteScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Quote'>;
  route: RouteProp<RootStackParamList, 'Quote'>;
};

// Mock quote for development
const MOCK_QUOTE: TransferQuote = {
  id: 'q_mock',
  sendAmount: 500,
  sendCurrency: 'USD',
  receiveAmount: 41350,
  receiveCurrency: 'INR',
  exchangeRate: 83.12,
  matchedAmount: 410,
  matchedPercentage: 82,
  unmatchedAmount: 90,
  matchedFee: 0,
  unmatchedFee: 0.18,
  platformFee: 0,
  totalFee: 0.18,
  totalFeePercentage: 0.036,
  estimatedDelivery: new Date(Date.now() + 1800000).toISOString(),
  expiresAt: new Date(Date.now() + 120000).toISOString(),
  competitorComparison: [
    { name: 'Wise', fee: 3.25, rate: 82.87, savings: 3.07 },
    { name: 'Western Union', fee: 12.49, rate: 81.35, savings: 12.31 },
    { name: 'Remitly', fee: 6.99, rate: 82.56, savings: 6.81 },
  ],
};

const QuoteScreen: React.FC<QuoteScreenProps> = ({ navigation, route }) => {
  const { quoteId } = route.params;
  const [quote, setQuote] = useState<TransferQuote>(MOCK_QUOTE);
  const [expirySeconds, setExpirySeconds] = useState(120);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadQuote = async () => {
      try {
        const data = await getQuoteById(quoteId);
        setQuote(data);
      } catch {
        // Use mock data
      }
    };
    loadQuote();
  }, [quoteId]);

  // Countdown timer for quote expiry
  useEffect(() => {
    const timer = setInterval(() => {
      setExpirySeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatExpiry = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSelectRecipient = () => {
    navigation.navigate('Confirm', { quoteId: quote.id, recipientId: 'r1' });
  };

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
        <Text style={styles.headerTitle}>Review Quote</Text>
        <View style={styles.expiryBadge}>
          <Icon name="clock-outline" size={14} color={expirySeconds < 30 ? colors.error : colors.textSecondary} />
          <Text
            style={[
              styles.expiryText,
              expirySeconds < 30 && { color: colors.error },
            ]}
          >
            {formatExpiry(expirySeconds)}
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Transfer Summary Card */}
        <Card variant="elevated" padding="large" style={styles.summaryCard}>
          <View style={styles.amountSection}>
            <View style={styles.amountBlock}>
              <Text style={styles.amountLabel}>You send</Text>
              <Text style={styles.amountValue}>
                {formatCurrency(quote.sendAmount, quote.sendCurrency)}
              </Text>
              <Text style={styles.amountCurrency}>{quote.sendCurrency}</Text>
            </View>

            <View style={styles.arrowContainer}>
              <View style={styles.arrowCircle}>
                <Icon name="arrow-right" size={20} color={colors.primary} />
              </View>
              <Text style={styles.rateText}>
                1 {quote.sendCurrency} = {formatRate(quote.exchangeRate)} {quote.receiveCurrency}
              </Text>
            </View>

            <View style={[styles.amountBlock, { alignItems: 'flex-end' }]}>
              <Text style={styles.amountLabel}>They receive</Text>
              <Text style={[styles.amountValue, { color: colors.secondary }]}>
                {formatCurrency(quote.receiveAmount, quote.receiveCurrency)}
              </Text>
              <Text style={styles.amountCurrency}>{quote.receiveCurrency}</Text>
            </View>
          </View>
        </Card>

        {/* Match Status */}
        <View style={styles.section}>
          <MatchStatus matchedPercentage={quote.matchedPercentage} />
        </View>

        {/* Fee Breakdown */}
        <View style={styles.section}>
          <FeeBreakdown quote={quote} />
        </View>

        {/* Delivery Info */}
        <Card variant="outlined" padding="medium" style={styles.section}>
          <View style={styles.infoRow}>
            <View style={styles.infoItem}>
              <Icon name="clock-fast" size={20} color={colors.primary} />
              <Text style={styles.infoLabel}>Delivery</Text>
              <Text style={styles.infoValue}>
                {formatDelivery(quote.estimatedDelivery)}
              </Text>
            </View>
            <View style={styles.infoDivider} />
            <View style={styles.infoItem}>
              <Icon name="shield-check" size={20} color={colors.secondary} />
              <Text style={styles.infoLabel}>Security</Text>
              <Text style={styles.infoValue}>On-chain</Text>
            </View>
            <View style={styles.infoDivider} />
            <View style={styles.infoItem}>
              <Icon name="swap-horizontal" size={20} color={colors.matchGreen} />
              <Text style={styles.infoLabel}>Match</Text>
              <Text style={styles.infoValue}>
                {formatPercentage(quote.matchedPercentage, 0)}
              </Text>
            </View>
          </View>
        </Card>

        {/* Transparent pricing notice */}
        <Card variant="highlight" padding="small" style={styles.section}>
          <View style={styles.noticeRow}>
            <Icon name="information-outline" size={18} color={colors.primary} />
            <Text style={styles.noticeText}>
              We use the mid-market exchange rate. No hidden markups or spreads. The only
              fee is on the {formatPercentage(100 - quote.matchedPercentage, 0)} that goes
              through liquidity pools.
            </Text>
          </View>
        </Card>

        <View style={{ height: 100 }} />
      </ScrollView>

      {/* Bottom CTA */}
      <View style={styles.bottomCta}>
        <Button
          title="Select Recipient & Continue"
          onPress={handleSelectRecipient}
          variant="primary"
          size="large"
          disabled={expirySeconds === 0}
          icon="account-arrow-right"
        />
        {expirySeconds === 0 && (
          <Button
            title="Refresh Quote"
            onPress={() => {
              setExpirySeconds(120);
              // Re-fetch quote
            }}
            variant="outline"
            size="medium"
            style={{ marginTop: spacing.sm }}
          />
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
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
  expiryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceVariant,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.round,
    marginRight: spacing.sm,
  },
  expiryText: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.xxl,
    paddingTop: spacing.xl,
  },
  summaryCard: {
    marginBottom: spacing.lg,
  },
  amountSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  amountBlock: {},
  amountLabel: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  amountValue: {
    ...typography.displaySmall,
    color: colors.text,
  },
  amountCurrency: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginTop: 2,
  },
  arrowContainer: {
    alignItems: 'center',
  },
  arrowCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primaryBg,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  rateText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    textAlign: 'center',
    maxWidth: 100,
  },
  section: {
    marginBottom: spacing.lg,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  infoItem: {
    flex: 1,
    alignItems: 'center',
  },
  infoLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginTop: spacing.xs,
  },
  infoValue: {
    ...typography.labelLarge,
    color: colors.text,
    marginTop: 2,
  },
  infoDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.border,
  },
  noticeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: spacing.sm,
  },
  noticeText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
    flex: 1,
    lineHeight: 18,
  },
  bottomCta: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.xxl,
    paddingVertical: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});

export default QuoteScreen;
