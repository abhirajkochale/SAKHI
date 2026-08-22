import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, TextInput } from 'react-native';
import { Location } from '../types/api';

interface Props {
  onAnalyze: (origin: Location, destination: Location) => void;
  loading: boolean;
}

export default function JourneyForm({ onAnalyze, loading }: Props) {
  const [originText, setOriginText] = useState('');
  const [destinationText, setDestinationText] = useState('');
  const [origin, setOrigin] = useState<Location | null>(null);
  const [destination, setDestination] = useState<Location | null>(null);
  const [geocodeLoading, setGeocodeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const geocodeAddress = async (address: string): Promise<Location | null> => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1`, {
        headers: { 'User-Agent': 'SAKHI-Hackathon-App' }
      });
      const data = await res.json();
      if (data && data.length > 0) {
        return { latitude: parseFloat(data[0].lat), longitude: parseFloat(data[0].lon) };
      }
      return null;
    } catch (e) {
      console.error(e);
      return null;
    }
  };

  const handleAnalyze = async () => {
    setError(null);
    if (!originText || !destinationText) {
      setError("Please enter origin and destination addresses.");
      return;
    }
    
    let currentOrig = origin;
    let currentDest = destination;

    if (!currentOrig) {
      setGeocodeLoading(true);
      currentOrig = await geocodeAddress(originText);
      setGeocodeLoading(false);
      if (!currentOrig) {
        setError(`Could not find location for: ${originText}`);
        return;
      }
      setOrigin(currentOrig);
    }
    
    if (!currentDest) {
      setGeocodeLoading(true);
      currentDest = await geocodeAddress(destinationText);
      setGeocodeLoading(false);
      if (!currentDest) {
        setError(`Could not find location for: ${destinationText}`);
        return;
      }
      setDestination(currentDest);
    }
    
    onAnalyze(currentOrig, currentDest);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>SAKHI</Text>
      <Text style={styles.subtitle}>Smart Assistance for keeping HER informed</Text>
      
      {error && <Text style={{color: '#dc2626', marginBottom: 8, fontSize: 12}}>{error}</Text>}

      <View style={styles.inputContainer}>
        <Text style={styles.label}>Origin</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter starting location..."
          value={originText}
          onChangeText={(t) => { setOriginText(t); setOrigin(null); }}
        />
      </View>

      <View style={styles.inputContainer}>
        <Text style={styles.label}>Destination</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter destination..."
          value={destinationText}
          onChangeText={(t) => { setDestinationText(t); setDestination(null); }}
        />
      </View>

      <View style={styles.buttonRow}>
        <TouchableOpacity 
          style={[styles.analyzeButton, (!originText || !destinationText) && styles.disabledButton]} 
          onPress={handleAnalyze}
          disabled={!originText || !destinationText || loading || geocodeLoading}
        >
          {loading || geocodeLoading ? (
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
  input: {
    fontSize: 14,
    padding: 10,
    backgroundColor: '#f9fafb',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#d1d5db',
    color: '#111827',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
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
