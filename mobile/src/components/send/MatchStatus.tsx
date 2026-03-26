// ============================================================
// Ha_Chain - Match Status Component (Animated matching display)
// ============================================================

import React, { useEffect, useRef } from 'react';
import { StyleSheet, View, Text, Animated, Easing } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing, typography, borderRadius } from '../../theme';
import { formatPercentage } from '../../utils/formatting';

interface MatchStatusProps {
  matchedPercentage: number;
  isSearching?: boolean;
  estimatedTime?: string;
}

const MatchStatus: React.FC<MatchStatusProps> = ({
  matchedPercentage,
  isSearching = false,
  estimatedTime,
}) => {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const progressAnim = useRef(new Animated.Value(0)).current;
  const spinAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Animate the progress bar to the matched percentage
    Animated.timing(progressAnim, {
      toValue: matchedPercentage / 100,
      duration: 1200,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [matchedPercentage]);

  useEffect(() => {
    if (isSearching) {
      // Pulse animation for searching state
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.1,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ]),
      );

      // Spin animation for the search icon
      const spin = Animated.loop(
        Animated.timing(spinAnim, {
          toValue: 1,
          duration: 2000,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
      );

      pulse.start();
      spin.start();

      return () => {
        pulse.stop();
        spin.stop();
      };
    }
  }, [isSearching]);

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0%', '100%'],
  });

  const spinRotation = spinAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const getStatusMessage = (): string => {
    if (isSearching) return 'Finding your match...';
    if (matchedPercentage >= 100) return 'Fully matched!';
    if (matchedPercentage >= 70) return 'Great match found!';
    if (matchedPercentage >= 40) return 'Partial match found';
    return 'Searching for matches...';
  };

  const getStatusColor = (): string => {
    if (matchedPercentage >= 80) return colors.matchGreen;
    if (matchedPercentage >= 50) return colors.primary;
    return colors.accent;
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Animated.View
          style={[
            styles.iconContainer,
            { backgroundColor: getStatusColor() + '20' },
            isSearching && { transform: [{ scale: pulseAnim }] },
          ]}
        >
          {isSearching ? (
            <Animated.View style={{ transform: [{ rotate: spinRotation }] }}>
              <Icon name="magnify" size={24} color={getStatusColor()} />
            </Animated.View>
          ) : (
            <Icon
              name={matchedPercentage >= 100 ? 'check-circle' : 'swap-horizontal'}
              size={24}
              color={getStatusColor()}
            />
          )}
        </Animated.View>
        <View style={styles.statusInfo}>
          <Text style={styles.statusMessage}>{getStatusMessage()}</Text>
          {estimatedTime && isSearching && (
            <Text style={styles.estimatedTime}>Est. {estimatedTime}</Text>
          )}
        </View>
        <Text style={[styles.percentage, { color: getStatusColor() }]}>
          {formatPercentage(matchedPercentage, 0)}
        </Text>
      </View>

      {/* Progress bar */}
      <View style={styles.progressTrack}>
        <Animated.View
          style={[
            styles.progressFill,
            {
              width: progressWidth,
              backgroundColor: getStatusColor(),
            },
          ]}
        />
        {/* Divider mark between matched and unmatched */}
        {matchedPercentage > 0 && matchedPercentage < 100 && (
          <Animated.View
            style={[
              styles.progressDivider,
              { left: progressWidth },
            ]}
          />
        )}
      </View>

      {/* Labels beneath the bar */}
      <View style={styles.legendRow}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: getStatusColor() }]} />
          <Text style={styles.legendText}>
            Matched ({formatPercentage(matchedPercentage, 0)}) - FREE
          </Text>
        </View>
        {matchedPercentage < 100 && (
          <View style={styles.legendItem}>
            <View style={[styles.legendDot, { backgroundColor: colors.accent }]} />
            <Text style={styles.legendText}>
              Liquidity ({formatPercentage(100 - matchedPercentage, 0)}) - 0.2%
            </Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  statusInfo: {
    flex: 1,
  },
  statusMessage: {
    ...typography.labelLarge,
    color: colors.text,
  },
  estimatedTime: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
  percentage: {
    ...typography.headlineLarge,
  },
  progressTrack: {
    height: 10,
    backgroundColor: colors.surfaceVariant,
    borderRadius: 5,
    overflow: 'hidden',
    position: 'relative',
  },
  progressFill: {
    height: '100%',
    borderRadius: 5,
  },
  progressDivider: {
    position: 'absolute',
    top: -2,
    width: 3,
    height: 14,
    backgroundColor: colors.surface,
    borderRadius: 1.5,
  },
  legendRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.md,
    flexWrap: 'wrap',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: spacing.md,
    marginBottom: spacing.xs,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: spacing.xs,
  },
  legendText: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
});

export default MatchStatus;
