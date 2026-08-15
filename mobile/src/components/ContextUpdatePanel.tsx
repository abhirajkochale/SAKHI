import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';

interface Props {
  segmentId: string;
}

export default function ContextUpdatePanel({ segmentId }: Props) {
  const [showReport, setShowReport] = useState(false);

  if (showReport) {
    return (
      <View style={[styles.container, styles.reportContainer]}>
        <View style={styles.header}>
          <Text style={styles.title}>✅ SAFETY ANALYSIS REPORT</Text>
        </View>
        <Text style={styles.desc}>
          The SAKHI AI engine actively evaluated multiple paths for this journey. 
        </Text>
        <Text style={styles.desc}>
          By analyzing real-time environmental context—such as footfall, street lighting, and CCTV coverage—the system successfully identified and recommended a safer corridor (Risk ~20-50).
        </Text>
        <Text style={styles.desc}>
          The alternative route, while slightly faster, was flagged as High Risk (Risk ~55-80) due to poor infrastructure and historical baselines, keeping you away from vulnerable areas.
        </Text>
        <TouchableOpacity 
          style={styles.closeButton} 
          onPress={() => setShowReport(false)}
        >
          <Text style={styles.buttonText}>Close Report</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DEMO CONTROL</Text>
        <Text style={styles.badge}>SIMULATED DEMO EVENT</Text>
      </View>
      
      <Text style={styles.desc}>
        Simulate an AI Safety Report to understand why this specific route was recommended over the faster alternatives for Segment {segmentId?.substring(0,6)}.
      </Text>

      <TouchableOpacity 
        style={styles.button} 
        onPress={() => setShowReport(true)}
      >
        <Text style={styles.buttonText}>Simulate Safety Report</Text>
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
  reportContainer: {
    backgroundColor: '#ecfdf5', // light green for success
    borderColor: '#10b981',
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
    color: '#065f46',
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
    color: '#064e3b',
    marginBottom: 10,
    lineHeight: 20,
  },
  button: {
    backgroundColor: '#d97706',
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 6,
  },
  closeButton: {
    backgroundColor: '#10b981',
    paddingVertical: 12,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 6,
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  }
});
