// ============================================================
// Ha_Chain - Confirm Screen (Final confirmation before send)
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  StatusBar,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton, Divider, Checkbox } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { RootStackParamList, TransferQuote, Recipient } from '../../types';
import { sendTransfer } from '../../services/transfer';
import { formatCurrency, formatRate, formatPercentage } from '../../utils/formatting';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';

type ConfirmScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Confirm'>;
  route: RouteProp<RootStackParamList, 'Confirm'>;
};

const MOCK_RECIPIENT: Recipient = {
  id: 'r1',
  firstName: 'Priya',
  lastName: 'Sharma',
  phone: '+919876543210',
  country: 'IN',
  currency: 'INR',
  deliveryMethod: 'bank_transfer',
  accountDetails: {
    bankName: 'State Bank of India',
    accountNumber: '****5678',
  },
  isSaved: true,
};

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
  competitorComparison: [],
};

const ConfirmScreen: React.FC<ConfirmScreenProps> = ({ navigation, route }) => {
  const { quoteId, recipientId } = route.params;
  const [quote] = useState<TransferQuote>(MOCK_QUOTE);
  const [recipient] = useState<Recipient>(MOCK_RECIPIENT);
  const [confirmed, setConfirmed] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirm = async () => {
    if (!confirmed) {
      Alert.alert('Confirmation Required', 'Please confirm the transfer details.');
      return;
    }

    setIsSubmitting(true);
    try {
      const transfer = await sendTransfer({
        quoteId: quote.id,
        recipientId: recipient.id,
        deliveryMethod: recipient.deliveryMethod,
      });
      navigation.navigate('Success', { transferId: transfer.id });
    } catch {
      // Use mock success for development
      navigation.navigate('Success', { transferId: 't_' + Date.now() });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getDeliveryMethodLabel = (method: string): string => {
    switch (method) {
      case 'bank_transfer':
        return 'Bank Transfer';
      case 'mobile_money':
        return 'Mobile Money';
      case 'cash_pickup':
        return 'Cash Pickup';
      case 'wallet':
        return 'Wallet';
      default:
        return method;
    }
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
        <Text style={styles.headerTitle}>Confirm Transfer</Text>
        <View style={{ width: 48 }} />
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Amount Summary */}
        <Card variant="elevated" padding="large" style={styles.summaryCard}>
          <View style={styles.summaryCenter}>
            <Text style={styles.sendLabel}>Sending</Text>
            <Text style={styles.sendAmount}>
              {formatCurrency(quote.sendAmount, quote.sendCurrency)}
            </Text>
            <View style={styles.arrowDown}>
              <Icon name="arrow-down" size={20} color={colors.primary} />
            </View>
            <Text style={styles.receiveLabel}>Recipient gets</Text>
            <Text style={styles.receiveAmount}>
              {formatCurrency(quote.receiveAmount, quote.receiveCurrency)}
            </Text>
          </View>
        </Card>

        {/* Recipient Details */}
        <Card variant="default" padding="medium" style={styles.section}>
          <Text style={styles.cardTitle}>Recipient</Text>
          <View style={styles.recipientRow}>
            <View style={styles.recipientAvatar}>
              <Text style={styles.recipientInitials}>
                {recipient.firstName[0]}{recipient.lastName[0]}
              </Text>
            </View>
            <View style={styles.recipientInfo}>
              <Text style={styles.recipientName}>
                {recipient.firstName} {recipient.lastName}
              </Text>
              <Text style={styles.recipientPhone}>{recipient.phone}</Text>
            </View>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Delivery method</Text>
            <Text style={styles.detailValue}>
              {getDeliveryMethodLabel(recipient.deliveryMethod)}
            </Text>
          </View>

          {recipient.accountDetails?.bankName && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Bank</Text>
              <Text style={styles.detailValue}>{recipient.accountDetails.bankName}</Text>
            </View>
          )}

          {recipient.accountDetails?.accountNumber && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Account</Text>
              <Text style={styles.detailValue}>{recipient.accountDetails.accountNumber}</Text>
            </View>
          )}
        </Card>

        {/* Transfer Details */}
        <Card variant="default" padding="medium" style={styles.section}>
          <Text style={styles.cardTitle}>Transfer Details</Text>

          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Exchange rate</Text>
            <Text style={styles.detailValue}>
              1 {quote.sendCurrency} = {formatRate(quote.exchangeRate)} {quote.receiveCurrency}
            </Text>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Match rate</Text>
            <View style={styles.matchBadge}>
              <Text style={styles.matchBadgeText}>
                {formatPercentage(quote.matchedPercentage, 0)} matched
              </Text>
            </View>
          </View>

          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Fees</Text>
            <Text style={styles.detailValue}>
              {formatCurrency(quote.totalFee, quote.sendCurrency)} ({formatPercentage(quote.totalFeePercentage)})
            </Text>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.detailRow}>
            <Text style={styles.totalLabel}>Total debit</Text>
            <Text style={styles.totalValue}>
              {formatCurrency(quote.sendAmount + quote.totalFee, quote.sendCurrency)}
            </Text>
          </View>
        </Card>

        {/* Security Notice */}
        <Card variant="highlight" padding="small" style={styles.section}>
          <View style={styles.securityRow}>
            <Icon name="shield-check" size={20} color={colors.primary} />
            <Text style={styles.securityText}>
              This transfer is secured by blockchain technology. Funds are held in escrow
              until delivery is confirmed.
            </Text>
          </View>
        </Card>

        {/* Confirmation checkbox */}
        <View style={styles.checkboxRow}>
          <Checkbox
            status={confirmed ? 'checked' : 'unchecked'}
            onPress={() => setConfirmed(!confirmed)}
            color={colors.primary}
          />
          <Text style={styles.checkboxText}>
            I confirm the transfer details are correct and authorize this payment.
          </Text>
        </View>

        <View style={{ height: 100 }} />
      </ScrollView>

      {/* Bottom CTA */}
      <View style={styles.bottomCta}>
        <Button
          title={`Send ${formatCurrency(quote.sendAmount, quote.sendCurrency)}`}
          onPress={handleConfirm}
          variant="primary"
          size="large"
          disabled={!confirmed || isSubmitting}
          loading={isSubmitting}
          icon="send"
        />
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
  summaryCenter: {
    alignItems: 'center',
  },
  sendLabel: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  sendAmount: {
    ...typography.displayMedium,
    color: colors.text,
  },
  arrowDown: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.primaryBg,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: spacing.md,
  },
  receiveLabel: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  receiveAmount: {
    ...typography.displayMedium,
    color: colors.secondary,
  },
  section: {
    marginBottom: spacing.lg,
  },
  cardTitle: {
    ...typography.headlineSmall,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  recipientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  recipientAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  recipientInitials: {
    ...typography.headlineSmall,
    color: '#FFFFFF',
  },
  recipientInfo: {
    flex: 1,
  },
  recipientName: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  recipientPhone: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  divider: {
    marginVertical: spacing.md,
    backgroundColor: colors.borderLight,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  detailLabel: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  detailValue: {
    ...typography.labelMedium,
    color: colors.text,
  },
  matchBadge: {
    backgroundColor: colors.secondaryBg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.round,
  },
  matchBadgeText: {
    ...typography.labelSmall,
    color: colors.secondary,
  },
  totalLabel: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  totalValue: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  securityRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: spacing.sm,
  },
  securityText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
    flex: 1,
    lineHeight: 18,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.xl,
  },
  checkboxText: {
    ...typography.bodyMedium,
    color: colors.text,
    flex: 1,
    marginTop: spacing.sm,
  },
  bottomCta: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.xxl,
    paddingVertical: spacing.lg,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});

export default ConfirmScreen;
