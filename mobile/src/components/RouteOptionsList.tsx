import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { RouteOption, RouteRankingResponse } from '../types/api';

interface Props {
  ranking: RouteRankingResponse;
  selectedRouteId: string | null;
  onSelectRoute: (route: RouteOption) => void;
}

export default function RouteOptionsList({ ranking, selectedRouteId, onSelectRoute }: Props) {
  const options = [
    { label: '🛡 Safest', key: 'safest', route: ranking.safest_route, desc: 'Safety-prioritized' },
    { label: '⚖ Balanced', key: 'balanced', route: ranking.balanced_route, desc: 'Balanced' },
    { label: '⚡ Fastest', key: 'fastest', route: ranking.fastest_route, desc: 'Time-prioritized' }
  ].filter(opt => opt.route !== null);

  if (options.length === 0) {
    return <Text style={styles.errorText}>No alternative routes available.</Text>;
  }

  // Handle case where backend returns 1 candidate but still maps it to safest/fastest
  // Filter out exact duplicate routes to avoid confusion
  const uniqueOptions = options.reduce((acc, current) => {
    const x = acc.find(item => item.route!.route_id === current.route!.route_id);
    if (!x) {
      return acc.concat([current]);
    } else {
      x.label += ` / ${current.label.split(' ')[1]}`;
      return acc;
    }
  }, [] as typeof options);

  if (uniqueOptions.length === 1) {
    // Only one route candidate exists
    const route = uniqueOptions[0].route!;
    return (
      <View style={styles.container}>
        <Text style={styles.noteText}>Only one candidate route was available for this journey.</Text>
        <TouchableOpacity style={[styles.card, styles.selectedCard]} activeOpacity={1}>
          <Text style={styles.cardTitle}>Primary Route</Text>
          <View style={styles.metricRow}>
            <Text style={styles.metricText}>Risk: {route.risk_score.toFixed(1)}</Text>
            <Text style={styles.metricText}>Dist: {(route.distance_m / 1000).toFixed(2)} km</Text>
            <Text style={styles.metricText}>Time: {Math.round(route.duration_s / 60)} min</Text>
          </View>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {uniqueOptions.map((opt) => {
        const route = opt.route!;
        const isSelected = selectedRouteId === route.route_id;
        
        return (
          <TouchableOpacity 
            key={opt.key}
            style={[styles.card, isSelected && styles.selectedCard]}
            onPress={() => onSelectRoute(route)}
          >
            <Text style={[styles.cardTitle, isSelected && styles.selectedCardTitle]}>{opt.label}</Text>
            
            <View style={styles.metricRow}>
              <Text style={styles.metricText}>Risk: {route.risk_score.toFixed(1)}</Text>
              <Text style={styles.metricText}>Dist: {(route.distance_m / 1000).toFixed(2)} km</Text>
              <Text style={styles.metricText}>Time: {Math.round(route.duration_s / 60)} min</Text>
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 10,
  },
  card: {
    padding: 12,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginBottom: 8,
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
    marginBottom: 8,
  },
  selectedCardTitle: {
    color: '#1d4ed8',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricText: {
    fontSize: 14,
    color: '#4b5563',
  },
  noteText: {
    fontSize: 12,
    color: '#6b7280',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  errorText: {
    color: 'red',
  }
});
