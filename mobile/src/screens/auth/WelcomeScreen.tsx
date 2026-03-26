// ============================================================
// Ha_Chain - Welcome Screen (Landing Page)
// ============================================================

import React from 'react';
import { StyleSheet, View, Text, StatusBar, Dimensions, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, typography, borderRadius } from '../../theme';
import { RootStackParamList } from '../../types';
import Button from '../../components/common/Button';

const { width } = Dimensions.get('window');

type WelcomeScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Welcome'>;
};

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ navigation }) => {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor={colors.background} />

      {/* Hero Section */}
      <View style={styles.heroSection}>
        <View style={styles.logoContainer}>
          <View style={styles.logoIcon}>
            <Icon name="swap-horizontal-circle" size={40} color="#FFFFFF" />
          </View>
          <Text style={styles.logoText}>Ha_Chain</Text>
        </View>

        {/* Illustration area */}
        <View style={styles.illustrationContainer}>
          <View style={styles.globeContainer}>
            <Icon name="earth" size={120} color={colors.primaryLight} />
            {/* Floating currency symbols around the globe */}
            <View style={[styles.floatingCurrency, { top: 10, left: 20 }]}>
              <Text style={styles.currencyEmoji}>$</Text>
            </View>
            <View style={[styles.floatingCurrency, { top: 20, right: 10 }]}>
              <Text style={styles.currencyEmoji}>&#x20B9;</Text>
            </View>
            <View style={[styles.floatingCurrency, { bottom: 20, left: 10 }]}>
              <Text style={styles.currencyEmoji}>&#x20A6;</Text>
            </View>
            <View style={[styles.floatingCurrency, { bottom: 10, right: 20 }]}>
              <Text style={styles.currencyEmoji}>&#x20B1;</Text>
            </View>
          </View>
        </View>

        {/* Tagline */}
        <Text style={styles.tagline}>Send Money{'\n'}Anywhere</Text>
        <Text style={styles.subtitle}>
          Peer-matched transfers with near-zero fees.{'\n'}
          Your money finds a match, not a middleman.
        </Text>
      </View>

      {/* Features */}
      <View style={styles.featuresRow}>
        <View style={styles.featureItem}>
          <Icon name="lightning-bolt" size={20} color={colors.accent} />
          <Text style={styles.featureText}>Instant</Text>
        </View>
        <View style={styles.featureDivider} />
        <View style={styles.featureItem}>
          <Icon name="shield-check" size={20} color={colors.secondary} />
          <Text style={styles.featureText}>Secure</Text>
        </View>
        <View style={styles.featureDivider} />
        <View style={styles.featureItem}>
          <Icon name="cash-multiple" size={20} color={colors.primary} />
          <Text style={styles.featureText}>Low Fees</Text>
        </View>
      </View>

      {/* CTA Buttons */}
      <View style={styles.ctaSection}>
        <Button
          title="Get Started"
          onPress={() => navigation.navigate('Login')}
          variant="primary"
          size="large"
        />
        <Button
          title="I already have an account"
          onPress={() => navigation.navigate('Login')}
          variant="ghost"
          size="medium"
          style={styles.loginButton}
        />
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: spacing.xxl,
  },
  heroSection: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xxxl,
  },
  logoIcon: {
    width: 52,
    height: 52,
    borderRadius: borderRadius.lg,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  logoText: {
    ...typography.displayMedium,
    color: colors.text,
  },
  illustrationContainer: {
    width: width * 0.5,
    height: width * 0.5,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.xxxl,
  },
  globeContainer: {
    position: 'relative',
    justifyContent: 'center',
    alignItems: 'center',
  },
  floatingCurrency: {
    position: 'absolute',
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  currencyEmoji: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.primary,
  },
  tagline: {
    ...typography.displayLarge,
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  subtitle: {
    ...typography.bodyLarge,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  featuresRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: spacing.xxl,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
  },
  featureText: {
    ...typography.labelMedium,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
  },
  featureDivider: {
    width: 1,
    height: 16,
    backgroundColor: colors.border,
  },
  ctaSection: {
    paddingBottom: spacing.xxxl,
  },
  loginButton: {
    marginTop: spacing.sm,
  },
});

export default WelcomeScreen;
