import React from 'react';
import { View, TextInput, TextInputProps } from 'react-native';
import { useTheme } from '../../theme';
import { SakhiText } from './SakhiText';

interface SakhiInputProps extends TextInputProps {
  label?: string;
  error?: string;
}

export const SakhiInput = ({ label, error, style, ...props }: SakhiInputProps) => {
  const { colors, spacing, radius, typography, isHighContrast } = useTheme();

  const borderColor = error ? colors.danger : colors.border;
  const borderWidth = isHighContrast ? 3 : 1;

  return (
    <View style={{ marginBottom: spacing.md }}>
      {label && (
        <SakhiText variant="subtext" color="primary" style={{ marginBottom: spacing.xs, fontWeight: 'bold' }}>
          {label}
        </SakhiText>
      )}
      <TextInput
        style={[
          typography.body,
          {
            color: colors.text,
            backgroundColor: colors.surface,
            borderColor,
            borderWidth,
            borderRadius: radius.md,
            padding: spacing.md,
          },
          style,
        ]}
        placeholderTextColor={colors.textMuted}
        {...props}
      />
      {error && (
        <SakhiText variant="caption" color="danger" style={{ marginTop: spacing.xs }}>
          {error}
        </SakhiText>
      )}
    </View>
  );
};
