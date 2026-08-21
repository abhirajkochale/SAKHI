import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { sakhiApi } from '../api/sakhiApi';

interface Props {
  journeyId?: string;
}

export default function EmergencyPanel({ journeyId }: Props) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const handleSos = async () => {
    setLoading(true);
    setStatus(null);
    try {
      // Mock location for demo since we don't have expo-location here yet
      const loc = { latitude: 28.6139, longitude: 77.2090 }; 
      const res = await sakhiApi.triggerSos(journeyId || null, loc);
      setStatus(`SOS Sent! ID: ${res.sos_id.substring(0,8)}`);
    } catch (e) {
      setStatus('Failed to send SOS');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>EMERGENCY</Text>
      <Text style={styles.subtitle}>Current journey information available</Text>
      
      {status && (
        <View style={styles.statusBox}>
          <Text style={styles.statusText}>{status}</Text>
        </View>
      )}

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.callButton}>
          <Text style={styles.buttonText}>CALL 112</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.sosButton} 
          onPress={handleSos}
          disabled={loading}
        >
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>SEND SOS</Text>}
        </TouchableOpacity>
      </View>

      <Text style={styles.demoNote}>
        * Prototype Actions. Does not actually dial or alert authorities.
      </Text>
      
      <View style={styles.offlineContainer}>
        <Text style={styles.offlineTitle}>OFFLINE MODE DEMO</Text>
        <Text style={styles.offlineText}>✓ Cached journey information</Text>
        <Text style={styles.offlineText}>✓ Cached route information</Text>
        <Text style={styles.offlineText}>✓ Cached safety information</Text>
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
    marginVertical: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#dc2626',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 16,
  },
  statusBox: {
    backgroundColor: '#fee2e2',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
    borderColor: '#dc2626',
    borderWidth: 1,
  },
  statusText: {
    color: '#991b1b',
    fontWeight: 'bold',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  callButton: {
    flex: 1,
    backgroundColor: '#dc2626',
    padding: 14,
    borderRadius: 8,
    marginRight: 8,
    alignItems: 'center',
  },
  sosButton: {
    flex: 1,
    backgroundColor: '#111827',
    padding: 14,
    borderRadius: 8,
    marginLeft: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  demoNote: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
    marginBottom: 16,
  },
  offlineContainer: {
    backgroundColor: '#f3f4f6',
    padding: 12,
    borderRadius: 8,
  },
  offlineTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#374151',
  },
  offlineText: {
    fontSize: 14,
    color: '#4b5563',
    marginBottom: 4,
  }
});
