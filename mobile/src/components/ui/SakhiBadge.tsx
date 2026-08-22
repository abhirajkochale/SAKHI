import React from 'react';
import { View, ViewProps } from 'react-native';
import { useTheme } from '../../theme';
import { SakhiText } from './SakhiText';

interface SakhiBadgeProps extends ViewProps {
  label: string;
  variant?: 'success' | 'warning' | 'danger' | 'info';
}

export const SakhiBadge = ({ label, variant = 'info', style, ...props }: SakhiBadgeProps) => {
  const { colors, spacing, radius, isHighContrast } = useTheme();

  const getBackgroundColor = () => {
    if (isHighContrast) return colors.surface;
    switch (variant) {
      case 'success': return '#D1FAE5'; // Light green
      case 'warning': return '#FEF3C7'; // Light orange
      case 'danger': return '#FEE2E2'; // Light red
      case 'info': return '#DBEAFE'; // Light blue
      default: return '#DBEAFE';
    }
  };

  const getTextColor = () => {
    switch (variant) {
      case 'success': return colors.success;
      case 'warning': return colors.warning;
      case 'danger': return colors.danger;
      case 'info': return colors.info;
      default: return colors.info;
    }
  };

  return (
    <View
      style={[
        {
          backgroundColor: getBackgroundColor(),
          paddingHorizontal: spacing.sm,
          paddingVertical: spacing.xs,
          borderRadius: radius.pill,
          borderWidth: isHighContrast ? 2 : 0,
          borderColor: isHighContrast ? getTextColor() : 'transparent',
          alignSelf: 'flex-start',
        },
        style,
      ]}
      {...props}
    >
      <SakhiText variant="caption" style={{ color: getTextColor(), fontWeight: 'bold' }}>
        {label}
      </SakhiText>
    </View>
  );
};
