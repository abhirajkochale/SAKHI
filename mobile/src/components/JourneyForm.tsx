import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Location } from '../types/api';

interface Props {
  onAnalyze: (origin: Location, destination: Location) => void;
  loading: boolean;
}

export default function JourneyForm({ onAnalyze, loading }: Props) {
  const [origin, setOrigin] = useState<Location | null>(null);
  const [destination, setDestination] = useState<Location | null>(null);

  const loadDemoJourney = () => {
    // Mumbai demo coordinates
    setOrigin({ latitude: 18.922, longitude: 72.827 });
    setDestination({ latitude: 18.928, longitude: 72.833 });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>SAKHI</Text>
      <Text style={styles.subtitle}>Smart Assistance for keeping HER informed</Text>
      
      <View style={styles.inputContainer}>
        <Text style={styles.label}>Origin</Text>
        <Text style={styles.value}>
          {origin ? `${origin.latitude.toFixed(4)}, ${origin.longitude.toFixed(4)}` : 'Not Set'}
        </Text>
      </View>

      <View style={styles.inputContainer}>
        <Text style={styles.label}>Destination</Text>
        <Text style={styles.value}>
          {destination ? `${destination.latitude.toFixed(4)}, ${destination.longitude.toFixed(4)}` : 'Not Set'}
        </Text>
      </View>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.demoButton} onPress={loadDemoJourney}>
          <Text style={styles.demoButtonText}>Load Demo Journey</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.analyzeButton, (!origin || !destination) && styles.disabledButton]} 
          onPress={() => onAnalyze(origin!, destination!)}
          disabled={!origin || !destination || loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.analyzeButtonText}>Analyze Journey</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1d4ed8', // blue-700
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 16,
  },
  inputContainer: {
    marginBottom: 12,
  },
  label: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#4b5563',
    marginBottom: 4,
  },
  value: {
    fontSize: 14,
    padding: 10,
    backgroundColor: '#f3f4f6',
    borderRadius: 6,
    color: '#111827',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  demoButton: {
    flex: 1,
    padding: 12,
    backgroundColor: '#e5e7eb',
    borderRadius: 6,
    marginRight: 8,
    alignItems: 'center',
  },
  demoButtonText: {
    color: '#4b5563',
    fontWeight: 'bold',
  },
  analyzeButton: {
    flex: 1,
    padding: 12,
    backgroundColor: '#2563eb',
    borderRadius: 6,
    marginLeft: 8,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#93c5fd',
  },
  analyzeButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  }
});
