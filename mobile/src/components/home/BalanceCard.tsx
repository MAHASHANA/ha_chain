// ============================================================
// Ha_Chain - Balance Card Component
// ============================================================

import React, { useState } from 'react';
import { StyleSheet, View, Text, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { WalletInfo, CurrencyCode } from '../../types';
import { formatCurrency } from '../../utils/formatting';

interface BalanceCardProps {
  wallet: WalletInfo;
  onDeposit?: () => void;
  onWithdraw?: () => void;
}

const BalanceCard: React.FC<BalanceCardProps> = ({ wallet, onDeposit, onWithdraw }) => {
  const [balanceVisible, setBalanceVisible] = useState(true);

  const primaryBalance = wallet.balances.find(b => b.currency === 'USD') || wallet.balances[0];

  return (
    <View style={styles.container}>
      <View style={styles.gradient}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerLabel}>Total Balance</Text>
          <TouchableOpacity
            onPress={() => setBalanceVisible(!balanceVisible)}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Icon
              name={balanceVisible ? 'eye-outline' : 'eye-off-outline'}
              size={22}
              color="rgba(255,255,255,0.8)"
            />
          </TouchableOpacity>
        </View>

        {/* Main Balance */}
        <Text style={styles.balanceAmount}>
          {balanceVisible
            ? formatCurrency(wallet.totalValueUSD, 'USD')
            : '$ ****.**'}
        </Text>

        {/* USDC Balance */}
        {wallet.usdcBalance > 0 && (
          <View style={styles.usdcRow}>
            <Icon name="circle-multiple-outline" size={14} color="rgba(255,255,255,0.7)" />
            <Text style={styles.usdcLabel}>
              {balanceVisible
                ? `${wallet.usdcBalance.toLocaleString()} USDC on-chain`
                : '**** USDC on-chain'}
            </Text>
          </View>
        )}

        {/* Action buttons */}
        <View style={styles.actionsRow}>
          <TouchableOpacity style={styles.actionButton} onPress={onDeposit}>
            <View style={styles.actionIcon}>
              <Icon name="arrow-down" size={18} color={colors.primary} />
            </View>
            <Text style={styles.actionLabel}>Deposit</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={onWithdraw}>
            <View style={styles.actionIcon}>
              <Icon name="arrow-up" size={18} color={colors.primary} />
            </View>
            <Text style={styles.actionLabel}>Withdraw</Text>
          </TouchableOpacity>
        </View>

        {/* Multi-currency balances */}
        {wallet.balances.length > 1 && (
          <View style={styles.multiCurrencyRow}>
            {wallet.balances.slice(0, 3).map((balance) => (
              <View key={balance.currency} style={styles.currencyChip}>
                <Text style={styles.currencyChipText}>
                  {balance.currency}: {balanceVisible
                    ? formatCurrency(balance.available, balance.currency, { showSymbol: false, compact: true })
                    : '***'}
                </Text>
              </View>
            ))}
            {wallet.balances.length > 3 && (
              <View style={styles.currencyChip}>
                <Text style={styles.currencyChipText}>
                  +{wallet.balances.length - 3} more
                </Text>
              </View>
            )}
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: borderRadius.xl,
    overflow: 'hidden',
    ...shadows.large,
  },
  gradient: {
    backgroundColor: colors.primary,
    padding: spacing.xxl,
    borderRadius: borderRadius.xl,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  headerLabel: {
    ...typography.labelLarge,
    color: 'rgba(255,255,255,0.8)',
  },
  balanceAmount: {
    ...typography.displayLarge,
    color: '#FFFFFF',
    marginBottom: spacing.xs,
  },
  usdcRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  usdcLabel: {
    ...typography.bodySmall,
    color: 'rgba(255,255,255,0.7)',
    marginLeft: spacing.xs,
  },
  actionsRow: {
    flexDirection: 'row',
    marginBottom: spacing.lg,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: borderRadius.round,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    marginRight: spacing.md,
  },
  actionIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.sm,
  },
  actionLabel: {
    ...typography.labelMedium,
    color: '#FFFFFF',
  },
  multiCurrencyRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: spacing.sm,
  },
  currencyChip: {
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: borderRadius.round,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    marginRight: spacing.sm,
    marginBottom: spacing.xs,
  },
  currencyChipText: {
    ...typography.labelSmall,
    color: 'rgba(255,255,255,0.9)',
  },
});

export default BalanceCard;
