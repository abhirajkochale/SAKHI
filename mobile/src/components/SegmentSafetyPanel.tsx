import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { JourneySegment } from '../types/api';

interface Props {
  segment: JourneySegment;
}

export default function SegmentSafetyPanel({ segment }: Props) {
  if (!segment.risk_score && !segment.explanation) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Segment Safety</Text>
        <Text style={styles.text}>No risk data available for this segment.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Segment {segment.sequence} Safety</Text>
      
      <View style={styles.row}>
        <View style={styles.metric}>
          <Text style={styles.label}>Contextual Risk</Text>
          <Text style={[styles.value, { color: segment.risk_score! > 50 ? '#ef4444' : '#10b981' }]}>
            {segment.risk_score?.toFixed(1)} / 100
          </Text>
        </View>
        
        <View style={styles.metric}>
          <Text style={styles.label}>Confidence</Text>
          <Text style={[styles.value, { color: segment.confidence_score! > 70 ? '#10b981' : '#f59e0b' }]}>
            {segment.confidence_score?.toFixed(1)}%
          </Text>
        </View>
      </View>

      {segment.explanation && segment.explanation.available && (
        <View style={styles.explanationContainer}>
          <Text style={styles.whyTitle}>Why? (SHAP Factors)</Text>
          
          <Text style={styles.subTitle}>Top Positive Factors (↑ Risk)</Text>
          {segment.explanation.top_positive_factors.map((factor: any) => (
            <View key={factor.feature} style={styles.factorRow}>
              <Text style={styles.factorName}>{factor.feature.replace(/_/g, ' ')}</Text>
              <Text style={styles.factorValue}>+{factor.contribution.toFixed(2)}</Text>
            </View>
          ))}
          
          <Text style={[styles.subTitle, { marginTop: 8 }]}>Top Negative Factors (↓ Risk)</Text>
          {segment.explanation.top_negative_factors.map((factor: any) => (
            <View key={factor.feature} style={styles.factorRow}>
              <Text style={styles.factorName}>{factor.feature.replace(/_/g, ' ')}</Text>
              <Text style={styles.factorValueNegative}>{factor.contribution.toFixed(2)}</Text>
            </View>
          ))}
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
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  metric: {
    flex: 1,
  },
  label: {
    fontSize: 14,
    color: '#6b7280',
  },
  value: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  text: {
    color: '#4b5563',
  },
  explanationContainer: {
    backgroundColor: '#f9fafb',
    padding: 12,
    borderRadius: 8,
  },
  whyTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#111827',
  },
  subTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4b5563',
    marginBottom: 4,
  },
  factorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  factorName: {
    fontSize: 14,
    color: '#374151',
    textTransform: 'capitalize',
  },
  factorValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ef4444', // Red for increased risk
  },
  factorValueNegative: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#10b981', // Green for decreased risk
  }
});
