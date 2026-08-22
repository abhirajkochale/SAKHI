import React from 'react';
import { Text, TextProps } from 'react-native';
import { useTheme } from '../../theme';

interface SakhiTextProps extends TextProps {
  variant?: 'h1' | 'h2' | 'h3' | 'body' | 'subtext' | 'caption' | 'button';
  color?: 'primary' | 'secondary' | 'muted' | 'inverse' | 'danger' | 'success';
}

export const SakhiText = ({ variant = 'body', color = 'primary', style, ...props }: SakhiTextProps) => {
  const { colors, typography } = useTheme();

  const getColor = () => {
    switch (color) {
      case 'primary': return colors.text;
      case 'secondary': return colors.textSecondary;
      case 'muted': return colors.textMuted;
      case 'inverse': return colors.primaryText;
      case 'danger': return colors.danger;
      case 'success': return colors.success;
      default: return colors.text;
    }
  };

  return (
    <Text
      style={[
        typography[variant],
        { color: getColor() },
        style,
      ]}
      {...props}
    />
  );
};
