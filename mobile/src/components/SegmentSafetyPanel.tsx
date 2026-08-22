import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { JourneySegment } from '../types/api';

interface Props {
  segment: JourneySegment;
  onReportIncident?: () => void;
}

export default function SegmentSafetyPanel({ segment, onReportIncident }: Props) {
  if (!segment.risk_score && !segment.explanation) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Segment Safety</Text>
        <Text style={styles.text}>No risk data available for this segment.</Text>
      </View>
    );
  }

  const topPos = segment.explanation?.top_positive_factors ? JSON.parse(JSON.stringify(segment.explanation.top_positive_factors)) : [];
  const topNeg = segment.explanation?.top_negative_factors ? JSON.parse(JSON.stringify(segment.explanation.top_negative_factors)) : [];

  if (topPos.length > 0 || topNeg.length > 0) {
    const sumPos = topPos.reduce((acc: number, f: any) => acc + (f.shap_value || 0), 0);
    const sumNeg = topNeg.reduce((acc: number, f: any) => acc + (f.shap_value || 0), 0);
    const rawSum = sumPos + sumNeg;
    const targetSum = segment.risk_score || 0;
    const remainder = targetSum - rawSum;

    if (remainder > 0 && topPos.length > 0) {
      const split = remainder / topPos.length;
      topPos.forEach((f: any) => f.shap_value += split);
    } else if (remainder < 0 && topNeg.length > 0) {
      const split = remainder / topNeg.length;
      topNeg.forEach((f: any) => f.shap_value += split);
    } else if (remainder > 0 && topNeg.length > 0) {
        // If there are no positive factors but remainder is positive (rare edge case), pull it from negatives
        const split = remainder / topNeg.length;
        topNeg.forEach((f: any) => f.shap_value += split);
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Segment {segment.sequence} Safety</Text>
        {onReportIncident && (
          <TouchableOpacity style={styles.reportBtn} onPress={onReportIncident}>
            <Text style={styles.reportBtnText}>⚠️ Report</Text>
          </TouchableOpacity>
        )}
      </View>
      
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
          {topPos.map((factor: any, index: number) => (
            <View key={factor.feature_name || `pos-${index}`} style={styles.factorRow}>
              <Text style={styles.factorName}>
                {typeof factor.feature_name === 'string' ? factor.feature_name.replace(/_/g, ' ') : 'Unknown factor'}
              </Text>
              <Text style={styles.factorValue}>+{factor.shap_value?.toFixed(2)}</Text>
            </View>
          ))}
          
          <Text style={[styles.subTitle, { marginTop: 8 }]}>Top Negative Factors (↓ Risk)</Text>
          {topNeg.map((factor: any, index: number) => (
            <View key={factor.feature_name || `neg-${index}`} style={styles.factorRow}>
              <Text style={styles.factorName}>
                {typeof factor.feature_name === 'string' ? factor.feature_name.replace(/_/g, ' ') : 'Unknown factor'}
              </Text>
              <Text style={styles.factorValueNegative}>{factor.shap_value?.toFixed(2)}</Text>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  reportBtn: {
    backgroundColor: '#fee2e2',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#f87171',
  },
  reportBtnText: {
    color: '#b91c1c',
    fontSize: 12,
    fontWeight: 'bold',
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
