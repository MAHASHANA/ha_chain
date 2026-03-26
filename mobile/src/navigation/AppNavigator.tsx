// ============================================================
// Ha_Chain - App Navigator (Stack + Bottom Tab navigation)
// ============================================================

import React from 'react';
import { StyleSheet, View, Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, typography, spacing } from '../theme';
import { RootStackParamList, MainTabParamList } from '../types';
import { useAuth } from '../store/AuthContext';

// Auth Screens
import WelcomeScreen from '../screens/auth/WelcomeScreen';
import LoginScreen from '../screens/auth/LoginScreen';

// Main Screens
import HomeScreen from '../screens/home/HomeScreen';
import SendScreen from '../screens/send/SendScreen';
import QuoteScreen from '../screens/send/QuoteScreen';
import ConfirmScreen from '../screens/send/ConfirmScreen';
import SuccessScreen from '../screens/send/SuccessScreen';
import PoolStatusScreen from '../screens/pool/PoolStatusScreen';
import AssetsScreen from '../screens/invest/AssetsScreen';
import PortfolioScreen from '../screens/invest/PortfolioScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

// --- Bottom Tab Navigator ---

const MainTabs: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textTertiary,
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabBarLabel,
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="home" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="SendTab"
        component={SendScreen}
        options={{
          tabBarLabel: 'Send',
          tabBarIcon: ({ color, size, focused }) => (
            <View
              style={[
                styles.sendTabIcon,
                focused && styles.sendTabIconActive,
              ]}
            >
              <Icon
                name="send"
                size={focused ? 26 : size}
                color={focused ? '#FFFFFF' : color}
              />
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="Pool"
        component={PoolStatusScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="swap-horizontal-circle-outline" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Invest"
        component={AssetsScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="chart-line" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="More"
        component={MorePlaceholder}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Icon name="dots-horizontal" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// Placeholder for More tab
const MorePlaceholder: React.FC = () => (
  <View style={styles.placeholder}>
    <Icon name="cog-outline" size={48} color={colors.textTertiary} />
    <Text style={styles.placeholderText}>Settings & More</Text>
    <Text style={styles.placeholderSubtext}>Coming soon</Text>
  </View>
);

// --- Root Stack Navigator ---

const AppNavigator: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <View style={styles.loadingLogo}>
          <Icon name="swap-horizontal-circle" size={56} color={colors.primary} />
        </View>
        <Text style={styles.loadingText}>Ha_Chain</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
          contentStyle: { backgroundColor: colors.background },
        }}
      >
        {!isAuthenticated ? (
          // Auth flow
          <>
            <Stack.Screen name="Welcome" component={WelcomeScreen} />
            <Stack.Screen name="Login" component={LoginScreen} />
          </>
        ) : (
          // Main app flow
          <>
            <Stack.Screen name="MainTabs" component={MainTabs} />
            <Stack.Screen name="Send" component={SendScreen} />
            <Stack.Screen name="Quote" component={QuoteScreen} />
            <Stack.Screen name="Confirm" component={ConfirmScreen} />
            <Stack.Screen
              name="Success"
              component={SuccessScreen}
              options={{ gestureEnabled: false }}
            />
            <Stack.Screen name="PoolStatus" component={PoolStatusScreen} />
            <Stack.Screen name="Assets" component={AssetsScreen} />
            <Stack.Screen name="Portfolio" component={PortfolioScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.borderLight,
    height: 60,
    paddingBottom: 6,
    paddingTop: 6,
  },
  tabBarLabel: {
    ...typography.labelSmall,
    marginTop: -2,
  },
  sendTabIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: -4,
  },
  sendTabIconActive: {
    backgroundColor: colors.primary,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  loadingLogo: {
    marginBottom: spacing.lg,
  },
  loadingText: {
    ...typography.headlineLarge,
    color: colors.text,
  },
  placeholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  placeholderText: {
    ...typography.headlineSmall,
    color: colors.textSecondary,
    marginTop: spacing.lg,
  },
  placeholderSubtext: {
    ...typography.bodyMedium,
    color: colors.textTertiary,
    marginTop: spacing.sm,
  },
});

export default AppNavigator;
