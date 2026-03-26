// ============================================================
// Ha_Chain - Currency Selector Component
// ============================================================

import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  Modal,
  FlatList,
  SafeAreaView,
} from 'react-native';
import { Searchbar, IconButton } from 'react-native-paper';
import { colors, spacing, typography, borderRadius, shadows } from '../../theme';
import { Currency, CurrencyCode } from '../../types';
import { SUPPORTED_CURRENCIES } from '../../utils/constants';

interface CurrencySelectorProps {
  selectedCurrency: CurrencyCode;
  onSelect: (currency: CurrencyCode) => void;
  label?: string;
  filterCurrencies?: CurrencyCode[];
  disabled?: boolean;
}

const CurrencySelector: React.FC<CurrencySelectorProps> = ({
  selectedCurrency,
  onSelect,
  label,
  filterCurrencies,
  disabled = false,
}) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const availableCurrencies = filterCurrencies
    ? SUPPORTED_CURRENCIES.filter(c => filterCurrencies.includes(c.code))
    : SUPPORTED_CURRENCIES;

  const filteredCurrencies = availableCurrencies.filter(
    c =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.code.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const selected = SUPPORTED_CURRENCIES.find(c => c.code === selectedCurrency);

  const handleSelect = (code: CurrencyCode) => {
    onSelect(code);
    setModalVisible(false);
    setSearchQuery('');
  };

  const renderCurrencyItem = ({ item }: { item: Currency }) => (
    <TouchableOpacity
      style={[
        styles.currencyItem,
        item.code === selectedCurrency && styles.currencyItemSelected,
      ]}
      onPress={() => handleSelect(item.code)}
      activeOpacity={0.7}
    >
      <Text style={styles.flag}>{item.flag}</Text>
      <View style={styles.currencyInfo}>
        <Text style={styles.currencyCode}>{item.code}</Text>
        <Text style={styles.currencyName}>{item.name}</Text>
      </View>
      {item.code === selectedCurrency && (
        <IconButton icon="check-circle" iconColor={colors.primary} size={22} />
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {label && <Text style={styles.label}>{label}</Text>}
      <TouchableOpacity
        style={[styles.selector, disabled && styles.selectorDisabled]}
        onPress={() => !disabled && setModalVisible(true)}
        activeOpacity={0.7}
      >
        <Text style={styles.selectedFlag}>{selected?.flag}</Text>
        <View style={styles.selectedInfo}>
          <Text style={styles.selectedCode}>{selected?.code}</Text>
          <Text style={styles.selectedName}>{selected?.name}</Text>
        </View>
        <IconButton icon="chevron-down" iconColor={colors.textSecondary} size={20} />
      </TouchableOpacity>

      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setModalVisible(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Select Currency</Text>
            <IconButton
              icon="close"
              onPress={() => setModalVisible(false)}
              iconColor={colors.text}
            />
          </View>
          <Searchbar
            placeholder="Search currencies..."
            onChangeText={setSearchQuery}
            value={searchQuery}
            style={styles.searchBar}
            inputStyle={styles.searchInput}
          />
          <FlatList
            data={filteredCurrencies}
            renderItem={renderCurrencyItem}
            keyExtractor={item => item.code}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
          />
        </SafeAreaView>
      </Modal>
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
  selector: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderColor: colors.border,
    borderRadius: borderRadius.lg,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    minHeight: 56,
  },
  selectorDisabled: {
    opacity: 0.5,
  },
  selectedFlag: {
    fontSize: 24,
    marginRight: spacing.md,
  },
  selectedInfo: {
    flex: 1,
  },
  selectedCode: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  selectedName: {
    ...typography.bodySmall,
    color: colors.textSecondary,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  modalTitle: {
    ...typography.headlineLarge,
    color: colors.text,
  },
  searchBar: {
    margin: spacing.lg,
    backgroundColor: colors.surfaceVariant,
    borderRadius: borderRadius.md,
    elevation: 0,
  },
  searchInput: {
    ...typography.bodyMedium,
  },
  listContent: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xxxl,
  },
  currencyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: borderRadius.md,
    marginBottom: spacing.xs,
  },
  currencyItemSelected: {
    backgroundColor: colors.primaryBg,
  },
  flag: {
    fontSize: 28,
    marginRight: spacing.lg,
  },
  currencyInfo: {
    flex: 1,
  },
  currencyCode: {
    ...typography.headlineSmall,
    color: colors.text,
  },
  currencyName: {
    ...typography.bodySmall,
    color: colors.textSecondary,
    marginTop: 2,
  },
});

export default CurrencySelector;
