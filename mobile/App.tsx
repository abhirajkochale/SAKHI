import { StatusBar } from 'expo-status-bar';
import React, { useEffect } from 'react';
import JourneyDashboard from './src/screens/JourneyDashboard';
import { initDb } from './src/api/cache';
import { AccessibilityProvider } from './src/contexts/AccessibilityContext';

export default function App() {
  useEffect(() => {
    initDb();
  }, []);

  return (
    <AccessibilityProvider>
      <JourneyDashboard />
      <StatusBar style="auto" />
    </AccessibilityProvider>
  );
}

