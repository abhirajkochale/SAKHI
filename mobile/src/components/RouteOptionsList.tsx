import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { RouteOption, RouteRankingResponse } from '../types/api';

interface Props {
  ranking: RouteRankingResponse;
  selectedRouteId: string | null;
  onSelectRoute: (route: RouteOption) => void;
}

export default function RouteOptionsList({ ranking, selectedRouteId, onSelectRoute }: Props) {
  // Collect all route slots that are non-null
  const rawOptions = [
    { label: '✅ Recommended (Safest)', key: 'safest', route: ranking.safest_route },
    { label: '⚖ Balanced', key: 'balanced', route: ranking.balanced_route },
    { label: '⚠️ High Risk (Not Preferred)', key: 'fastest', route: ranking.fastest_route },
  ].filter(opt => opt.route != null) as { label: string; key: string; route: RouteOption }[];

  // Deduplicate by route_id, merging labels for routes that serve multiple roles
  const uniqueOptions: { label: string; key: string; route: RouteOption }[] = [];
  for (const opt of rawOptions) {
    const existing = uniqueOptions.find(u => u.route.route_id === opt.route.route_id);
    if (existing) {
      // Append only the emoji+word, e.g. "🛡 Safest / ⚡ Fastest"
      existing.label += ` / ${opt.label}`;
    } else {
      uniqueOptions.push({ ...opt });
    }
  }

  if (uniqueOptions.length === 0) {
    return <Text style={styles.errorText}>No routes available.</Text>;
  }

  const isSingleRoute = uniqueOptions.length === 1;

  return (
    <View style={styles.container}>
      {isSingleRoute && (
        <Text style={styles.noteText}>
          Route risk level: {riskLabel(uniqueOptions[0].route.risk_score)}
        </Text>
      )}
      {uniqueOptions.map((opt) => {
        const isSelected = selectedRouteId === opt.route.route_id;

        return (
          <TouchableOpacity
            key={opt.key}
            style={[styles.card, isSelected && styles.selectedCard]}
            onPress={() => onSelectRoute(opt.route)}
            activeOpacity={0.75}
          >
            <Text style={[styles.cardTitle, isSelected && styles.selectedCardTitle]}>
              {isSingleRoute ? riskLabel(opt.route.risk_score) : opt.label}
            </Text>

            <View style={styles.metricRow}>
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>Risk</Text>
                <Text style={[styles.metricValue, { color: riskColor(opt.route.risk_score) }]}>
                  {opt.route.risk_score.toFixed(1)}
                </Text>
              </View>
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>Distance</Text>
                <Text style={styles.metricValue}>{(opt.route.distance_m / 1000).toFixed(2)} km</Text>
              </View>
              <View style={styles.metric}>
                <Text style={styles.metricLabel}>Time</Text>
                <Text style={styles.metricValue}>{Math.round(opt.route.duration_s / 60)} min</Text>
              </View>
            </View>
            
            {opt.route.amenity_counts && (
              <View style={styles.amenityRow}>
                <Text style={styles.amenityText}>
                  🚻 Washrooms: {opt.route.amenity_counts.washrooms} | 🏥 Medical: {opt.route.amenity_counts.medical} | 🚓 Police: {opt.route.amenity_counts.police}
                </Text>
              </View>
            )}
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

function riskColor(score: number): string {
  if (score >= 70) return '#dc2626'; // red
  if (score >= 40) return '#d97706'; // amber
  return '#16a34a'; // green
}

function riskLabel(score: number): string {
  if (score >= 70) return '🚨 Only Route — High Risk';
  if (score >= 40) return '⚠️ Only Route — Moderate Risk';
  return '✅ Only Route — Low Risk';
}

const styles = StyleSheet.create({
  container: { marginVertical: 10 },
  card: {
    padding: 14,
    backgroundColor: '#fff',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  selectedCard: {
    borderColor: '#3b82f6',
    backgroundColor: '#eff6ff',
    borderWidth: 2,
  },
  cardTitle: {
    fontWeight: 'bold',
    fontSize: 16,
    color: '#374151',
    marginBottom: 10,
  },
  selectedCardTitle: { color: '#1d4ed8' },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: { alignItems: 'center' },
  metricLabel: {
    fontSize: 11,
    color: '#9ca3af',
    marginBottom: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  noteText: {
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  errorText: { color: 'red' },
  amenityRow: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6',
    alignItems: 'center',
  },
  amenityText: {
    fontSize: 11,
    color: '#4b5563',
    fontWeight: '500',
  }
});
