// ============================================================
// Ha_Chain - Amount Input Component
// ============================================================

import React, { useState } from 'react';
import { StyleSheet, View, TextInput, Text, ViewStyle } from 'react-native';
import { colors, spacing, typography, borderRadius } from '../../theme';
import { CurrencyCode } from '../../types';
import { getCurrency } from '../../utils/constants';

interface AmountInputProps {
  value: string;
  onChangeText: (text: string) => void;
  currency: CurrencyCode;
  label?: string;
  placeholder?: string;
  editable?: boolean;
  error?: string;
  style?: ViewStyle;
}

const AmountInput: React.FC<AmountInputProps> = ({
  value,
  onChangeText,
  currency,
  label,
  placeholder = '0.00',
  editable = true,
  error,
  style,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const currencyInfo = getCurrency(currency);

  const handleChange = (text: string) => {
    // Allow only valid numeric input with decimals
    const cleaned = text.replace(/[^0-9.]/g, '');
    // Prevent multiple decimal points
    const parts = cleaned.split('.');
    if (parts.length > 2) return;
    // Limit decimal places
    if (parts[1] && parts[1].length > (currencyInfo?.decimals ?? 2)) return;
    onChangeText(cleaned);
  };

  return (
    <View style={[styles.container, style]}>
      {label && <Text style={styles.label}>{label}</Text>}
      <View
        style={[
          styles.inputWrapper,
          isFocused && styles.inputFocused,
          error ? styles.inputError : null,
          !editable && styles.inputDisabled,
        ]}
      >
        <Text style={styles.currencySymbol}>{currencyInfo?.symbol || '$'}</Text>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={handleChange}
          placeholder={placeholder}
          placeholderTextColor={colors.textTertiary}
          keyboardType="decimal-pad"
          editable={editable}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          selectionColor={colors.primary}
        />
        <View style={styles.currencyBadge}>
          <Text style={styles.currencyFlag}>{currencyInfo?.flag}</Text>
          <Text style={styles.currencyCode}>{currency}</Text>
        </View>
      </View>
      {error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: spacing.lg,
  },
  label: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    minHeight: 60,
  },
  inputFocused: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryBg,
  },
  inputError: {
    borderColor: colors.error,
  },
  inputDisabled: {
    backgroundColor: colors.surfaceVariant,
    opacity: 0.8,
  },
  currencySymbol: {
    ...typography.amountSmall,
    color: colors.textSecondary,
    marginRight: spacing.xs,
  },
  input: {
    flex: 1,
    ...typography.amountSmall,
    color: colors.text,
    padding: 0,
  },
  currencyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceVariant,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: borderRadius.round,
    marginLeft: spacing.sm,
  },
  currencyFlag: {
    fontSize: 16,
    marginRight: spacing.xs,
  },
  currencyCode: {
    ...typography.labelLarge,
    color: colors.text,
  },
  errorText: {
    ...typography.bodySmall,
    color: colors.error,
    marginTop: spacing.xs,
  },
});

export default AmountInput;
