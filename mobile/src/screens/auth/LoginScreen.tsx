// ============================================================
// Ha_Chain - Login Screen (Phone + OTP)
// ============================================================

import React, { useState, useRef } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { IconButton, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { colors, spacing, typography, borderRadius } from '../../theme';
import { RootStackParamList } from '../../types';
import { useAuth } from '../../store/AuthContext';
import Button from '../../components/common/Button';

type LoginScreenProps = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Login'>;
};

const COUNTRY_CODES = [
  { code: '+1', country: 'US', flag: '🇺🇸' },
  { code: '+44', country: 'GB', flag: '🇬🇧' },
  { code: '+91', country: 'IN', flag: '🇮🇳' },
  { code: '+63', country: 'PH', flag: '🇵🇭' },
  { code: '+234', country: 'NG', flag: '🇳🇬' },
  { code: '+254', country: 'KE', flag: '🇰🇪' },
  { code: '+233', country: 'GH', flag: '🇬🇭' },
  { code: '+252', country: 'SO', flag: '🇸🇴' },
  { code: '+251', country: 'ET', flag: '🇪🇹' },
  { code: '+880', country: 'BD', flag: '🇧🇩' },
  { code: '+92', country: 'PK', flag: '🇵🇰' },
  { code: '+52', country: 'MX', flag: '🇲🇽' },
  { code: '+55', country: 'BR', flag: '🇧🇷' },
];

const OTP_LENGTH = 6;

const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  const { requestOTP, verifyOTP, isLoading, error, clearError } = useAuth();

  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [selectedCountry, setSelectedCountry] = useState(COUNTRY_CODES[0]);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState<string[]>(Array(OTP_LENGTH).fill(''));
  const otpRefs = useRef<(TextInput | null)[]>([]);

  const handleSendOTP = async () => {
    if (phone.length < 7) {
      Alert.alert('Invalid Phone', 'Please enter a valid phone number.');
      return;
    }
    try {
      await requestOTP(phone, selectedCountry.code);
      setStep('otp');
    } catch {
      // Error is handled in AuthContext
    }
  };

  const handleVerifyOTP = async () => {
    const otpString = otp.join('');
    if (otpString.length !== OTP_LENGTH) {
      Alert.alert('Invalid OTP', 'Please enter the complete verification code.');
      return;
    }
    try {
      await verifyOTP(phone, selectedCountry.code, otpString);
      // Navigation to MainTabs is handled by the navigator based on auth state
    } catch {
      // Error is handled in AuthContext
    }
  };

  const handleOTPChange = (text: string, index: number) => {
    clearError();
    const newOtp = [...otp];
    newOtp[index] = text;
    setOtp(newOtp);

    // Auto-focus next input
    if (text && index < OTP_LENGTH - 1) {
      otpRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all digits entered
    if (text && index === OTP_LENGTH - 1) {
      const complete = newOtp.join('');
      if (complete.length === OTP_LENGTH) {
        handleVerifyOTP();
      }
    }
  };

  const handleOTPKeyPress = (key: string, index: number) => {
    if (key === 'Backspace' && !otp[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const renderPhoneStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Enter your phone number</Text>
      <Text style={styles.stepSubtitle}>
        We will send you a verification code via SMS
      </Text>

      <View style={styles.phoneInputRow}>
        <TouchableOpacity style={styles.countrySelector}>
          <Text style={styles.countryFlag}>{selectedCountry.flag}</Text>
          <Text style={styles.countryCode}>{selectedCountry.code}</Text>
          <Icon name="chevron-down" size={16} color={colors.textSecondary} />
        </TouchableOpacity>
        <View style={styles.phoneInputWrapper}>
          <TextInput
            style={styles.phoneInput}
            value={phone}
            onChangeText={(text) => {
              clearError();
              setPhone(text.replace(/[^0-9]/g, ''));
            }}
            placeholder="Phone number"
            placeholderTextColor={colors.textTertiary}
            keyboardType="phone-pad"
            autoFocus
            maxLength={15}
          />
        </View>
      </View>

      {error && <Text style={styles.errorText}>{error}</Text>}

      <Button
        title="Send Verification Code"
        onPress={handleSendOTP}
        variant="primary"
        size="large"
        loading={isLoading}
        disabled={phone.length < 7 || isLoading}
        style={styles.submitButton}
      />
    </View>
  );

  const renderOTPStep = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Enter verification code</Text>
      <Text style={styles.stepSubtitle}>
        Sent to {selectedCountry.code} {phone}
      </Text>

      <View style={styles.otpContainer}>
        {Array(OTP_LENGTH)
          .fill(0)
          .map((_, index) => (
            <TextInput
              key={index}
              ref={(ref) => (otpRefs.current[index] = ref)}
              style={[
                styles.otpInput,
                otp[index] ? styles.otpInputFilled : null,
                error ? styles.otpInputError : null,
              ]}
              value={otp[index]}
              onChangeText={(text) => handleOTPChange(text.replace(/[^0-9]/g, ''), index)}
              onKeyPress={({ nativeEvent }) => handleOTPKeyPress(nativeEvent.key, index)}
              keyboardType="number-pad"
              maxLength={1}
              autoFocus={index === 0}
              selectTextOnFocus
            />
          ))}
      </View>

      {error && <Text style={styles.errorText}>{error}</Text>}

      {isLoading && (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={styles.loadingText}>Verifying...</Text>
        </View>
      )}

      <Button
        title="Verify"
        onPress={handleVerifyOTP}
        variant="primary"
        size="large"
        loading={isLoading}
        disabled={otp.join('').length !== OTP_LENGTH || isLoading}
        style={styles.submitButton}
      />

      <TouchableOpacity
        style={styles.resendRow}
        onPress={() => {
          setOtp(Array(OTP_LENGTH).fill(''));
          clearError();
          handleSendOTP();
        }}
      >
        <Text style={styles.resendText}>Didn't receive the code? </Text>
        <Text style={styles.resendLink}>Resend</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        {/* Back button */}
        <View style={styles.navBar}>
          <IconButton
            icon="arrow-left"
            onPress={() => {
              if (step === 'otp') {
                setStep('phone');
                setOtp(Array(OTP_LENGTH).fill(''));
                clearError();
              } else {
                navigation.goBack();
              }
            }}
            iconColor={colors.text}
          />
        </View>

        {/* Logo */}
        <View style={styles.logoContainer}>
          <View style={styles.logoIcon}>
            <Icon name="swap-horizontal-circle" size={32} color="#FFFFFF" />
          </View>
          <Text style={styles.logoText}>Ha_Chain</Text>
        </View>

        {step === 'phone' ? renderPhoneStep() : renderOTPStep()}

        {/* Terms */}
        <Text style={styles.termsText}>
          By continuing, you agree to our{' '}
          <Text style={styles.termsLink}>Terms of Service</Text> and{' '}
          <Text style={styles.termsLink}>Privacy Policy</Text>
        </Text>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  keyboardView: {
    flex: 1,
    paddingHorizontal: spacing.xxl,
  },
  navBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: -spacing.md,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xxxl,
    marginTop: spacing.lg,
  },
  logoIcon: {
    width: 44,
    height: 44,
    borderRadius: borderRadius.md,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: spacing.md,
  },
  logoText: {
    ...typography.headlineLarge,
    color: colors.text,
  },
  stepContainer: {
    flex: 1,
  },
  stepTitle: {
    ...typography.displaySmall,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  stepSubtitle: {
    ...typography.bodyLarge,
    color: colors.textSecondary,
    marginBottom: spacing.xxxl,
  },
  phoneInputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xxl,
  },
  countrySelector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.lg,
    marginRight: spacing.md,
  },
  countryFlag: {
    fontSize: 20,
    marginRight: spacing.xs,
  },
  countryCode: {
    ...typography.headlineSmall,
    color: colors.text,
    marginRight: spacing.xs,
  },
  phoneInputWrapper: {
    flex: 1,
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.lg,
  },
  phoneInput: {
    ...typography.headlineSmall,
    color: colors.text,
    paddingVertical: spacing.lg,
  },
  otpContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xxl,
  },
  otpInput: {
    width: 48,
    height: 56,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: borderRadius.md,
    backgroundColor: colors.surface,
    textAlign: 'center',
    ...typography.headlineLarge,
    color: colors.text,
  },
  otpInputFilled: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryBg,
  },
  otpInputError: {
    borderColor: colors.error,
  },
  errorText: {
    ...typography.bodyMedium,
    color: colors.error,
    marginBottom: spacing.lg,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.lg,
  },
  loadingText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
    marginLeft: spacing.sm,
  },
  submitButton: {
    marginBottom: spacing.lg,
  },
  resendRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: spacing.md,
  },
  resendText: {
    ...typography.bodyMedium,
    color: colors.textSecondary,
  },
  resendLink: {
    ...typography.labelLarge,
    color: colors.primary,
  },
  termsText: {
    ...typography.bodySmall,
    color: colors.textTertiary,
    textAlign: 'center',
    paddingBottom: spacing.xxl,
  },
  termsLink: {
    color: colors.primary,
  },
});

export default LoginScreen;
