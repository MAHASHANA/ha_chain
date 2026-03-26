// ============================================================
// Ha_Chain - Assets Screen (Browse tokenized assets)
// ============================================================

import React, { useState, useEffect, useCallback } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  RefreshControl,
  StatusBar,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton, Chip, Searchbar } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { RootStackParamList, TokenizedAsset, AssetType, RiskLevel } from '../../types';
import { getAssets } from '../../services/transfer';
import { formatCurrency, formatPercentage } from '../../utils/formatting';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';

type AssetsScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Assets'>;
};

const MOCK_ASSETS: TokenizedAsset[] = [
  {
    id: 'a1',
    name: 'US Treasury Bill 6-Month',
    description: 'Tokenized 6-month US Treasury Bill. Low risk, stable returns backed by US government.',
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
  {
    id: 'a2',
    name: 'Gold Reserve Token',
    description: 'Tokenized gold reserves stored in LBMA-approved vaults. Each token represents 0.01 oz of gold.',
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
  {
    id: 'a3',
    name: 'Nairobi Real Estate Fund',
    description: 'Fractional ownership in premium commercial real estate properties in Nairobi CBD.',
    assetType: 'real_estate',
    tokenSymbol: 'haNRE',
    totalSupply: 2000000,
    pricePerToken: 10.0,
    currency: 'USD',
    apy: 8.5,
    riskLevel: 'medium',
    minInvestment: 100,
    totalInvested: 1800000,
    investorCount: 890,
  },
  {
    id: 'a4',
    name: 'Ha_Chain Liquidity Pool',
    description: 'Provide liquidity to the Ha_Chain matching pool and earn fees from unmatched transfers.',
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
  {
    id: 'a5',
    name: 'East Africa Solar Infrastructure',
    description: 'Invest in solar energy infrastructure across Kenya, Tanzania, and Uganda. Impact investing.',
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
  {
    id: 'a6',
    name: 'Emerging Market Bond Index',
    description: 'Diversified exposure to government bonds from emerging market economies.',
    assetType: 'bond',
    tokenSymbol: 'haEMB',
    totalSupply: 8000000,
    pricePerToken: 1.0,
    currency: 'USD',
    apy: 7.1,
    riskLevel: 'medium',
    minInvestment: 100,
    totalInvested: 5600000,
    investorCount: 3210,
  },
];

type FilterType = 'all' | AssetType;

const FILTERS: { label: string; value: FilterType; icon: string }[] = [
  { label: 'All', value: 'all', icon: 'view-grid' },
  { label: 'Bonds', value: 'bond', icon: 'file-certificate' },
  { label: 'Gold & Commodities', value: 'commodity', icon: 'gold' },
  { label: 'Real Estate', value: 'real_estate', icon: 'home-city' },
  { label: 'Liquidity', value: 'liquidity_pool', icon: 'water' },
  { label: 'Infrastructure', value: 'infrastructure', icon: 'solar-panel' },
];

const AssetsScreen: React.FC<AssetsScreenProps> = ({ navigation }) => {
  const [assets, setAssets] = useState<TokenizedAsset[]>(MOCK_ASSETS);
  const [filter, setFilter] = useState<FilterType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const loadAssets = useCallback(async () => {
    try {
      const data = await getAssets();
      setAssets(data);
    } catch {
      // Use mock data
    }
  }, []);

  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAssets();
    setRefreshing(false);
  }, [loadAssets]);

  const filteredAssets = assets.filter((asset) => {
    const matchesFilter = filter === 'all' || asset.assetType === filter;
    const matchesSearch =
      searchQuery === '' ||
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.tokenSymbol.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getRiskColor = (risk: RiskLevel): string => {
    switch (risk) {
      case 'low':
        return colors.matchGreen;
      case 'medium':
        return colors.accent;
      case 'high':
        return colors.error;
    }
  };

  const getAssetIcon = (type: AssetType): string => {
    switch (type) {
      case 'bond':
        return 'file-certificate';
      case 'commodity':
        return 'gold';
      case 'real_estate':
        return 'home-city';
      case 'liquidity_pool':
        return 'water';
      case 'infrastructure':
        return 'solar-panel';
    }
  };

  const getAssetColor = (type: AssetType): string => {
    switch (type) {
      case 'bond':
        return colors.primary;
      case 'commodity':
        return colors.accent;
      case 'real_estate':
        return colors.matchPurple;
      case 'liquidity_pool':
        return colors.poolBlue;
      case 'infrastructure':
        return colors.secondary;
    }
  };

  const renderAssetCard = (asset: TokenizedAsset) => (
    <Card key={asset.id} variant="default" padding="medium" style={styles.assetCard}>
      <View style={styles.assetHeader}>
        <View
          style={[
            styles.assetIconContainer,
            { backgroundColor: getAssetColor(asset.assetType) + '15' },
          ]}
        >
          <Icon
            name={getAssetIcon(asset.assetType)}
            size={24}
            color={getAssetColor(asset.assetType)}
          />
        </View>
        <View style={styles.assetHeaderInfo}>
          <Text style={styles.assetName} numberOfLines={1}>
            {asset.name}
          </Text>
          <Text style={styles.assetSymbol}>{asset.tokenSymbol}</Text>
        </View>
        <View style={styles.apyBadge}>
          <Text style={styles.apyValue}>{formatPercentage(asset.apy)}</Text>
          <Text style={styles.apyLabel}>APY</Text>
        </View>
      </View>

      <Text style={styles.assetDescription} numberOfLines={2}>
        {asset.description}
      </Text>

      <View style={styles.assetStats}>
        <View style={styles.assetStat}>
          <Text style={styles.assetStatLabel}>Min invest</Text>
          <Text style={styles.assetStatValue}>
            {formatCurrency(asset.minInvestment, asset.currency)}
          </Text>
        </View>
        <View style={styles.assetStat}>
          <Text style={styles.assetStatLabel}>Total invested</Text>
          <Text style={styles.assetStatValue}>
            {formatCurrency(asset.totalInvested, asset.currency, { compact: true })}
          </Text>
        </View>
        <View style={styles.assetStat}>
          <Text style={styles.assetStatLabel}>Risk</Text>
          <View style={styles.riskBadge}>
            <View
              style={[styles.riskDot, { backgroundColor: getRiskColor(asset.riskLevel) }]}
            />
            <Text
              style={[styles.riskText, { color: getRiskColor(asset.riskLevel) }]}
            >
              {asset.riskLevel.charAt(0).toUpperCase() + asset.riskLevel.slice(1)}
            </Text>
          </View>
        </View>
      </View>

      <Button
        title="Invest Now"
        onPress={() => {}}
        variant="primary"
        size="small"
        style={styles.investButton}
      />
    </Card>
  );

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
        <Text style={styles.headerTitle}>Invest</Text>
        <IconButton
          icon="briefcase-outline"
          onPress={() => navigation.navigate('Portfolio')}
          iconColor={colors.text}
        />
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <Searchbar
          placeholder="Search assets..."
          onChangeText={setSearchQuery}
          value={searchQuery}
          style={styles.searchBar}
          inputStyle={styles.searchInput}
        />
      </View>

      {/* Filters */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterRow}
      >
        {FILTERS.map((f) => (
          <Chip
            key={f.value}
            selected={filter === f.value}
            onPress={() => setFilter(f.value)}
            style={[
              styles.filterChip,
              filter === f.value && styles.filterChipActive,
            ]}
            textStyle={[
              styles.filterChipText,
              filter === f.value && styles.filterChipTextActive,
            ]}
            icon={f.icon}
          >
            {f.label}
          </Chip>
        ))}
      </ScrollView>

      {/* Assets list */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[colors.primary]} />
        }
      >
        {filteredAssets.length === 0 ? (
          <View style={styles.emptyState}>
            <Icon name="magnify" size={48} color={colors.textTertiary} />
            <Text style={styles.emptyText}>No assets found</Text>
          </View>
        ) : (
          filteredAssets.map(renderAssetCard)
        )}
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
  searchContainer: {
    paddingHorizontal: spacing.xxl,
    paddingTop: spacing.md,
  },
  searchBar: {
    backgroundColor: colors.surfaceVariant,
    borderRadius: borderRadius.md,
    elevation: 0,
  },
  searchInput: {
    ...typography.bodyMedium,
  },
  filterRow: {
    paddingHorizontal: spacing.xxl,
    paddingVertical: spacing.md,
  },
  filterChip: {
    marginRight: spacing.sm,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  filterChipActive: {
    backgroundColor: colors.primaryBg,
    borderColor: colors.primary,
  },
  filterChipText: {
    ...typography.labelMedium,
    color: colors.textSecondary,
  },
  filterChipTextActive: {
    color: colors.primary,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.xxl,
  },
  assetCard: {
    marginBottom: spacing.md,
  },
  assetHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  assetIconContainer: {
    width: 48,
    height: 48,
    borderRadius: borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  assetHeaderInfo: {
    flex: 1,
  },
  assetName: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  assetSymbol: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  apyBadge: {
    alignItems: 'center',
    backgroundColor: colors.secondaryBg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.md,
  },
  apyValue: {
    ...typography.headlineSmall,
    color: colors.secondary,
  },
  apyLabel: {
    ...typography.labelSmall,
    color: colors.secondaryDark,
  },
  assetDescription: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    lineHeight: 20,
    marginBottom: spacing.md,
  },
  assetStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  assetStat: {
    alignItems: 'center',
  },
  assetStatLabel: {
    ...typography.labelSmall,
    color: colors.textTertiary,
    marginBottom: spacing.xs,
  },
  assetStatValue: {
    ...typography.labelLarge,
    color: colors.text,
  },
  riskBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  riskDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.xs,
  },
  riskText: {
    ...typography.labelMedium,
  },
  investButton: {
    marginTop: spacing.xs,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.huge,
  },
  emptyText: {
    ...typography.bodyLarge,
    color: colors.textTertiary,
    marginTop: spacing.md,
  },
});

export default AssetsScreen;
