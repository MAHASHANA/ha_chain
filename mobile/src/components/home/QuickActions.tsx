// ============================================================
// Ha_Chain - Quick Actions Component
// ============================================================

import React from 'react';
import { StyleSheet, View, Text, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';

interface QuickAction {
  icon: string;
  label: string;
  color: string;
  bgColor: string;
  onPress: () => void;
}

interface QuickActionsProps {
  onSend: () => void;
  onPool: () => void;
  onInvest: () => void;
  onMore: () => void;
}

const QuickActions: React.FC<QuickActionsProps> = ({
  onSend,
  onPool,
  onInvest,
  onMore,
}) => {
  const actions: QuickAction[] = [
    {
      icon: 'send',
      label: 'Send',
      color: colors.primary,
      bgColor: colors.primaryBg,
      onPress: onSend,
    },
    {
      icon: 'swap-horizontal-circle',
      label: 'Pool',
      color: colors.poolBlue,
      bgColor: '#ECFEFF',
      onPress: onPool,
    },
    {
      icon: 'chart-line',
      label: 'Invest',
      color: colors.secondary,
      bgColor: colors.secondaryBg,
      onPress: onInvest,
    },
    {
      icon: 'dots-horizontal-circle',
      label: 'More',
      color: colors.matchPurple,
      bgColor: '#F5F3FF',
      onPress: onMore,
    },
  ];

  return (
    <View style={styles.container}>
      {actions.map((action, index) => (
        <TouchableOpacity
          key={index}
          style={styles.actionItem}
          onPress={action.onPress}
          activeOpacity={0.7}
        >
          <View style={[styles.iconContainer, { backgroundColor: action.bgColor }]}>
            <Icon name={action.icon} size={26} color={action.color} />
          </View>
          <Text style={styles.label}>{action.label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: spacing.lg,
  },
  actionItem: {
    alignItems: 'center',
    minWidth: 70,
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: borderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
    ...shadows.small,
  },
  label: {
    ...typography.labelMedium,
    color: colors.text,
  },
});

export default QuickActions;
