import React from 'react';
import { TouchableOpacity, TouchableOpacityProps, StyleSheet, ActivityIndicator } from 'react-native';
import { useTheme } from '../../theme';
import { baseColors } from '../../theme/colors';
import { SakhiText } from './SakhiText';

interface SakhiButtonProps extends TouchableOpacityProps {
  title: string;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  loading?: boolean;
}

export const SakhiButton = ({ title, variant = 'primary', loading, disabled, style, ...props }: SakhiButtonProps) => {
  const { colors, spacing, radius, isHighContrast } = useTheme();

  const getBackgroundColor = () => {
    if (disabled) return baseColors.gray300;
    switch (variant) {
      case 'primary': return colors.primary;
      case 'secondary': return baseColors.gray200;
      case 'outline': return 'transparent';
      case 'danger': return colors.danger;
      default: return colors.primary;
    }
  };

  const getBorderColor = () => {
    if (disabled) return baseColors.gray400;
    if (variant === 'outline') return colors.primary;
    if (isHighContrast) return colors.border;
    return 'transparent';
  };

  const getTextColor = () => {
    if (disabled) return 'muted';
    switch (variant) {
      case 'primary':
      case 'danger':
        return 'inverse';
      case 'secondary':
      case 'outline':
        return 'primary';
      default: return 'inverse';
    }
  };

  return (
    <TouchableOpacity
      disabled={disabled || loading}
      style={[
        styles.button,
        {
          backgroundColor: getBackgroundColor(),
          borderColor: getBorderColor(),
          borderWidth: (variant === 'outline' || isHighContrast) ? (isHighContrast ? 3 : 2) : 0,
          borderRadius: radius.md,
          paddingVertical: spacing.md,
          paddingHorizontal: spacing.lg,
        },
        style,
      ]}
      {...props}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'outline' ? colors.primary : colors.primaryText} />
      ) : (
        <SakhiText variant="button" color={getTextColor()} style={styles.textCenter}>
          {title}
        </SakhiText>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  textCenter: {
    textAlign: 'center',
  },
});
