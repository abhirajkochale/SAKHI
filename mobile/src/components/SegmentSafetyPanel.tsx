import React from 'react';
import { View, StyleSheet, TouchableOpacity } from 'react-native';
import { JourneySegment } from '../types/api';
import { SakhiText } from './ui/SakhiText';
import { SakhiCard } from './ui/SakhiCard';
import { SakhiBadge } from './ui/SakhiBadge';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  segment: JourneySegment;
  onReportIncident?: () => void;
}

export default function SegmentSafetyPanel({ segment, onReportIncident }: Props) {
  if (!segment.risk_score && !segment.explanation) {
    return (
      <SakhiCard style={styles.container}>
        <SakhiText variant="h3">Safety Details</SakhiText>
        <SakhiText variant="body" color="secondary">No risk data available for this segment.</SakhiText>
      </SakhiCard>
    );
  }

  // Preserve SHAP logic exactly as is
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
        const split = remainder / topNeg.length;
        topNeg.forEach((f: any) => f.shap_value += split);
    }
  }

  // Determine Risk Semantic
  const riskScore = segment.risk_score || 0;
  const isHighRisk = riskScore > 65;
  const isModerateRisk = riskScore >= 35 && riskScore <= 65;
  
  let riskStatus: 'success' | 'warning' | 'danger' = 'success';
  let riskLabel = 'LOW RISK';
  if (isHighRisk) { riskStatus = 'danger'; riskLabel = 'HIGH RISK'; }
  else if (isModerateRisk) { riskStatus = 'warning'; riskLabel = 'MODERATE'; }

  return (
    <SakhiCard style={styles.container}>
      {/* Header */}
      <View style={styles.headerRow}>
        <View>
          <SakhiText variant="caption" color="secondary" style={styles.headerSubtitle}>SAFETY DETAILS</SakhiText>
          <SakhiText variant="h3">Segment {segment.sequence}</SakhiText>
        </View>
        <SakhiBadge variant={riskStatus} label={riskLabel} />
      </View>

      {/* Metrics Row */}
      <View style={styles.metricsRow}>
        <View style={styles.metricBlock}>
          <SakhiText variant="caption" color="secondary">Contextual Risk</SakhiText>
          <View style={styles.metricValueRow}>
            <SakhiText variant="h2" color={riskStatus === 'warning' ? undefined : riskStatus} style={riskStatus === 'warning' ? {color: '#F59E0B'} : undefined}>{riskScore.toFixed(1)}</SakhiText>
            <SakhiText variant="body" color="secondary" style={styles.metricSuffix}>/ 100</SakhiText>
          </View>
        </View>
        
        <View style={styles.metricDivider} />

        <View style={styles.metricBlock}>
          <SakhiText variant="caption" color="secondary">Confidence</SakhiText>
          <SakhiText variant="h2" color={segment.confidence_score! > 70 ? 'success' : undefined} style={segment.confidence_score! <= 70 ? {color: '#F59E0B'} : undefined}>
            {segment.confidence_score?.toFixed(1)}%
          </SakhiText>
        </View>
      </View>

      {/* Explanation Section */}
      {segment.explanation && segment.explanation.available && (
        <View style={styles.explanationSection}>
          <SakhiText variant="h3" style={styles.whyTitle}>Why this score?</SakhiText>
          
          {topPos.length > 0 && (
            <View style={styles.factorGroup}>
              <SakhiText variant="caption" color="secondary" style={styles.factorGroupTitle}>Higher Risk</SakhiText>
              {topPos.map((factor: any, index: number) => (
                <View key={`pos-${index}`} style={styles.factorRow}>
                  <View style={styles.factorNameRow}>
                    <Ionicons name="arrow-up" size={16} color="#DC2626" style={styles.factorIcon} />
                    <SakhiText variant="body" style={styles.factorName}>
                      {typeof factor.feature_name === 'string' ? factor.feature_name.replace(/_/g, ' ') : 'Unknown factor'}
                    </SakhiText>
                  </View>
                  <SakhiText variant="body" style={styles.factorPosValue}>+{factor.shap_value?.toFixed(2)}</SakhiText>
                </View>
              ))}
            </View>
          )}
          
          {topNeg.length > 0 && (
            <View style={styles.factorGroup}>
              <SakhiText variant="caption" color="secondary" style={styles.factorGroupTitle}>Lower Risk</SakhiText>
              {topNeg.map((factor: any, index: number) => (
                <View key={`neg-${index}`} style={styles.factorRow}>
                  <View style={styles.factorNameRow}>
                    <Ionicons name="arrow-down" size={16} color="#10B981" style={styles.factorIcon} />
                    <SakhiText variant="body" style={styles.factorName}>
                      {typeof factor.feature_name === 'string' ? factor.feature_name.replace(/_/g, ' ') : 'Unknown factor'}
                    </SakhiText>
                  </View>
                  <SakhiText variant="body" style={styles.factorNegValue}>{factor.shap_value?.toFixed(2)}</SakhiText>
                </View>
              ))}
            </View>
          )}
        </View>
      )}

      {/* Report Action */}
      {onReportIncident && (
        <TouchableOpacity style={styles.reportBtn} onPress={onReportIncident}>
          <View style={styles.reportBtnContent}>
            <Ionicons name="warning-outline" size={18} color="#DC2626" style={styles.reportIcon} />
            <SakhiText variant="body" style={styles.reportBtnText}>Report an incident</SakhiText>
          </View>
          <Ionicons name="arrow-forward" size={18} color="#DC2626" />
        </TouchableOpacity>
      )}
    </SakhiCard>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 12,
    padding: 24,
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: '#F3F4F6',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 12,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  headerSubtitle: {
    letterSpacing: 1,
    marginBottom: 4,
    fontSize: 10,
    fontWeight: 'bold',
  },
  metricsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  metricBlock: {
    flex: 1,
  },
  metricValueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginTop: 4,
  },
  metricSuffix: {
    marginLeft: 4,
    fontSize: 14,
  },
  metricDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 16,
  },
  explanationSection: {
    marginBottom: 8,
  },
  whyTitle: {
    marginBottom: 16,
    color: '#1F2937',
  },
  factorGroup: {
    marginBottom: 16,
  },
  factorGroupTitle: {
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
    fontWeight: '600',
    fontSize: 11,
  },
  factorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  factorNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  factorIcon: {
    marginRight: 8,
  },
  factorName: {
    textTransform: 'capitalize',
    color: '#374151',
    flexShrink: 1,
  },
  factorPosValue: {
    fontWeight: '600',
    color: '#DC2626',
    marginLeft: 12,
  },
  factorNegValue: {
    fontWeight: '600',
    color: '#10B981',
    marginLeft: 12,
  },
  reportBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FEF2F2',
    padding: 16,
    borderRadius: 16,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#FEE2E2',
  },
  reportBtnContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  reportIcon: {
    marginRight: 8,
  },
  reportBtnText: {
    color: '#DC2626',
    fontWeight: '600',
  },
});
