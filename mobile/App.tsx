import { StatusBar } from 'expo-status-bar';
import React from 'react';
import JourneyDashboard from './src/screens/JourneyDashboard';

export default function App() {
  return (
    <>
      <JourneyDashboard />
      <StatusBar style="auto" />
    </>
  );
}

