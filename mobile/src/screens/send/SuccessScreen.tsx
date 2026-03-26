// ============================================================
// Ha_Chain - Success Screen (Transfer complete with tracking)
// ============================================================

import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  StatusBar,
  Animated,
  Easing,
  Share,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Divider } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { RootStackParamList, Transfer } from '../../types';
import { getTransfer } from '../../services/transfer';
import { formatCurrency, formatPercentage, formatTimeAgo } from '../../utils/formatting';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';

type SuccessScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Success'>;
  route: RouteProp<RootStackParamList, 'Success'>;
};

const MOCK_TRANSFER: Transfer = {
  id: 't_mock',
  status: 'processing',
  sendAmount: 500,
  sendCurrency: 'USD',
  receiveAmount: 41350,
  receiveCurrency: 'INR',
  exchangeRate: 83.12,
  totalFee: 0.18,
  matchedPercentage: 82,
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
  matchDetails: {
    matchId: 'm_123',
    matchedWithUserId: 'u_456',
    matchedAmount: 410,
    matchedAt: new Date().toISOString(),
    isFullMatch: false,
  },
  createdAt: new Date().toISOString(),
  estimatedDelivery: new Date(Date.now() + 1800000).toISOString(),
  blockchainTxHash: '0xabc123def456...789',
};

const TRACKING_STEPS = [
  { id: 'submitted', label: 'Transfer Submitted', icon: 'check-circle', completed: true },
  { id: 'matched', label: 'Peer Matched (82%)', icon: 'swap-horizontal', completed: true },
  { id: 'processing', label: 'Processing', icon: 'progress-clock', completed: true, active: true },
  { id: 'sending', label: 'Sending to Recipient', icon: 'bank-transfer', completed: false },
  { id: 'completed', label: 'Delivered', icon: 'check-all', completed: false },
];

const SuccessScreen: React.FC<SuccessScreenProps> = ({ navigation, route }) => {
  const { transferId } = route.params;
  const [transfer, setTransfer] = useState<Transfer>(MOCK_TRANSFER);

  // Animations
  const checkScale = useRef(new Animated.Value(0)).current;
  const fadeIn = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Animated entry
    Animated.sequence([
      Animated.spring(checkScale, {
        toValue: 1,
        friction: 4,
        tension: 40,
        useNativeDriver: true,
      }),
      Animated.timing(fadeIn, {
        toValue: 1,
        duration: 500,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    ]).start();

    // Load real transfer data
    const loadTransfer = async () => {
      try {
        const data = await getTransfer(transferId);
        setTransfer(data);
      } catch {
        // Use mock data
      }
    };
    loadTransfer();
  }, [transferId]);

  const handleShare = async () => {
    try {
      await Share.share({
        message: `I just sent ${formatCurrency(transfer.sendAmount, transfer.sendCurrency)} to ${
          transfer.recipient.firstName
        } via Ha_Chain with only ${formatCurrency(
          transfer.totalFee,
          transfer.sendCurrency,
        )} in fees! ${transfer.matchedPercentage}% was peer-matched for FREE.`,
      });
    } catch {
      // Share cancelled
    }
  };

  const handleDone = () => {
    navigation.popToTop();
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Success Animation */}
        <View style={styles.successHeader}>
          <Animated.View
            style={[
              styles.checkCircle,
              { transform: [{ scale: checkScale }] },
            ]}
          >
            <Icon name="check" size={48} color="#FFFFFF" />
          </Animated.View>
          <Text style={styles.successTitle}>Transfer Initiated!</Text>
          <Text style={styles.successSubtitle}>
            Your money is on its way to {transfer.recipient.firstName}
          </Text>
        </View>

        <Animated.View style={{ opacity: fadeIn }}>
          {/* Amount Card */}
          <Card variant="elevated" padding="large" style={styles.amountCard}>
            <View style={styles.amountRow}>
              <View>
                <Text style={styles.amountLabel}>Sent</Text>
                <Text style={styles.amountSend}>
                  {formatCurrency(transfer.sendAmount, transfer.sendCurrency)}
                </Text>
              </View>
              <Icon name="arrow-right" size={24} color={colors.textTertiary} />
              <View style={{ alignItems: 'flex-end' }}>
                <Text style={styles.amountLabel}>Receiving</Text>
                <Text style={styles.amountReceive}>
                  {formatCurrency(transfer.receiveAmount, transfer.receiveCurrency)}
                </Text>
              </View>
            </View>

            <Divider style={styles.divider} />

            <View style={styles.feeSavingsRow}>
              <View style={styles.feeSavingsItem}>
                <Text style={styles.feeSavingsLabel}>Total Fee</Text>
                <Text style={styles.feeSavingsValue}>
                  {formatCurrency(transfer.totalFee, transfer.sendCurrency)}
                </Text>
              </View>
              <View style={styles.feeSavingsItem}>
                <Text style={styles.feeSavingsLabel}>Matched</Text>
                <Text style={[styles.feeSavingsValue, { color: colors.secondary }]}>
                  {formatPercentage(transfer.matchedPercentage, 0)}
                </Text>
              </View>
            </View>
          </Card>

          {/* Tracking Steps */}
          <Card variant="default" padding="medium" style={styles.trackingCard}>
            <Text style={styles.trackingTitle}>Transfer Tracking</Text>
            {TRACKING_STEPS.map((step, index) => (
              <View key={step.id} style={styles.trackingStep}>
                <View style={styles.trackingTimeline}>
                  <View
                    style={[
                      styles.trackingDot,
                      step.completed && styles.trackingDotCompleted,
                      step.active && styles.trackingDotActive,
                    ]}
                  >
                    {step.completed && (
                      <Icon
                        name="check"
                        size={12}
                        color={step.active ? colors.primary : '#FFFFFF'}
                      />
                    )}
                  </View>
                  {index < TRACKING_STEPS.length - 1 && (
                    <View
                      style={[
                        styles.trackingLine,
                        step.completed && styles.trackingLineCompleted,
                      ]}
                    />
                  )}
                </View>
                <View style={styles.trackingContent}>
                  <View style={styles.trackingRow}>
                    <Icon
                      name={step.icon}
                      size={18}
                      color={
                        step.active
                          ? colors.primary
                          : step.completed
                          ? colors.secondary
                          : colors.textTertiary
                      }
                    />
                    <Text
                      style={[
                        styles.trackingLabel,
                        step.active && styles.trackingLabelActive,
                        !step.completed && !step.active && styles.trackingLabelPending,
                      ]}
                    >
                      {step.label}
                    </Text>
                  </View>
                  {step.active && (
                    <Text style={styles.trackingStatus}>In progress...</Text>
                  )}
                </View>
              </View>
            ))}
          </Card>

          {/* Blockchain Reference */}
          {transfer.blockchainTxHash && (
            <Card variant="outlined" padding="small" style={styles.txCard}>
              <View style={styles.txRow}>
                <Icon name="link-variant" size={18} color={colors.matchPurple} />
                <View style={styles.txInfo}>
                  <Text style={styles.txLabel}>Blockchain TX</Text>
                  <Text style={styles.txHash}>{transfer.blockchainTxHash}</Text>
                </View>
                <Icon name="open-in-new" size={16} color={colors.textTertiary} />
              </View>
            </Card>
          )}

          {/* Actions */}
          <View style={styles.actionsSection}>
            <Button
              title="Share Transfer"
              onPress={handleShare}
              variant="outline"
              size="medium"
              icon="share-variant"
            />
            <View style={{ height: spacing.md }} />
            <Button
              title="Send Another"
              onPress={() => navigation.navigate('Send')}
              variant="secondary"
              size="medium"
              icon="send"
            />
            <View style={{ height: spacing.md }} />
            <Button
              title="Back to Home"
              onPress={handleDone}
              variant="primary"
              size="large"
            />
          </View>
        </Animated.View>

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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.xxl,
    paddingTop: spacing.xxxl,
  },
  successHeader: {
    alignItems: 'center',
    marginBottom: spacing.xxxl,
  },
  checkCircle: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: colors.secondary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xl,
    ...shadows.large,
  },
  successTitle: {
    ...typography.displaySmall,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  successSubtitle: {
    ...typography.bodyLarge,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  amountCard: {
    marginBottom: spacing.lg,
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  amountLabel: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  amountSend: {
    ...typography.headlineLarge,
    color: colors.text,
  },
  amountReceive: {
    ...typography.headlineLarge,
    color: colors.secondary,
  },
  divider: {
    marginVertical: spacing.lg,
    backgroundColor: colors.borderLight,
  },
  feeSavingsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  feeSavingsItem: {
    alignItems: 'center',
  },
  feeSavingsLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
    marginBottom: spacing.xs,
  },
  feeSavingsValue: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  trackingCard: {
    marginBottom: spacing.lg,
  },
  trackingTitle: {
    ...typography.headlineSmall,
    color: colors.text,
    marginBottom: spacing.lg,
  },
  trackingStep: {
    flexDirection: 'row',
    minHeight: 50,
  },
  trackingTimeline: {
    alignItems: 'center',
    width: 24,
    marginRight: spacing.md,
  },
  trackingDot: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: colors.surfaceVariant,
    borderWidth: 2,
    borderColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackingDotCompleted: {
    backgroundColor: colors.secondary,
    borderColor: colors.secondary,
  },
  trackingDotActive: {
    backgroundColor: colors.primaryBg,
    borderColor: colors.primary,
    borderWidth: 3,
  },
  trackingLine: {
    flex: 1,
    width: 2,
    backgroundColor: colors.border,
    marginVertical: 2,
  },
  trackingLineCompleted: {
    backgroundColor: colors.secondary,
  },
  trackingContent: {
    flex: 1,
    paddingBottom: spacing.md,
  },
  trackingRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  trackingLabel: {
    ...typography.labelLarge,
    color: colors.text,
    marginLeft: spacing.sm,
  },
  trackingLabelActive: {
    color: colors.primary,
  },
  trackingLabelPending: {
    color: colors.textTertiary,
  },
  trackingStatus: {
    ...typography.bodySmall,
    color: colors.primary,
    marginLeft: spacing.sm + 18,
    marginTop: 2,
  },
  txCard: {
    marginBottom: spacing.lg,
  },
  txRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.sm,
  },
  txInfo: {
    flex: 1,
    marginLeft: spacing.sm,
  },
  txLabel: {
    ...typography.labelSmall,
    color: colors.textSecondary,
  },
  txHash: {
    ...typography.bodySmall,
    color: colors.matchPurple,
    marginTop: 2,
  },
  actionsSection: {
    marginTop: spacing.lg,
  },
});

export default SuccessScreen;
