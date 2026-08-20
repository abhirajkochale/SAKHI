import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import axios from 'axios';
import { Location } from '../types/api';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface Props {
  journeyId: string;
}

export default function DeadManSwitchPanel({ journeyId }: Props) {
  const [isEnabled, setIsEnabled] = useState(false);
  const [lastCheckin, setLastCheckin] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performCheckin = async () => {
    setLoading(true);
    setError(null);
    try {
      const loc: Location = { latitude: 28.6139, longitude: 77.2090 };
      const res = await axios.post(`${BASE_URL}/journeys/${journeyId}/checkin`, loc);
      const timeStr = new Date(res.data.checked_in_at).toLocaleTimeString();
      setLastCheckin(timeStr);
    } catch (e: any) {
      setError(e.message || 'Checkin failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let interval: any;
    if (isEnabled && journeyId) {
      // For demo, check in every 10 seconds so we can see it working
      interval = setInterval(() => {
        performCheckin();
      }, 10000);
      performCheckin(); // initial checkin
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isEnabled, journeyId]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DEAD-MAN'S SWITCH</Text>
        <TouchableOpacity 
          style={[styles.toggleButton, isEnabled ? styles.enabled : styles.disabled]}
          onPress={() => setIsEnabled(!isEnabled)}
        >
          <Text style={styles.toggleText}>{isEnabled ? 'ACTIVE' : 'OFF'}</Text>
        </TouchableOpacity>
      </View>
      
      <Text style={styles.desc}>
        Periodically checks in with the server to confirm your safety. 
        If the server doesn't hear from you, it automatically triggers an SOS on your behalf.
      </Text>

      {isEnabled && (
        <View style={styles.statusBox}>
          {loading ? (
             <ActivityIndicator size="small" color="#10b981" />
          ) : (
             <Text style={styles.statusText}>
               {lastCheckin ? `Last check-in: ${lastCheckin}` : 'Waiting for first check-in...'}
             </Text>
          )}
          {error && <Text style={styles.errorText}>{error}</Text>}
        </View>
      )}
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontWeight: 'bold',
    fontSize: 14,
    color: '#374151',
  },
  toggleButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  enabled: {
    backgroundColor: '#10b981',
  },
  disabled: {
    backgroundColor: '#d1d5db',
  },
  toggleText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
  },
  desc: {
    fontSize: 13,
    color: '#6b7280',
    marginBottom: 10,
    lineHeight: 18,
  },
  statusBox: {
    backgroundColor: '#f0fdf4',
    padding: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#bbf7d0',
    alignItems: 'center',
  },
  statusText: {
    color: '#166534',
    fontWeight: '500',
    fontSize: 13,
  },
  errorText: {
    color: '#dc2626',
    fontSize: 12,
    marginTop: 4,
  }
});
