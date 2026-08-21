import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { sakhiApi } from '../api/sakhiApi';
import { ContextUpdateEvent, ContextUpdateResponse } from '../types/api';

interface Props {
  segmentId: string;
  journeyId: string;
  onUpdateResult: (result: ContextUpdateResponse) => void;
}

export default function ContextUpdatePanel({ segmentId, journeyId, onUpdateResult }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = async (eventType: 'validated_report' | 'infrastructure_outage') => {
    setLoading(true);
    setError(null);
    try {
      const event: ContextUpdateEvent = {
        segment_id: segmentId,
        event_type: eventType,
        severity: 1.0,
        source: 'simulated_demo',
        timestamp: new Date().toISOString(),
        active: true,
      };
      const result = await sakhiApi.updateContext(journeyId, event);
      onUpdateResult(result);
    } catch (err: any) {
      setError(err.message || 'Failed to update context');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DYNAMIC CONTEXT CONTROL</Text>
        <Text style={styles.badge}>DEMO FEATURE</Text>
      </View>
      
      <Text style={styles.desc}>
        Simulate a real-time event on segment {segmentId?.substring(0,6)} to watch SAKHI's AI recalculate risk and dynamically re-rank the routes.
      </Text>

      {error && <Text style={styles.errorText}>{error}</Text>}

      <TouchableOpacity 
        style={[styles.button, styles.reportButton]} 
        onPress={() => handleUpdate('validated_report')}
        disabled={loading}
      >
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Trigger Validated Risk Report</Text>}
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={[styles.button, styles.infraButton]} 
        onPress={() => handleUpdate('infrastructure_outage')}
        disabled={loading}
      >
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Trigger Infrastructure Outage (Lights/CCTV)</Text>}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fffbe1',
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
    fontSize: 14,
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
    fontSize: 13,
    color: '#92400e',
    marginBottom: 10,
    lineHeight: 18,
  },
  errorText: {
    color: '#dc2626',
    marginBottom: 8,
    fontSize: 12,
  },
  button: {
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 6,
  },
  reportButton: {
    backgroundColor: '#dc2626',
  },
  infraButton: {
    backgroundColor: '#4b5563',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  }
});
