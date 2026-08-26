import React, { useState } from 'react';
import { View, StyleSheet, TouchableOpacity, ScrollView, Modal, ActivityIndicator, Alert } from 'react-native';
import { WashroomResponse } from '../types/api';
import { SakhiCard } from './ui/SakhiCard';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { Ionicons } from '@expo/vector-icons';
import { sakhiApi } from '../api/sakhiApi';

// Haversine distance for UI calculation
function getDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371e3; // meters
  const p1 = lat1 * Math.PI/180;
  const p2 = lat2 * Math.PI/180;
  const dp = (lat2-lat1) * Math.PI/180;
  const dl = (lon2-lon1) * Math.PI/180;

  const a = Math.sin(dp/2) * Math.sin(dp/2) +
            Math.cos(p1) * Math.cos(p2) *
            Math.sin(dl/2) * Math.sin(dl/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

  return R * c;
}

interface Props {
  visible: boolean;
  washroom: WashroomResponse | null;
  distance: number;
  onClose: () => void;
  onFeedbackSubmitted?: () => void;
}

export default function WashroomFacilityCard({ visible, washroom, distance, onClose, onFeedbackSubmitted }: Props) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Feedback form state
  const [isOpen, setIsOpen] = useState<boolean | null>(null);
  const [cleanliness, setCleanliness] = useState<string | null>(null);
  const [safety, setSafety] = useState<string | null>(null);
  const [accessible, setAccessible] = useState<boolean | null>(null);

  React.useEffect(() => {
    if (visible) {
      setIsOpen(null);
      setCleanliness(null);
      setSafety(null);
      setAccessible(null);
      setShowFeedback(false);
    }
  }, [visible, washroom?.id]);

  const distance_value = distance;

  if (!washroom) return null;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await sakhiApi.submitWashroomFeedback(washroom.id, {
        is_open: isOpen ?? true,
        cleanliness: cleanliness || 'Average',
        safety: safety || 'Safe',
        accessible: accessible ?? true
      });
      setShowFeedback(false);
      Alert.alert('Success', 'Feedback submitted successfully.');
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
      onClose();
    } catch (e) {
      console.warn('Failed to submit feedback', e);
      Alert.alert('Error', 'Unable to submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const getFreshnessText = () => {
    if (!washroom.last_verified_timestamp) {
      return "Status not recently verified. Last verified: Never.";
    }
    const verifiedDate = new Date(washroom.last_verified_timestamp);
    const now = new Date();
    const diffHours = (now.getTime() - verifiedDate.getTime()) / (1000 * 60 * 60);

    if (diffHours < 24) {
      return `✓ Verified by ${washroom.verified_count} users. Last reported: ${Math.max(1, Math.round(diffHours))} hours ago.`;
    } else {
      const days = Math.round(diffHours / 24);
      return `⚠️ Status not recently verified. Last verified: ${days} days ago.`;
    }
  };

  const StatusRow = ({ label, value, good, neutral, bad }: any) => {
    let color = '#6B7280';
    let icon = 'ellipse';
    if (value === good) { color = '#10B981'; icon = 'checkmark-circle'; }
    else if (value === neutral) { color = '#F59E0B'; icon = 'alert-circle'; }
    else if (value === bad) { color = '#DC2626'; icon = 'close-circle'; }

    return (
      <View style={styles.statusRow}>
        <SakhiText style={{ width: 100, fontWeight: 'bold' }}>{label}</SakhiText>
        <Ionicons name={icon as any} size={18} color={color} style={{ marginRight: 6 }} />
        <SakhiText style={{ color }}>{value || 'Unknown'}</SakhiText>
      </View>
    );
  };

  return (
    <Modal visible={visible} transparent={true} animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.container}>
          <View style={styles.cardHeader}>
            <View style={{flexDirection: 'row', alignItems: 'center'}}>
              <Ionicons name="water-outline" size={22} color="#7E22CE" style={{marginRight: 8}} />
              <SakhiText variant="h3" style={{ fontWeight: 'bold' }}>
                {washroom.name}
              </SakhiText>
            </View>
            {distance_value !== null && distance_value > 0 && (
              <SakhiText variant="subtext" style={{ color: '#4B5563', fontWeight: 'bold' }}>
                {Math.round(distance_value)} m away
              </SakhiText>
            )}
          </View>
          <SakhiText variant="caption" style={{ marginBottom: 16, color: '#6B7280' }}>
            {washroom.address || 'Location on map'}
          </SakhiText>

          <SakhiText variant="caption" style={{ marginBottom: 16, fontStyle: 'italic' }}>
            {getFreshnessText()}
          </SakhiText>

          {washroom.verified_count === 0 ? (
            <View style={styles.statusBox}>
              <SakhiText style={{ textAlign: 'center', color: '#6B7280', fontStyle: 'italic' }}>No ratings yet. Be the first to provide feedback!</SakhiText>
            </View>
          ) : (
            <View style={styles.statusBox}>
              <StatusRow label="Status" value={washroom.is_open === null ? null : (washroom.is_open ? 'Open' : 'Closed')} good="Open" bad="Closed" />
              <StatusRow label="Cleanliness" value={washroom.cleanliness} good="Clean" neutral="Average" bad="Dirty" />
              <StatusRow label="Safety" value={washroom.safety} good="Safe" neutral="Concern" bad="Unsafe" />
              <StatusRow label="Accessible" value={washroom.accessible === null ? null : (washroom.accessible ? 'Accessible' : 'Not Accessible')} good="Accessible" bad="Not Accessible" />
            </View>
          )}

          {!showFeedback ? (
            <View style={styles.actions}>
              <SakhiButton title="Provide Feedback" variant="secondary" onPress={() => setShowFeedback(true)} style={{ flex: 1, marginRight: 8 }} />
              <SakhiButton title="Close" onPress={onClose} style={{ flex: 1 }} />
            </View>
          ) : (
            <View style={styles.feedbackForm}>
              <SakhiText variant="h3" style={{ marginBottom: 12 }}>Your Feedback</SakhiText>
              
              <SakhiText style={{ fontWeight: 'bold', marginTop: 8 }}>Is it open?</SakhiText>
              <View style={styles.pillRow}>
                <TouchableOpacity onPress={() => setIsOpen(true)} style={[styles.pill, isOpen === true && styles.pillActive]}><SakhiText style={isOpen === true ? styles.pillTextActive : {}}>Yes</SakhiText></TouchableOpacity>
                <TouchableOpacity onPress={() => setIsOpen(false)} style={[styles.pill, isOpen === false && styles.pillActive]}><SakhiText style={isOpen === false ? styles.pillTextActive : {}}>No</SakhiText></TouchableOpacity>
              </View>

              <SakhiText style={{ fontWeight: 'bold', marginTop: 8 }}>Cleanliness</SakhiText>
              <View style={styles.pillRow}>
                <TouchableOpacity onPress={() => setCleanliness('Clean')} style={[styles.pill, cleanliness === 'Clean' && styles.pillActive]}><SakhiText style={cleanliness === 'Clean' ? styles.pillTextActive : {}}>Clean</SakhiText></TouchableOpacity>
                <TouchableOpacity onPress={() => setCleanliness('Average')} style={[styles.pill, cleanliness === 'Average' && styles.pillActive]}><SakhiText style={cleanliness === 'Average' ? styles.pillTextActive : {}}>Average</SakhiText></TouchableOpacity>
                <TouchableOpacity onPress={() => setCleanliness('Dirty')} style={[styles.pill, cleanliness === 'Dirty' && styles.pillActive]}><SakhiText style={cleanliness === 'Dirty' ? styles.pillTextActive : {}}>Dirty</SakhiText></TouchableOpacity>
              </View>

              <SakhiText style={{ fontWeight: 'bold', marginTop: 8 }}>Safety</SakhiText>
              <View style={styles.pillRow}>
                <TouchableOpacity onPress={() => setSafety('Safe')} style={[styles.pill, safety === 'Safe' && styles.pillActive]}><SakhiText style={safety === 'Safe' ? styles.pillTextActive : {}}>Safe</SakhiText></TouchableOpacity>
                <TouchableOpacity onPress={() => setSafety('Concern')} style={[styles.pill, safety === 'Concern' && styles.pillActive]}><SakhiText style={safety === 'Concern' ? styles.pillTextActive : {}}>Concern</SakhiText></TouchableOpacity>
                <TouchableOpacity onPress={() => setSafety('Unsafe')} style={[styles.pill, safety === 'Unsafe' && styles.pillActive]}><SakhiText style={safety === 'Unsafe' ? styles.pillTextActive : {}}>Unsafe</SakhiText></TouchableOpacity>
              </View>

              <SakhiText style={{ fontWeight: 'bold', marginTop: 8 }}>Wheelchair Accessible?</SakhiText>
              <View style={styles.pillRow}>
                <TouchableOpacity onPress={() => setAccessible(true)} style={[styles.pill, accessible === true && styles.pillActive]}><SakhiText style={accessible === true ? styles.pillTextActive : {}}>Yes</SakhiText></TouchableOpacity>
                <TouchableOpacity onPress={() => setAccessible(false)} style={[styles.pill, accessible === false && styles.pillActive]}><SakhiText style={accessible === false ? styles.pillTextActive : {}}>No</SakhiText></TouchableOpacity>
              </View>

              <View style={[styles.actions, { marginTop: 16 }]}>
                <SakhiButton title="Cancel" variant="secondary" onPress={() => setShowFeedback(false)} style={{ flex: 1, marginRight: 8 }} />
                <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit} disabled={submitting}>
                  {submitting ? <ActivityIndicator color="#FFF" /> : <SakhiText style={{ color: '#FFF', fontWeight: 'bold' }}>Submit</SakhiText>}
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#fff',
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  statusBox: {
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  feedbackForm: {
    marginTop: 10,
    borderTopWidth: 1,
    borderColor: '#E5E7EB',
    paddingTop: 16,
  },
  pillRow: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 8,
  },
  pill: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 20,
    paddingVertical: 6,
    paddingHorizontal: 16,
  },
  pillActive: {
    backgroundColor: '#DC2626',
    borderColor: '#DC2626',
  },
  pillTextActive: {
    color: '#FFF',
    fontWeight: 'bold',
  },
  submitBtn: {
    flex: 1,
    backgroundColor: '#DC2626',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  }
});
