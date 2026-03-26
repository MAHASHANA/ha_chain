// ============================================================
// Ha_Chain Theme - Colors, Typography, Spacing
// ============================================================

export const colors = {
  // Primary palette
  primary: '#2563EB',
  primaryDark: '#1D4ED8',
  primaryLight: '#60A5FA',
  primaryBg: '#EFF6FF',

  // Secondary palette
  secondary: '#10B981',
  secondaryDark: '#059669',
  secondaryLight: '#34D399',
  secondaryBg: '#ECFDF5',

  // Accent
  accent: '#F59E0B',
  accentDark: '#D97706',
  accentLight: '#FCD34D',
  accentBg: '#FFFBEB',

  // Neutrals
  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceVariant: '#F1F5F9',
  border: '#E2E8F0',
  borderLight: '#F1F5F9',

  // Text
  text: '#1E293B',
  textSecondary: '#64748B',
  textTertiary: '#94A3B8',
  textInverse: '#FFFFFF',
  textLink: '#2563EB',

  // Status
  success: '#10B981',
  successBg: '#ECFDF5',
  warning: '#F59E0B',
  warningBg: '#FFFBEB',
  error: '#EF4444',
  errorBg: '#FEF2F2',
  info: '#3B82F6',
  infoBg: '#EFF6FF',

  // Match-specific
  matchGreen: '#10B981',
  matchPurple: '#8B5CF6',
  matchGold: '#F59E0B',
  poolBlue: '#06B6D4',

  // Shadows
  shadowColor: '#000000',

  // Transparent
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.1)',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
  huge: 48,
  massive: 64,
} as const;

export const borderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  round: 999,
} as const;

export const typography = {
  // Display
  displayLarge: {
    fontSize: 34,
    fontWeight: '700' as const,
    lineHeight: 42,
    letterSpacing: -0.5,
  },
  displayMedium: {
    fontSize: 28,
    fontWeight: '700' as const,
    lineHeight: 36,
    letterSpacing: -0.3,
  },
  displaySmall: {
    fontSize: 24,
    fontWeight: '600' as const,
    lineHeight: 32,
    letterSpacing: -0.2,
  },

  // Headings
  headlineLarge: {
    fontSize: 22,
    fontWeight: '600' as const,
    lineHeight: 28,
  },
  headlineMedium: {
    fontSize: 18,
    fontWeight: '600' as const,
    lineHeight: 24,
  },
  headlineSmall: {
    fontSize: 16,
    fontWeight: '600' as const,
    lineHeight: 22,
  },

  // Body
  bodyLarge: {
    fontSize: 16,
    fontWeight: '400' as const,
    lineHeight: 24,
  },
  bodyMedium: {
    fontSize: 14,
    fontWeight: '400' as const,
    lineHeight: 20,
  },
  bodySmall: {
    fontSize: 12,
    fontWeight: '400' as const,
    lineHeight: 16,
  },

  // Labels
  labelLarge: {
    fontSize: 14,
    fontWeight: '600' as const,
    lineHeight: 20,
  },
  labelMedium: {
    fontSize: 12,
    fontWeight: '600' as const,
    lineHeight: 16,
  },
  labelSmall: {
    fontSize: 10,
    fontWeight: '600' as const,
    lineHeight: 14,
  },

  // Special
  amount: {
    fontSize: 36,
    fontWeight: '700' as const,
    lineHeight: 44,
    letterSpacing: -1,
  },
  amountSmall: {
    fontSize: 24,
    fontWeight: '700' as const,
    lineHeight: 30,
    letterSpacing: -0.5,
  },
} as const;

export const shadows = {
  small: {
    shadowColor: colors.shadowColor,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  medium: {
    shadowColor: colors.shadowColor,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  large: {
    shadowColor: colors.shadowColor,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
  },
} as const;

const theme = {
  colors,
  spacing,
  borderRadius,
  typography,
  shadows,
};

export default theme;
