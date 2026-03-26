// ============================================================
// Ha_Chain - Fee Breakdown Component
// Shows matched vs unmatched fees transparently
// ============================================================

import React from 'react';
import { StyleSheet, View, Text } from 'react-native';
import { Divider } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing, typography, borderRadius } from '../../theme';
import { TransferQuote, CurrencyCode } from '../../types';
import { formatCurrency, formatPercentage } from '../../utils/formatting';
import Card from '../common/Card';

interface FeeBreakdownProps {
  quote: TransferQuote;
}

const FeeBreakdown: React.FC<FeeBreakdownProps> = ({ quote }) => {
  return (
    <Card variant="outlined" padding="medium">
      <Text style={styles.title}>Fee Breakdown</Text>

      {/* Matched portion - FREE */}
      <View style={styles.feeRow}>
        <View style={styles.feeLeft}>
          <View style={[styles.dot, { backgroundColor: colors.matchGreen }]} />
          <View>
            <Text style={styles.feeLabel}>
              Matched ({formatPercentage(quote.matchedPercentage, 0)})
            </Text>
            <Text style={styles.feeDescription}>
              Peer-to-peer matched - no exchange needed
            </Text>
          </View>
        </View>
        <View style={styles.feeRight}>
          <Text style={styles.freeTag}>FREE</Text>
        </View>
      </View>

      {/* Unmatched portion */}
      {quote.unmatchedAmount > 0 && (
        <View style={styles.feeRow}>
          <View style={styles.feeLeft}>
            <View style={[styles.dot, { backgroundColor: colors.accent }]} />
            <View>
              <Text style={styles.feeLabel}>
                Liquidity ({formatPercentage(100 - quote.matchedPercentage, 0)})
              </Text>
              <Text style={styles.feeDescription}>
                {formatCurrency(quote.unmatchedAmount, quote.sendCurrency)} via liquidity pool
              </Text>
            </View>
          </View>
          <View style={styles.feeRight}>
            <Text style={styles.feeAmount}>
              {formatCurrency(quote.unmatchedFee, quote.sendCurrency)}
            </Text>
          </View>
        </View>
      )}

      {/* Platform fee */}
      {quote.platformFee > 0 && (
        <View style={styles.feeRow}>
          <View style={styles.feeLeft}>
            <View style={[styles.dot, { backgroundColor: colors.poolBlue }]} />
            <View>
              <Text style={styles.feeLabel}>Platform Fee</Text>
              <Text style={styles.feeDescription}>Ha_Chain service charge</Text>
            </View>
          </View>
          <View style={styles.feeRight}>
            <Text style={styles.feeAmount}>
              {formatCurrency(quote.platformFee, quote.sendCurrency)}
            </Text>
          </View>
        </View>
      )}

      <Divider style={styles.divider} />

      {/* Total */}
      <View style={styles.totalRow}>
        <Text style={styles.totalLabel}>Total Fees</Text>
        <View style={styles.totalRight}>
          <Text style={styles.totalAmount}>
            {formatCurrency(quote.totalFee, quote.sendCurrency)}
          </Text>
          <Text style={styles.totalPercentage}>
            ({formatPercentage(quote.totalFeePercentage)})
          </Text>
        </View>
      </View>

      {/* Competitor comparison */}
      {quote.competitorComparison.length > 0 && (
        <View style={styles.comparisonContainer}>
          <View style={styles.comparisonHeader}>
            <Icon name="trending-down" size={16} color={colors.secondary} />
            <Text style={styles.comparisonTitle}>You save compared to:</Text>
          </View>
          {quote.competitorComparison.map((comp, index) => (
            <View key={index} style={styles.comparisonRow}>
              <Text style={styles.comparisonName}>{comp.name}</Text>
              <Text style={styles.comparisonSavings}>
                Save {formatCurrency(comp.savings, quote.sendCurrency)}
              </Text>
            </View>
          ))}
        </View>
      )}
    </Card>
  );
};

const styles = StyleSheet.create({
  title: {
    ...typography.headlineSmall,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  feeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  feeLeft: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 6,
    marginRight: spacing.md,
  },
  feeLabel: {
    ...typography.labelLarge,
    color: colors.text,
  },
  feeDescription: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  feeRight: {
    alignItems: 'flex-end',
    marginLeft: spacing.md,
  },
  freeTag: {
    ...typography.labelLarge,
    color: colors.secondary,
    backgroundColor: colors.secondaryBg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.sm,
    overflow: 'hidden',
  },
  feeAmount: {
    ...typography.labelLarge,
    color: colors.text,
  },
  divider: {
    marginVertical: spacing.md,
    backgroundColor: colors.border,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  totalLabel: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  totalRight: {
    alignItems: 'flex-end',
  },
  totalAmount: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  totalPercentage: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  comparisonContainer: {
    marginTop: spacing.lg,
    backgroundColor: colors.secondaryBg,
    borderRadius: borderRadius.md,
    padding: spacing.md,
  },
  comparisonHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  comparisonTitle: {
    ...typography.labelMedium,
    color: colors.secondary,
    marginLeft: spacing.xs,
  },
  comparisonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  comparisonName: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  comparisonSavings: {
    ...typography.labelMedium,
    color: colors.secondary,
  },
});

export default FeeBreakdown;
