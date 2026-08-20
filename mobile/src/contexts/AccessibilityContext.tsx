import React, { createContext, useContext, useState, ReactNode } from 'react';

interface AccessibilityContextType {
  isAccessibleMode: boolean;
  toggleAccessibleMode: () => void;
}

const AccessibilityContext = createContext<AccessibilityContextType>({
  isAccessibleMode: false,
  toggleAccessibleMode: () => {},
});

export const useAccessibility = () => useContext(AccessibilityContext);

export const AccessibilityProvider = ({ children }: { children: ReactNode }) => {
  const [isAccessibleMode, setIsAccessibleMode] = useState(false);

  const toggleAccessibleMode = () => {
    setIsAccessibleMode(!isAccessibleMode);
  };

  return (
    <AccessibilityContext.Provider value={{ isAccessibleMode, toggleAccessibleMode }}>
      {children}
    </AccessibilityContext.Provider>
  );
};
