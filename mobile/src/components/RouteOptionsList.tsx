import React from 'react';
import { View, StyleSheet } from 'react-native';
import { RouteOption, RouteRankingResponse } from '../types/api';
import { SakhiCard } from './ui/SakhiCard';
import { SakhiText } from './ui/SakhiText';
import { SakhiButton } from './ui/SakhiButton';
import { SakhiBadge } from './ui/SakhiBadge';
import { useTheme } from '../theme';

interface Props {
  ranking: RouteRankingResponse;
  selectedRouteId: string | null;
  onSelectRoute: (route: RouteOption) => void;
  onOpenMaps?: () => void;
}

export default function RouteOptionsList({ ranking, selectedRouteId, onSelectRoute, onOpenMaps }: Props) {
  const { spacing, colors } = useTheme();
  
  // Collect all route slots that are non-null
  const rawOptions = [
    { label: 'SAFEST (Recommended)', key: 'safest', route: ranking.safest_route, badgeVariant: 'success' as const },
    { label: 'BALANCED', key: 'balanced', route: ranking.balanced_route, badgeVariant: 'info' as const },
    { label: 'FASTEST', key: 'fastest', route: ranking.fastest_route, badgeVariant: 'warning' as const },
  ];

  const validOptions = rawOptions.filter(opt => opt.route != null) as { 
    label: string; 
    key: string; 
    route: RouteOption; 
    badgeVariant: 'success' | 'info' | 'warning' 
  }[];

  // Deduplicate by route_id
  const uniqueOptions: typeof validOptions = [];
  for (const opt of validOptions) {
    const existing = uniqueOptions.find(u => u.route.route_id === opt.route.route_id);
    if (!existing) {
      uniqueOptions.push({ ...opt });
    }
  }

  if (uniqueOptions.length === 0) {
    return <SakhiText color="danger">No routes available.</SakhiText>;
  }

  const isSingleRoute = uniqueOptions.length === 1;

  const getRiskLevel = (score: number) => {
    if (score >= 70) return 'HIGH';
    if (score >= 40) return 'MODERATE';
    return 'LOW';
  };

  const getRiskColor = (score: number) => {
    if (score >= 70) return colors.danger;
    if (score >= 40) return colors.warning;
    return colors.success;
  };

  return (
    <View style={styles.container}>
      <SakhiText variant="h2" style={{ marginBottom: spacing.md }}>
        Choose a different route
      </SakhiText>

      {uniqueOptions.map((opt) => {
        const isSelected = selectedRouteId === opt.route.route_id;
        const isSafest = opt.key === 'safest';

        return (
          <SakhiCard 
            key={opt.key}
            elevated
            style={[
              styles.card,
              isSelected && { borderColor: colors.primary, borderWidth: 2 }
            ]}
          >
            {/* Header Row */}
            <View style={styles.headerRow}>
              <SakhiText variant="h3" style={{ fontWeight: 'bold' }}>
                {isSingleRoute ? 'Best available route' : opt.label}
              </SakhiText>
              <SakhiBadge 
                label={`Risk: ${opt.route.risk_score.toFixed(1)}/100`} 
                variant={opt.badgeVariant} 
              />
            </View>

            {/* Sub-header text for single route fallback */}
            {isSingleRoute && (
              <SakhiText variant="caption" color="muted" style={{ marginBottom: spacing.sm }}>
                No comparable alternative route was available for this journey.
              </SakhiText>
            )}

            {/* Risk Level */}
            {!isSingleRoute && (
              <SakhiText variant="subtext" style={{ marginBottom: spacing.sm, color: getRiskColor(opt.route.risk_score) }}>
                Risk level: <SakhiText style={{ fontWeight: 'bold', color: getRiskColor(opt.route.risk_score) }}>{getRiskLevel(opt.route.risk_score)}</SakhiText>
              </SakhiText>
            )}

            {/* Metrics Row (Time / Distance) */}
            <View style={styles.metricsRow}>
              <View style={{ marginRight: spacing.xl }}>
                <SakhiText variant="body" style={{ fontWeight: 'bold' }}>
                  {Math.round(opt.route.duration_s / 60)} min
                </SakhiText>
              </View>
              <View>
                <SakhiText variant="body" style={{ fontWeight: 'bold' }}>
                  {(opt.route.distance_m / 1000).toFixed(1)} km
                </SakhiText>
              </View>
            </View>

            {/* Amenities */}
            {opt.route.amenity_counts && (
              <View style={styles.amenitiesRow}>
                <SakhiText variant="subtext" color="secondary" style={{ marginRight: spacing.md }}>
                  🚻 {opt.route.amenity_counts.washrooms}
                </SakhiText>
                <SakhiText variant="subtext" color="secondary" style={{ marginRight: spacing.md }}>
                  🏥 {opt.route.amenity_counts.medical}
                </SakhiText>
                <SakhiText variant="subtext" color="secondary">
                  👮 {opt.route.amenity_counts.police}
                </SakhiText>
              </View>
            )}

            {/* Action */}
            <View style={{ marginTop: spacing.md }}>
              <SakhiButton 
                title={isSelected ? "↗ Open in Google Maps" : (isSingleRoute ? "Start Journey →" : "Choose Route →")} 
                variant={isSelected ? "primary" : "secondary"}
                onPress={() => {
                  if (isSelected && onOpenMaps) {
                    onOpenMaps();
                  } else {
                    onSelectRoute(opt.route);
                  }
                }}
                style={{ paddingVertical: spacing.sm }}
              />
            </View>
          </SakhiCard>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    marginVertical: 16 
  },
  card: {
    marginBottom: 16,
    padding: 16,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricsRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  amenitiesRow: {
    flexDirection: 'row',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6', // gray100
  }
});
