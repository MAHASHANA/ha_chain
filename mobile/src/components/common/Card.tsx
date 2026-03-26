// ============================================================
// Ha_Chain - Reusable Card Component
// ============================================================

import React, { ReactNode } from 'react';
import { StyleSheet, View, ViewStyle, TouchableOpacity } from 'react-native';
import { colors, borderRadius, spacing, shadows } from '../../theme';

interface CardProps {
  children: ReactNode;
  variant?: 'default' | 'elevated' | 'outlined' | 'highlight';
  padding?: 'none' | 'small' | 'medium' | 'large';
  onPress?: () => void;
  style?: ViewStyle;
}

const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  padding = 'medium',
  onPress,
  style,
}) => {
  const getVariantStyle = (): ViewStyle => {
    switch (variant) {
      case 'elevated':
        return { ...shadows.medium, backgroundColor: colors.surface };
      case 'outlined':
        return { borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface };
      case 'highlight':
        return { backgroundColor: colors.primaryBg, borderWidth: 1, borderColor: colors.primaryLight };
      default:
        return { ...shadows.small, backgroundColor: colors.surface };
    }
  };

  const getPaddingStyle = (): ViewStyle => {
    switch (padding) {
      case 'none':
        return { padding: 0 };
      case 'small':
        return { padding: spacing.md };
      case 'medium':
        return { padding: spacing.lg };
      case 'large':
        return { padding: spacing.xxl };
      default:
        return { padding: spacing.lg };
    }
  };

  const cardStyle = [styles.base, getVariantStyle(), getPaddingStyle(), style];

  if (onPress) {
    return (
      <TouchableOpacity activeOpacity={0.7} onPress={onPress} style={cardStyle}>
        {children}
      </TouchableOpacity>
    );
  }

  return <View style={cardStyle}>{children}</View>;
};

const styles = StyleSheet.create({
  base: {
    borderRadius: borderRadius.lg,
    overflow: 'hidden',
  },
});

export default Card;
