// ============================================================
// Ha_Chain - Portfolio Screen (User investment positions)
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  RefreshControl,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton, Divider } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { RootStackParamList, Portfolio, Investment } from '../../types';
import { getPortfolio } from '../../services/transfer';
import { formatCurrency, formatPercentage } from '../../utils/formatting';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';

type PortfolioScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Portfolio'>;
};

const MOCK_PORTFOLIO: Portfolio = {
  totalInvested: 5250,
  currentValue: 5680,
  totalReturn: 430,
  totalReturnPercentage: 8.19,
  investments: [
    {
      id: 'inv1',
      asset: {
        id: 'a1',
        name: 'US Treasury Bill 6-Month',
        description: 'Tokenized US Treasury Bill',
        assetType: 'bond',
        tokenSymbol: 'haTBILL',
        totalSupply: 10000000,
        pricePerToken: 1.0,
        currency: 'USD',
        apy: 5.2,
        riskLevel: 'low',
        minInvestment: 100,
        totalInvested: 4500000,
        investorCount: 2340,
      },
      tokensOwned: 2000,
      investedAmount: 2000,
      currentValue: 2052,
      returnAmount: 52,
      returnPercentage: 2.6,
      purchasedAt: new Date(Date.now() - 90 * 86400000).toISOString(),
    },
    {
      id: 'inv2',
      asset: {
        id: 'a4',
        name: 'Ha_Chain Liquidity Pool',
        description: 'Provide liquidity for transfers',
        assetType: 'liquidity_pool',
        tokenSymbol: 'haLP',
        totalSupply: 20000000,
        pricePerToken: 1.0,
        currency: 'USDC',
        apy: 12.4,
        riskLevel: 'medium',
        minInvestment: 50,
        totalInvested: 12000000,
        investorCount: 8930,
      },
      tokensOwned: 2000,
      investedAmount: 2000,
      currentValue: 2248,
      returnAmount: 248,
      returnPercentage: 12.4,
      purchasedAt: new Date(Date.now() - 180 * 86400000).toISOString(),
    },
    {
      id: 'inv3',
      asset: {
        id: 'a2',
        name: 'Gold Reserve Token',
        description: 'Tokenized gold reserves',
        assetType: 'commodity',
        tokenSymbol: 'haGOLD',
        totalSupply: 5000000,
        pricePerToken: 23.45,
        currency: 'USD',
        apy: 3.8,
        riskLevel: 'low',
        minInvestment: 50,
        totalInvested: 8200000,
        investorCount: 5620,
      },
      tokensOwned: 50,
      investedAmount: 1100,
      currentValue: 1172.5,
      returnAmount: 72.5,
      returnPercentage: 6.59,
      purchasedAt: new Date(Date.now() - 120 * 86400000).toISOString(),
    },
    {
      id: 'inv4',
      asset: {
        id: 'a5',
        name: 'East Africa Solar Infrastructure',
        description: 'Solar energy infrastructure',
        assetType: 'infrastructure',
        tokenSymbol: 'haSOLAR',
        totalSupply: 3000000,
        pricePerToken: 5.0,
        currency: 'USD',
        apy: 9.2,
        riskLevel: 'medium',
        minInvestment: 50,
        totalInvested: 3200000,
        investorCount: 1450,
      },
      tokensOwned: 30,
      investedAmount: 150,
      currentValue: 207.5,
      returnAmount: 57.5,
      returnPercentage: 38.3,
      purchasedAt: new Date(Date.now() - 365 * 86400000).toISOString(),
    },
  ],
};

const PortfolioScreen: React.FC<PortfolioScreenProps> = ({ navigation }) => {
  const [portfolio, setPortfolio] = useState<Portfolio>(MOCK_PORTFOLIO);
  const [refreshing, setRefreshing] = useState(false);

  const loadPortfolio = useCallback(async () => {
    try {
      const data = await getPortfolio();
      setPortfolio(data);
    } catch {
      // Use mock data
    }
  }, []);

  useEffect(() => {
    loadPortfolio();
  }, [loadPortfolio]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadPortfolio();
    setRefreshing(false);
  }, [loadPortfolio]);

  const getAssetIcon = (type: string): string => {
    switch (type) {
      case 'bond': return 'file-certificate';
      case 'commodity': return 'gold';
      case 'real_estate': return 'home-city';
      case 'liquidity_pool': return 'water';
      case 'infrastructure': return 'solar-panel';
      default: return 'chart-line';
    }
  };

  const getAssetColor = (type: string): string => {
    switch (type) {
      case 'bond': return colors.primary;
      case 'commodity': return colors.accent;
      case 'real_estate': return colors.matchPurple;
      case 'liquidity_pool': return colors.poolBlue;
      case 'infrastructure': return colors.secondary;
      default: return colors.primary;
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
        <Text style={styles.headerTitle}>Portfolio</Text>
        <View style={{ width: 48 }} />
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />
        }
      >
        {/* Portfolio Summary */}
        <Card variant="elevated" padding="large" style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>Portfolio Value</Text>
          <Text style={styles.summaryValue}>
            {formatCurrency(portfolio.currentValue, 'USD')}
          </Text>

          <View style={styles.returnRow}>
            <View
              style={[
                styles.returnBadge,
                {
                  backgroundColor:
                    portfolio.totalReturn >= 0 ? colors.secondaryBg : colors.errorBg,
                },
              ]}
            >
              <Icon
                name={portfolio.totalReturn >= 0 ? 'trending-up' : 'trending-down'}
                size={16}
                color={portfolio.totalReturn >= 0 ? colors.secondary : colors.error}
              />
              <Text
                style={[
                  styles.returnText,
                  {
                    color: portfolio.totalReturn >= 0 ? colors.secondary : colors.error,
                  },
                ]}
              >
                {portfolio.totalReturn >= 0 ? '+' : ''}
                {formatCurrency(portfolio.totalReturn, 'USD')} (
                {formatPercentage(portfolio.totalReturnPercentage)})
              </Text>
            </View>
          </View>

          <Divider style={styles.divider} />

          <View style={styles.summaryStats}>
            <View style={styles.summaryStat}>
              <Text style={styles.summaryStatLabel}>Invested</Text>
              <Text style={styles.summaryStatValue}>
                {formatCurrency(portfolio.totalInvested, 'USD')}
              </Text>
            </View>
            <View style={styles.summaryStat}>
              <Text style={styles.summaryStatLabel}>Assets</Text>
              <Text style={styles.summaryStatValue}>{portfolio.investments.length}</Text>
            </View>
          </View>
        </Card>

        {/* Investments */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Your Investments</Text>
        </View>

        {portfolio.investments.map((investment) => (
          <Card key={investment.id} variant="default" padding="medium" style={styles.investmentCard}>
            <View style={styles.investmentHeader}>
              <View
                style={[
                  styles.investmentIcon,
                  { backgroundColor: getAssetColor(investment.asset.assetType) + '15' },
                ]}
              >
                <Icon
                  name={getAssetIcon(investment.asset.assetType)}
                  size={22}
                  color={getAssetColor(investment.asset.assetType)}
                />
              </View>
              <View style={styles.investmentInfo}>
                <Text style={styles.investmentName} numberOfLines={1}>
                  {investment.asset.name}
                </Text>
                <Text style={styles.investmentSymbol}>
                  {investment.tokensOwned.toLocaleString()} {investment.asset.tokenSymbol}
                </Text>
              </View>
              <View style={styles.investmentReturn}>
                <Text style={styles.investmentValue}>
                  {formatCurrency(investment.currentValue, investment.asset.currency)}
                </Text>
                <Text
                  style={[
                    styles.investmentReturnPct,
                    {
                      color: investment.returnAmount >= 0 ? colors.secondary : colors.error,
                    },
                  ]}
                >
                  {investment.returnAmount >= 0 ? '+' : ''}
                  {formatPercentage(investment.returnPercentage)}
                </Text>
              </View>
            </View>

            {/* Simple allocation bar */}
            <View style={styles.allocationBar}>
              <View
                style={[
                  styles.allocationFill,
                  {
                    width: `${(investment.currentValue / portfolio.currentValue) * 100}%`,
                    backgroundColor: getAssetColor(investment.asset.assetType),
                  },
                ]}
              />
            </View>

            <View style={styles.investmentMeta}>
              <Text style={styles.investmentMetaText}>
                APY: {formatPercentage(investment.asset.apy)}
              </Text>
              <Text style={styles.investmentMetaText}>
                Return: {investment.returnAmount >= 0 ? '+' : ''}
                {formatCurrency(investment.returnAmount, investment.asset.currency)}
              </Text>
            </View>
          </Card>
        ))}

        {/* CTA */}
        <Button
          title="Browse More Assets"
          onPress={() => navigation.navigate('Assets')}
          variant="outline"
          size="medium"
          icon="plus"
          style={styles.browseButton}
        />

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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.xxl,
    paddingTop: spacing.xl,
  },
  summaryCard: {
    marginBottom: spacing.xl,
  },
  summaryLabel: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  summaryValue: {
    ...typography.displayLarge,
    color: colors.text,
  },
  returnRow: {
    marginTop: spacing.sm,
  },
  returnBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderRadius: borderRadius.round,
  },
  returnText: {
    ...typography.labelMedium,
    marginLeft: spacing.xs,
  },
  divider: {
    marginVertical: spacing.lg,
    backgroundColor: colors.borderLight,
  },
  summaryStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  summaryStat: {
    alignItems: 'center',
  },
  summaryStatLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  summaryStatValue: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  sectionHeader: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...typography.headlineMedium,
    color: colors.text,
  },
  investmentCard: {
    marginBottom: spacing.md,
  },
  investmentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  investmentIcon: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  investmentInfo: {
    flex: 1,
  },
  investmentName: {
    ...typography.labelLarge,
    color: colors.text,
  },
  investmentSymbol: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  investmentReturn: {
    alignItems: 'flex-end',
  },
  investmentValue: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  investmentReturnPct: {
    ...typography.labelMedium,
    marginTop: 2,
  },
  allocationBar: {
    height: 4,
    backgroundColor: colors.surfaceVariant,
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: spacing.sm,
  },
  allocationFill: {
    height: '100%',
    borderRadius: 2,
  },
  investmentMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  investmentMetaText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
  browseButton: {
    marginTop: spacing.lg,
  },
});

export default PortfolioScreen;
