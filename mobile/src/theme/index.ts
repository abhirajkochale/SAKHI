import { useAccessibility } from '../contexts/AccessibilityContext';
import { lightTheme, highContrastTheme } from './colors';
import { typography } from './typography';
import { spacing, radius } from './spacing';

export const useTheme = () => {
  const { isAccessibleMode } = useAccessibility();
  const colors = isAccessibleMode ? highContrastTheme : lightTheme;
  const isHighContrast = isAccessibleMode;

  return {
    colors,
    typography,
    spacing,
    radius,
    isHighContrast,
  };
};
