// ============================================================
// Ha_Chain - Pool Status Screen (Live matching pool visualization)
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  RefreshControl,
  StatusBar,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton, ProgressBar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { RootStackParamList, PoolStats, CurrencyPool, RecentMatch } from '../../types';
import { getPoolStats } from '../../services/transfer';
import { formatCurrency, abbreviateNumber, formatPercentage } from '../../utils/formatting';
import { getCurrency } from '../../utils/constants';
import Card from '../../components/common/Card';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

type PoolStatusScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'PoolStatus'>;
};

const MOCK_POOL_STATS: PoolStats = {
  totalVolume24h: 2850000,
  totalMatches24h: 4230,
  averageMatchTime: 45,
  currencyPools: [
    { currency: 'USD', totalAvailable: 450000, orderCount: 892, averageOrderSize: 504, matchRate: 87 },
    { currency: 'INR', totalAvailable: 37350000, orderCount: 1240, averageOrderSize: 30121, matchRate: 91 },
    { currency: 'NGN', totalAvailable: 425000000, orderCount: 634, averageOrderSize: 670347, matchRate: 82 },
    { currency: 'PHP', totalAvailable: 12500000, orderCount: 380, averageOrderSize: 32894, matchRate: 78 },
    { currency: 'GBP', totalAvailable: 180000, orderCount: 312, averageOrderSize: 577, matchRate: 89 },
    { currency: 'EUR', totalAvailable: 220000, orderCount: 445, averageOrderSize: 494, matchRate: 86 },
    { currency: 'KES', totalAvailable: 45000000, orderCount: 287, averageOrderSize: 156794, matchRate: 74 },
    { currency: 'BDT', totalAvailable: 28000000, orderCount: 195, averageOrderSize: 143589, matchRate: 71 },
  ],
  recentMatches: [
    { id: 'm1', fromCurrency: 'USD', toCurrency: 'INR', amount: 750, matchedAt: new Date(Date.now() - 15000).toISOString(), timeAgo: '15s ago' },
    { id: 'm2', fromCurrency: 'GBP', toCurrency: 'NGN', amount: 1200, matchedAt: new Date(Date.now() - 45000).toISOString(), timeAgo: '45s ago' },
    { id: 'm3', fromCurrency: 'EUR', toCurrency: 'PHP', amount: 300, matchedAt: new Date(Date.now() - 90000).toISOString(), timeAgo: '1m ago' },
    { id: 'm4', fromCurrency: 'USD', toCurrency: 'KES', amount: 500, matchedAt: new Date(Date.now() - 120000).toISOString(), timeAgo: '2m ago' },
    { id: 'm5', fromCurrency: 'USD', toCurrency: 'BDT', amount: 400, matchedAt: new Date(Date.now() - 180000).toISOString(), timeAgo: '3m ago' },
    { id: 'm6', fromCurrency: 'GBP', toCurrency: 'INR', amount: 850, matchedAt: new Date(Date.now() - 240000).toISOString(), timeAgo: '4m ago' },
    { id: 'm7', fromCurrency: 'EUR', toCurrency: 'NGN', amount: 2000, matchedAt: new Date(Date.now() - 300000).toISOString(), timeAgo: '5m ago' },
  ],
};

const PoolStatusScreen: React.FC<PoolStatusScreenProps> = ({ navigation }) => {
  const [poolStats, setPoolStats] = useState<PoolStats>(MOCK_POOL_STATS);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const data = await getPoolStats();
      setPoolStats(data);
    } catch {
      // Use mock data
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

  const getPoolBarWidth = (pool: CurrencyPool): number => {
    const maxAvailable = Math.max(...poolStats.currencyPools.map(p => p.totalAvailable));
    return (pool.totalAvailable / maxAvailable) * 100;
  };

  const getMatchRateColor = (rate: number): string => {
    if (rate >= 85) return colors.matchGreen;
    if (rate >= 70) return colors.primary;
    if (rate >= 50) return colors.accent;
    return colors.error;
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
        <Text style={styles.headerTitle}>Matching Pool</Text>
        <View style={styles.liveBadge}>
          <View style={styles.liveDot} />
          <Text style={styles.liveText}>Live</Text>
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
        {/* Overview Stats */}
        <View style={styles.overviewRow}>
          <Card variant="elevated" padding="medium" style={styles.overviewCard}>
            <Icon name="chart-bar" size={24} color={colors.primary} />
            <Text style={styles.overviewValue}>
              ${abbreviateNumber(poolStats.totalVolume24h)}
            </Text>
            <Text style={styles.overviewLabel}>24h Volume</Text>
          </Card>
          <Card variant="elevated" padding="medium" style={styles.overviewCard}>
            <Icon name="swap-horizontal-circle" size={24} color={colors.matchGreen} />
            <Text style={styles.overviewValue}>
              {abbreviateNumber(poolStats.totalMatches24h)}
            </Text>
            <Text style={styles.overviewLabel}>Matches</Text>
          </Card>
          <Card variant="elevated" padding="medium" style={styles.overviewCard}>
            <Icon name="clock-fast" size={24} color={colors.accent} />
            <Text style={styles.overviewValue}>{poolStats.averageMatchTime}s</Text>
            <Text style={styles.overviewLabel}>Avg Time</Text>
          </Card>
        </View>

        {/* Currency Pools */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Currency Pools</Text>
          <Text style={styles.sectionSubtitle}>Liquidity available for matching</Text>
        </View>

        {poolStats.currencyPools.map((pool) => {
          const currency = getCurrency(pool.currency);
          return (
            <Card key={pool.currency} variant="default" padding="medium" style={styles.poolCard}>
              <View style={styles.poolHeader}>
                <View style={styles.poolCurrency}>
                  <Text style={styles.poolFlag}>{currency?.flag}</Text>
                  <View>
                    <Text style={styles.poolCode}>{pool.currency}</Text>
                    <Text style={styles.poolName}>{currency?.name}</Text>
                  </View>
                </View>
                <View style={styles.poolMatchRate}>
                  <Text
                    style={[
                      styles.poolMatchRateValue,
                      { color: getMatchRateColor(pool.matchRate) },
                    ]}
                  >
                    {formatPercentage(pool.matchRate, 0)}
                  </Text>
                  <Text style={styles.poolMatchRateLabel}>match rate</Text>
                </View>
              </View>

              {/* Pool bar visualization */}
              <View style={styles.poolBarContainer}>
                <View style={styles.poolBarTrack}>
                  <View
                    style={[
                      styles.poolBarFill,
                      {
                        width: `${getPoolBarWidth(pool)}%`,
                        backgroundColor: getMatchRateColor(pool.matchRate),
                      },
                    ]}
                  />
                </View>
              </View>

              <View style={styles.poolStats}>
                <View style={styles.poolStatItem}>
                  <Text style={styles.poolStatValue}>
                    {formatCurrency(pool.totalAvailable, pool.currency, { compact: true })}
                  </Text>
                  <Text style={styles.poolStatLabel}>Available</Text>
                </View>
                <View style={styles.poolStatItem}>
                  <Text style={styles.poolStatValue}>{pool.orderCount}</Text>
                  <Text style={styles.poolStatLabel}>Orders</Text>
                </View>
                <View style={styles.poolStatItem}>
                  <Text style={styles.poolStatValue}>
                    {formatCurrency(pool.averageOrderSize, pool.currency, { compact: true })}
                  </Text>
                  <Text style={styles.poolStatLabel}>Avg Size</Text>
                </View>
              </View>
            </Card>
          );
        })}

        {/* Recent Matches - Live Feed */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionTitleRow}>
            <View style={styles.liveDotSmall} />
            <Text style={styles.sectionTitle}>Live Match Feed</Text>
          </View>
          <Text style={styles.sectionSubtitle}>Real-time peer matches</Text>
        </View>

        <Card variant="default" padding="medium">
          {poolStats.recentMatches.map((match, index) => (
            <View key={match.id}>
              <View style={styles.matchRow}>
                <View style={styles.matchIcon}>
                  <Icon name="swap-horizontal" size={18} color={colors.matchGreen} />
                </View>
                <View style={styles.matchInfo}>
                  <Text style={styles.matchPair}>
                    {match.fromCurrency} → {match.toCurrency}
                  </Text>
                  <Text style={styles.matchTime}>{match.timeAgo}</Text>
                </View>
                <Text style={styles.matchAmount}>
                  ${match.amount.toLocaleString()}
                </Text>
              </View>
              {index < poolStats.recentMatches.length - 1 && (
                <View style={styles.matchDivider} />
              )}
            </View>
          ))}
        </Card>

        {/* How it works */}
        <Card variant="highlight" padding="medium" style={styles.howItWorks}>
          <Text style={styles.howItWorksTitle}>How Matching Works</Text>
          <View style={styles.howStep}>
            <View style={[styles.howStepDot, { backgroundColor: colors.primary }]}>
              <Text style={styles.howStepNum}>1</Text>
            </View>
            <Text style={styles.howStepText}>
              You want to send USD → INR. Someone in India wants to send INR → USD.
            </Text>
          </View>
          <View style={styles.howStep}>
            <View style={[styles.howStepDot, { backgroundColor: colors.matchGreen }]}>
              <Text style={styles.howStepNum}>2</Text>
            </View>
            <Text style={styles.howStepText}>
              Ha_Chain matches you both. Each person receives their local currency - no
              international transfer needed.
            </Text>
          </View>
          <View style={styles.howStep}>
            <View style={[styles.howStepDot, { backgroundColor: colors.accent }]}>
              <Text style={styles.howStepNum}>3</Text>
            </View>
            <Text style={styles.howStepText}>
              The matched portion is FREE. Any unmatched remainder goes through a
              liquidity pool at just 0.2%.
            </Text>
          </View>
        </Card>

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
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderLight,
  },
  headerTitle: {
    ...typography.headlineMedium,
    color: colors.text,
  },
  liveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.secondaryBg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.round,
    marginRight: spacing.sm,
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.matchGreen,
    marginRight: spacing.xs,
  },
  liveText: {
    ...typography.labelSmall,
    color: colors.secondary,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.xxl,
    paddingTop: spacing.xl,
  },
  overviewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xl,
  },
  overviewCard: {
    flex: 1,
    marginHorizontal: spacing.xs,
    alignItems: 'center',
  },
  overviewValue: {
    ...typography.headlineMedium,
    color: colors.text,
    marginTop: spacing.sm,
  },
  overviewLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  sectionHeader: {
    marginBottom: spacing.md,
    marginTop: spacing.lg,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sectionTitle: {
    ...typography.headlineMedium,
    color: colors.text,
  },
  sectionSubtitle: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  liveDotSmall: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.matchGreen,
    marginRight: spacing.sm,
  },
  poolCard: {
    marginBottom: spacing.md,
  },
  poolHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  poolCurrency: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  poolFlag: {
    fontSize: 24,
    marginRight: spacing.md,
  },
  poolCode: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  poolName: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
  poolMatchRate: {
    alignItems: 'flex-end',
  },
  poolMatchRateValue: {
    ...typography.headlineMedium,
  },
  poolMatchRateLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
  },
  poolBarContainer: {
    marginBottom: spacing.md,
  },
  poolBarTrack: {
    height: 8,
    backgroundColor: colors.surfaceVariant,
    borderRadius: 4,
    overflow: 'hidden',
  },
  poolBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  poolStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  poolStatItem: {
    alignItems: 'center',
  },
  poolStatValue: {
    ...typography.labelLarge,
    color: colors.text,
  },
  poolStatLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  matchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  matchIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.secondaryBg,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  matchInfo: {
    flex: 1,
  },
  matchPair: {
    ...typography.labelLarge,
    color: colors.text,
  },
  matchTime: {
    ...typography.bodySmall,
    color: colors.textTertiary,
    marginTop: 2,
  },
  matchAmount: {
    ...typography.labelLarge,
    color: colors.text,
  },
  matchDivider: {
    height: 1,
    backgroundColor: colors.borderLight,
    marginVertical: spacing.xs,
  },
  howItWorks: {
    marginTop: spacing.xl,
  },
  howItWorksTitle: {
    ...typography.headlineSmall,
    color: colors.primary,
    marginBottom: spacing.lg,
  },
  howStep: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  howStepDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
    marginTop: 2,
  },
  howStepNum: {
    ...typography.labelSmall,
    color: '#FFFFFF',
  },
  howStepText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    flex: 1,
    lineHeight: 20,
  },
});

export default PoolStatusScreen;
