import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Amenity } from '../types/api';

interface Props {
  amenity: Amenity;
  onClose: () => void;
  onNavigate: (amenity: Amenity) => void;
}

export default function AmenityCard({ amenity, onClose, onNavigate }: Props) {
  const isToilet = amenity.type === 'TOILET';

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Text style={styles.emoji}>{isToilet ? '🚽' : amenity.type === 'HOSPITAL' ? '🏥' : '💊'}</Text>
          <View>
            <Text style={styles.typeText}>{amenity.type}</Text>
            <Text style={styles.nameText}>{amenity.name}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.closeButton} onPress={onClose}>
          <Text style={styles.closeText}>✕</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.detailsRow}>
        <View style={styles.badgeRow}>
          {amenity.is_24_7 ? (
            <View style={[styles.badge, styles.greenBadge]}>
              <Text style={styles.greenBadgeText}>Open 24/7</Text>
            </View>
          ) : (
            <View style={[styles.badge, styles.grayBadge]}>
              <Text style={styles.grayBadgeText}>Standard Hours</Text>
            </View>
          )}

          {amenity.is_stale && (
            <View style={[styles.badge, styles.warningBadge]}>
              <Text style={styles.warningBadgeText}>⚠️ May Be Stale</Text>
            </View>
          )}
        </View>

        {amenity.distance_m !== undefined && (
          <Text style={styles.distanceText}>
            {amenity.distance_m >= 1000 
              ? `${(amenity.distance_m / 1000).toFixed(1)} km away` 
              : `${amenity.distance_m.toFixed(0)}m away`}
          </Text>
        )}
      </View>

      {amenity.normalization_notes && (
        <Text style={styles.notesText}>{amenity.normalization_notes}</Text>
      )}

      {amenity.source_date_range && (
        <Text style={styles.metaText}>Source Validity: {amenity.source_date_range}</Text>
      )}

      <View style={styles.actionRow}>
        <TouchableOpacity style={styles.secondaryButton} onPress={onClose}>
          <Text style={styles.secondaryButtonText}>Close</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.primaryButton} onPress={() => onNavigate(amenity)}>
          <Text style={styles.primaryButtonText}>🗺️ Navigate Here</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#e5e7eb',
    marginVertical: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  emoji: {
    fontSize: 24,
    marginRight: 10,
  },
  typeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#6b7280',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  nameText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 2,
  },
  closeButton: {
    padding: 4,
  },
  closeText: {
    fontSize: 18,
    color: '#9ca3af',
    fontWeight: 'bold',
  },
  detailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 8,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  greenBadge: {
    backgroundColor: '#d1fae5',
  },
  greenBadgeText: {
    color: '#065f46',
    fontSize: 11,
    fontWeight: 'bold',
  },
  grayBadge: {
    backgroundColor: '#f3f4f6',
  },
  grayBadgeText: {
    color: '#374151',
    fontSize: 11,
    fontWeight: 'bold',
  },
  warningBadge: {
    backgroundColor: '#fef3c7',
  },
  warningBadgeText: {
    color: '#92400e',
    fontSize: 11,
    fontWeight: 'bold',
  },
  distanceText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#3b82f6',
  },
  notesText: {
    fontSize: 12,
    color: '#4b5563',
    fontStyle: 'italic',
    marginTop: 4,
  },
  metaText: {
    fontSize: 10,
    color: '#9ca3af',
    marginTop: 4,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 14,
    gap: 10,
  },
  secondaryButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#f3f4f6',
  },
  secondaryButtonText: {
    color: '#4b5563',
    fontWeight: '600',
    fontSize: 13,
  },
  primaryButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#0284c7',
  },
  primaryButtonText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 13,
  },
});
