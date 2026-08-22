import React from 'react';
import { View, ViewProps, StyleSheet } from 'react-native';
import { useTheme } from '../../theme';

interface SakhiCardProps extends ViewProps {
  elevated?: boolean;
}

export const SakhiCard = ({ elevated = false, style, children, ...props }: SakhiCardProps) => {
  const { colors, spacing, radius, isHighContrast } = useTheme();

  return (
    <View
      style={[
        {
          backgroundColor: colors.surface,
          borderRadius: radius.lg,
          padding: spacing.md,
          borderColor: colors.border,
          borderWidth: isHighContrast ? 3 : 1,
        },
        elevated && !isHighContrast ? styles.elevated : null,
        style,
      ]}
      {...props}
    >
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  elevated: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
});
