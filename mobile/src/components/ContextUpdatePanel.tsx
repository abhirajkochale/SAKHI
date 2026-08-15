import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { sakhiApi } from '../api/sakhiApi';
import { ContextUpdateEvent, ContextUpdateResponse } from '../types/api';

interface Props {
  journeyId: string;
  segmentId: string;
  onUpdateComplete: (response: ContextUpdateResponse) => void;
}

export default function ContextUpdatePanel({ journeyId, segmentId, onUpdateComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSimulate = async () => {
    setLoading(true);
    setError(null);
    try {
      const event: ContextUpdateEvent = {
        segment_id: segmentId,
        event_type: "validated_report",
        severity: 85,
        source: "simulated_demo",
        timestamp: new Date().toISOString(),
        active: true,
        description: "Simulated safety-context change for prototype demonstration",
      };
      const response = await sakhiApi.updateContext(journeyId, event);
      onUpdateComplete(response);
    } catch (err: any) {
      setError(err.message || "Failed to update context");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DEMO CONTROL</Text>
        <Text style={styles.badge}>SIMULATED DEMO EVENT</Text>
      </View>
      
      <Text style={styles.desc}>
        Simulate a contextual safety report on Segment {segmentId?.substring(0,6)}... to demonstrate dynamic recalculation and rerouting.
      </Text>

      {error && <Text style={styles.error}>{error}</Text>}

      <TouchableOpacity 
        style={styles.button} 
        onPress={handleSimulate}
        disabled={loading || !segmentId}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Simulate Safety Report</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fffbe1', // light yellow for demo warning
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#f59e0b',
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
    fontSize: 16,
    color: '#b45309',
  },
  badge: {
    backgroundColor: '#fef3c7',
    color: '#d97706',
    fontSize: 10,
    fontWeight: 'bold',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  desc: {
    fontSize: 14,
    color: '#92400e',
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#d97706',
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  error: {
    color: 'red',
    marginBottom: 8,
  }
});
