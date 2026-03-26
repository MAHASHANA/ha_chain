// ============================================================
// Ha_Chain - Reusable Button Component
// ============================================================

import React from 'react';
import { StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { Button as PaperButton } from 'react-native-paper';
import { colors, borderRadius, typography } from '../../theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  fullWidth?: boolean;
  style?: ViewStyle;
  labelStyle?: TextStyle;
}

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  icon,
  fullWidth = true,
  style,
  labelStyle,
}) => {
  const getMode = (): 'contained' | 'outlined' | 'text' => {
    switch (variant) {
      case 'primary':
      case 'secondary':
        return 'contained';
      case 'outline':
        return 'outlined';
      case 'ghost':
        return 'text';
      default:
        return 'contained';
    }
  };

  const getButtonColor = (): string => {
    switch (variant) {
      case 'primary':
        return colors.primary;
      case 'secondary':
        return colors.secondary;
      case 'outline':
        return colors.surface;
      case 'ghost':
        return 'transparent';
      default:
        return colors.primary;
    }
  };

  const getTextColor = (): string => {
    switch (variant) {
      case 'primary':
      case 'secondary':
        return colors.textInverse;
      case 'outline':
        return colors.primary;
      case 'ghost':
        return colors.primary;
      default:
        return colors.textInverse;
    }
  };

  const getSizeStyle = (): ViewStyle => {
    switch (size) {
      case 'small':
        return { paddingVertical: 2 };
      case 'medium':
        return { paddingVertical: 6 };
      case 'large':
        return { paddingVertical: 10 };
      default:
        return { paddingVertical: 6 };
    }
  };

  const getLabelSize = (): TextStyle => {
    switch (size) {
      case 'small':
        return { fontSize: 13, fontWeight: '600' };
      case 'medium':
        return { fontSize: 15, fontWeight: '600' };
      case 'large':
        return { fontSize: 17, fontWeight: '700' };
      default:
        return { fontSize: 15, fontWeight: '600' };
    }
  };

  return (
    <PaperButton
      mode={getMode()}
      onPress={onPress}
      disabled={disabled}
      loading={loading}
      icon={icon}
      buttonColor={getButtonColor()}
      textColor={getTextColor()}
      contentStyle={[getSizeStyle(), !fullWidth && styles.fitContent]}
      labelStyle={[getLabelSize(), labelStyle]}
      style={[
        styles.base,
        variant === 'outline' && styles.outlined,
        fullWidth && styles.fullWidth,
        style,
      ]}
    >
      {title}
    </PaperButton>
  );
};

const styles = StyleSheet.create({
  base: {
    borderRadius: borderRadius.md,
  },
  outlined: {
    borderColor: colors.primary,
    borderWidth: 1.5,
  },
  fullWidth: {
    width: '100%',
  },
  fitContent: {
    alignSelf: 'flex-start',
  },
});

export default Button;
