// ============================================================
// Ha_Chain - Home Screen (THE DASHBOARD)
// Balance, Send button, Recent Transfers, Pool Stats
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Badge, Avatar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { RootStackParamList, WalletInfo, Transfer, PoolStats, CurrencyCode } from '../../types';
import { useAuth } from '../../store/AuthContext';
import { getWallet, getTransferHistory, getPoolStats } from '../../services/transfer';
import { formatCurrency, formatTimeAgo, formatPercentage, abbreviateNumber } from '../../utils/formatting';
import BalanceCard from '../../components/home/BalanceCard';
import QuickActions from '../../components/home/QuickActions';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';

type HomeScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'MainTabs'>;
};

// Mock data for initial development
const MOCK_WALLET: WalletInfo = {
  balances: [
    { currency: 'USD', available: 2450.0, pending: 150.0, total: 2600.0 },
    { currency: 'USDC', available: 500.0, pending: 0, total: 500.0 },
    { currency: 'EUR', available: 320.0, pending: 0, total: 320.0 },
  ],
  usdcBalance: 500.0,
  totalValueUSD: 3420.0,
  walletAddress: '0x1234...5678',
};

const MOCK_TRANSFERS: Transfer[] = [
  {
    id: 't1',
    status: 'completed',
    sendAmount: 500,
    sendCurrency: 'USD',
    receiveAmount: 41500,
    receiveCurrency: 'INR',
    exchangeRate: 83.0,
    totalFee: 0.45,
    matchedPercentage: 92,
    recipient: {
      id: 'r1',
      firstName: 'Priya',
      lastName: 'Sharma',
      phone: '+919876543210',
      country: 'IN',
      currency: 'INR',
      deliveryMethod: 'bank_transfer',
      isSaved: true,
    },
    deliveryMethod: 'bank_transfer',
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    estimatedDelivery: new Date(Date.now() + 1800000).toISOString(),
  },
  {
    id: 't2',
    status: 'processing',
    sendAmount: 200,
    sendCurrency: 'USD',
    receiveAmount: 11400,
    receiveCurrency: 'PHP',
    exchangeRate: 57.0,
    totalFee: 0.22,
    matchedPercentage: 78,
    recipient: {
      id: 'r2',
      firstName: 'Maria',
      lastName: 'Santos',
      phone: '+639123456789',
      country: 'PH',
      currency: 'PHP',
      deliveryMethod: 'mobile_money',
      isSaved: true,
    },
    deliveryMethod: 'mobile_money',
    createdAt: new Date(Date.now() - 7200000).toISOString(),
    estimatedDelivery: new Date(Date.now() + 3600000).toISOString(),
  },
  {
    id: 't3',
    status: 'completed',
    sendAmount: 1000,
    sendCurrency: 'USD',
    receiveAmount: 950000,
    receiveCurrency: 'NGN',
    exchangeRate: 950.0,
    totalFee: 1.2,
    matchedPercentage: 100,
    recipient: {
      id: 'r3',
      firstName: 'Chidi',
      lastName: 'Okafor',
      phone: '+2348012345678',
      country: 'NG',
      currency: 'NGN',
      deliveryMethod: 'bank_transfer',
      isSaved: true,
    },
    deliveryMethod: 'bank_transfer',
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    completedAt: new Date(Date.now() - 82800000).toISOString(),
    estimatedDelivery: new Date(Date.now() - 82800000).toISOString(),
  },
];

const MOCK_POOL_STATS: PoolStats = {
  totalVolume24h: 2850000,
  totalMatches24h: 4230,
  averageMatchTime: 45,
  currencyPools: [
    { currency: 'USD', totalAvailable: 450000, orderCount: 892, averageOrderSize: 504, matchRate: 87 },
    { currency: 'INR', totalAvailable: 32000000, orderCount: 1240, averageOrderSize: 25806, matchRate: 91 },
    { currency: 'NGN', totalAvailable: 180000000, orderCount: 634, averageOrderSize: 283911, matchRate: 82 },
  ],
  recentMatches: [
    { id: 'm1', fromCurrency: 'USD', toCurrency: 'INR', amount: 750, matchedAt: new Date(Date.now() - 30000).toISOString(), timeAgo: '30s ago' },
    { id: 'm2', fromCurrency: 'GBP', toCurrency: 'NGN', amount: 1200, matchedAt: new Date(Date.now() - 120000).toISOString(), timeAgo: '2m ago' },
    { id: 'm3', fromCurrency: 'EUR', toCurrency: 'PHP', amount: 300, matchedAt: new Date(Date.now() - 300000).toISOString(), timeAgo: '5m ago' },
  ],
};

const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const { user } = useAuth();
  const [wallet, setWallet] = useState<WalletInfo>(MOCK_WALLET);
  const [recentTransfers, setRecentTransfers] = useState<Transfer[]>(MOCK_TRANSFERS);
  const [poolStats, setPoolStats] = useState<PoolStats>(MOCK_POOL_STATS);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [walletData, transferData, poolData] = await Promise.allSettled([
        getWallet(),
        getTransferHistory(1, 5),
        getPoolStats(),
      ]);

      if (walletData.status === 'fulfilled') setWallet(walletData.value);
      if (transferData.status === 'fulfilled') setRecentTransfers(transferData.value.items);
      if (poolData.status === 'fulfilled') setPoolStats(poolData.value);
    } catch {
      // Use mock data on failure (already set as defaults)
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, [loadData]);

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return colors.secondary;
      case 'processing':
      case 'matching':
      case 'sending':
        return colors.primary;
      case 'failed':
        return colors.error;
      default:
        return colors.accent;
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'completed':
        return 'check-circle';
      case 'processing':
      case 'sending':
        return 'progress-clock';
      case 'matching':
        return 'swap-horizontal';
      case 'failed':
        return 'alert-circle';
      default:
        return 'clock-outline';
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.greeting}>
            Hello, {user?.firstName || 'there'}
          </Text>
          <Text style={styles.subGreeting}>Welcome back</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity style={styles.notificationButton}>
            <Icon name="bell-outline" size={24} color={colors.text} />
            <Badge style={styles.badge} size={8} />
          </TouchableOpacity>
          <Avatar.Text
            size={40}
            label={(user?.firstName?.[0] || 'U') + (user?.lastName?.[0] || '')}
            style={styles.avatar}
            labelStyle={styles.avatarLabel}
          />
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />
        }
      >
        {/* Balance Card */}
        <BalanceCard wallet={wallet} />

        {/* Quick Actions */}
        <QuickActions
          onSend={() => navigation.navigate('Send')}
          onPool={() => navigation.navigate('PoolStatus')}
          onInvest={() => navigation.navigate('Assets')}
          onMore={() => {}}
        />

        {/* Send Money CTA */}
        <Card variant="highlight" padding="medium" style={styles.sendCta}>
          <View style={styles.sendCtaContent}>
            <View style={styles.sendCtaLeft}>
              <Text style={styles.sendCtaTitle}>Send money now</Text>
              <Text style={styles.sendCtaSubtitle}>
                Average match rate: {formatPercentage(poolStats.currencyPools[0]?.matchRate || 85)}
              </Text>
            </View>
            <Button
              title="Send"
              onPress={() => navigation.navigate('Send')}
              variant="primary"
              size="small"
              fullWidth={false}
              icon="send"
            />
          </View>
        </Card>

        {/* Live Pool Stats */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Live Pool Activity</Text>
          <TouchableOpacity onPress={() => navigation.navigate('PoolStatus')}>
            <Text style={styles.sectionLink}>See All</Text>
          </TouchableOpacity>
        </View>

        <Card variant="default" padding="medium" style={styles.poolCard}>
          <View style={styles.poolStatsRow}>
            <View style={styles.poolStat}>
              <Text style={styles.poolStatValue}>
                ${abbreviateNumber(poolStats.totalVolume24h)}
              </Text>
              <Text style={styles.poolStatLabel}>24h Volume</Text>
            </View>
            <View style={styles.poolStatDivider} />
            <View style={styles.poolStat}>
              <Text style={styles.poolStatValue}>
                {abbreviateNumber(poolStats.totalMatches24h)}
              </Text>
              <Text style={styles.poolStatLabel}>Matches</Text>
            </View>
            <View style={styles.poolStatDivider} />
            <View style={styles.poolStat}>
              <Text style={styles.poolStatValue}>{poolStats.averageMatchTime}s</Text>
              <Text style={styles.poolStatLabel}>Avg Match</Text>
            </View>
          </View>

          {/* Recent Matches */}
          <View style={styles.recentMatchesHeader}>
            <View style={styles.liveDot} />
            <Text style={styles.recentMatchesTitle}>Recent Matches</Text>
          </View>
          {poolStats.recentMatches.slice(0, 3).map((match) => (
            <View key={match.id} style={styles.matchRow}>
              <Icon name="swap-horizontal" size={16} color={colors.matchGreen} />
              <Text style={styles.matchText}>
                {match.fromCurrency} → {match.toCurrency}
              </Text>
              <Text style={styles.matchAmount}>${match.amount}</Text>
              <Text style={styles.matchTime}>{match.timeAgo}</Text>
            </View>
          ))}
        </Card>

        {/* Recent Transfers */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Transfers</Text>
          <TouchableOpacity>
            <Text style={styles.sectionLink}>View All</Text>
          </TouchableOpacity>
        </View>

        {recentTransfers.length === 0 ? (
          <Card variant="outlined" padding="large">
            <View style={styles.emptyState}>
              <Icon name="send-outline" size={48} color={colors.textTertiary} />
              <Text style={styles.emptyTitle}>No transfers yet</Text>
              <Text style={styles.emptySubtitle}>
                Send money to someone and it will appear here
              </Text>
              <Button
                title="Send Your First Transfer"
                onPress={() => navigation.navigate('Send')}
                variant="primary"
                size="medium"
                fullWidth={false}
                style={styles.emptyButton}
              />
            </View>
          </Card>
        ) : (
          recentTransfers.map((transfer) => (
            <Card
              key={transfer.id}
              variant="default"
              padding="medium"
              style={styles.transferCard}
              onPress={() => navigation.navigate('Success', { transferId: transfer.id })}
            >
              <View style={styles.transferRow}>
                <View style={styles.transferLeft}>
                  <View
                    style={[
                      styles.transferIcon,
                      { backgroundColor: getStatusColor(transfer.status) + '15' },
                    ]}
                  >
                    <Icon
                      name={getStatusIcon(transfer.status)}
                      size={22}
                      color={getStatusColor(transfer.status)}
                    />
                  </View>
                  <View style={styles.transferInfo}>
                    <Text style={styles.transferName}>
                      {transfer.recipient.firstName} {transfer.recipient.lastName}
                    </Text>
                    <Text style={styles.transferMeta}>
                      {transfer.sendCurrency} → {transfer.receiveCurrency}
                      {'  '}
                      <Text style={{ color: getStatusColor(transfer.status) }}>
                        {transfer.status.charAt(0).toUpperCase() + transfer.status.slice(1)}
                      </Text>
                    </Text>
                  </View>
                </View>
                <View style={styles.transferRight}>
                  <Text style={styles.transferAmount}>
                    -{formatCurrency(transfer.sendAmount, transfer.sendCurrency)}
                  </Text>
                  <Text style={styles.transferReceive}>
                    +{formatCurrency(transfer.receiveAmount, transfer.receiveCurrency)}
                  </Text>
                  <Text style={styles.transferTime}>
                    {formatTimeAgo(transfer.createdAt)}
                  </Text>
                </View>
              </View>

              {/* Match percentage indicator */}
              <View style={styles.matchIndicator}>
                <View style={styles.matchBar}>
                  <View
                    style={[
                      styles.matchBarFill,
                      { width: `${transfer.matchedPercentage}%` },
                    ]}
                  />
                </View>
                <Text style={styles.matchLabel}>
                  {transfer.matchedPercentage}% matched
                </Text>
              </View>
            </Card>
          ))
        )}

        {/* Bottom spacer */}
        <View style={{ height: spacing.huge }} />
      </ScrollView>
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
    paddingHorizontal: spacing.xxl,
    paddingVertical: spacing.lg,
  },
  headerLeft: {},
  greeting: {
    ...typography.headlineLarge,
    color: colors.text,
  },
  subGreeting: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginTop: 2,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  notificationButton: {
    marginRight: spacing.md,
    position: 'relative',
  },
  badge: {
    position: 'absolute',
    top: -2,
    right: -2,
    backgroundColor: colors.error,
  },
  avatar: {
    backgroundColor: colors.primaryLight,
  },
  avatarLabel: {
    ...typography.labelLarge,
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.xxl,
  },
  sendCta: {
    marginBottom: spacing.lg,
  },
  sendCtaContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sendCtaLeft: {
    flex: 1,
    marginRight: spacing.md,
  },
  sendCtaTitle: {
    ...typography.headlineSmall,
    color: colors.primary,
  },
  sendCtaSubtitle: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.xl,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...typography.headlineMedium,
    color: colors.text,
  },
  sectionLink: {
    ...typography.labelLarge,
    color: colors.primary,
  },
  poolCard: {
    marginBottom: spacing.sm,
  },
  poolStatsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  poolStat: {
    flex: 1,
    alignItems: 'center',
  },
  poolStatValue: {
    ...typography.headlineMedium,
    color: colors.text,
  },
  poolStatLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  poolStatDivider: {
    width: 1,
    height: 30,
    backgroundColor: colors.border,
  },
  recentMatchesHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.matchGreen,
    marginRight: spacing.sm,
  },
  recentMatchesTitle: {
    ...typography.labelMedium,
    color: colors.textSecondary,
  },
  matchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  matchText: {
    ...typography.bodyMedium,
    color: colors.text,
    marginLeft: spacing.sm,
    flex: 1,
  },
  matchAmount: {
    ...typography.labelMedium,
    color: colors.text,
    marginRight: spacing.md,
  },
  matchTime: {
    ...typography.bodySmall,
    color: colors.textTertiary,
    minWidth: 50,
    textAlign: 'right',
  },
  transferCard: {
    marginBottom: spacing.md,
  },
  transferRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  transferLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  transferIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  transferInfo: {
    flex: 1,
  },
  transferName: {
    ...typography.labelLarge,
    color: colors.text,
  },
  transferMeta: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  transferRight: {
    alignItems: 'flex-end',
  },
  transferAmount: {
    ...typography.labelLarge,
    color: colors.text,
  },
  transferReceive: {
    ...typography.bodySmall,
    color: colors.secondary,
    marginTop: 2,
  },
  transferTime: {
    ...typography.bodySmall,
    color: colors.textTertiary,
    marginTop: 2,
  },
  matchIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
  },
  matchBar: {
    flex: 1,
    height: 4,
    backgroundColor: colors.surfaceVariant,
    borderRadius: 2,
    marginRight: spacing.sm,
    overflow: 'hidden',
  },
  matchBarFill: {
    height: '100%',
    backgroundColor: colors.matchGreen,
    borderRadius: 2,
  },
  matchLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    minWidth: 80,
    textAlign: 'right',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: spacing.xxl,
  },
  emptyTitle: {
    ...typography.headlineSmall,
    color: colors.text,
    marginTop: spacing.lg,
  },
  emptySubtitle: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.sm,
    marginBottom: spacing.xl,
  },
  emptyButton: {
    marginTop: spacing.sm,
  },
});

export default HomeScreen;
