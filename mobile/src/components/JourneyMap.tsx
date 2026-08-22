import React, { useEffect, useMemo, useRef } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE, Region } from 'react-native-maps';

import { JourneySegment, Location, PublicToilet } from '../types/api';

interface JourneyMapProps {
  origin: Location | null;
  destination: Location | null;
  segments: JourneySegment[];
  selectedSegmentId: string | null;
  onSegmentPress: (segment: JourneySegment) => void;
  publicToilets: PublicToilet[];
  showPublicToilets: boolean;
  onNavigateRequest: () => void;
}

function riskColor(risk: number | null): string {
  if ((risk ?? 0) > 65) return '#ef4444';
  if ((risk ?? 0) >= 35) return '#f59e0b';
  return '#10b981';
}

function mapRegion(origin: Location | null, destination: Location | null): Region {
  const centerLatitude = ((origin?.latitude ?? 0) + (destination?.latitude ?? 0)) / 2;
  const centerLongitude = ((origin?.longitude ?? 0) + (destination?.longitude ?? 0)) / 2;
  const latitudeDelta = Math.max(Math.abs((origin?.latitude ?? centerLatitude) - (destination?.latitude ?? centerLatitude)) * 1.8, 0.02);
  const longitudeDelta = Math.max(Math.abs((origin?.longitude ?? centerLongitude) - (destination?.longitude ?? centerLongitude)) * 1.8, 0.02);

  return { latitude: centerLatitude, longitude: centerLongitude, latitudeDelta, longitudeDelta };
}

export default function JourneyMap({
  origin,
  destination,
  segments,
  selectedSegmentId,
  onSegmentPress,
  publicToilets,
  showPublicToilets,
  onNavigateRequest,
}: JourneyMapProps) {
  const initialRegion = useMemo(() => mapRegion(origin, destination), [origin, destination]);
  const mapKey = `${origin?.latitude ?? 'none'}-${origin?.longitude ?? 'none'}-${destination?.latitude ?? 'none'}-${destination?.longitude ?? 'none'}`;
  const mapRef = useRef<MapView>(null);
  const routeCoordinates = useMemo(
    () => segments.flatMap((segment) => (segment.geometry.coordinates || [])
      .filter((coordinate) => Array.isArray(coordinate) && coordinate.length >= 2)
      .map(([longitude, latitude]) => ({ latitude, longitude }))),
    [segments],
  );

  useEffect(() => {
    if (routeCoordinates.length >= 2) {
      mapRef.current?.fitToCoordinates(routeCoordinates, {
        animated: true,
        edgePadding: { top: 54, right: 42, bottom: 54, left: 42 },
      });
    }
  }, [routeCoordinates]);

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        key={mapKey}
        style={styles.map}
        provider={PROVIDER_GOOGLE}
        initialRegion={initialRegion}
        onPress={onNavigateRequest}
        showsUserLocation
        showsMyLocationButton
        loadingEnabled
      >
        {segments.map((segment) => {
          const coordinates = (segment.geometry.coordinates || [])
            .filter((coordinate) => Array.isArray(coordinate) && coordinate.length >= 2)
            .map(([longitude, latitude]) => ({ latitude, longitude }));

          if (coordinates.length < 2) return null;

          const isSelected = segment.segment_id === selectedSegmentId;
          return (
            <Polyline
              key={segment.segment_id}
              coordinates={coordinates}
              strokeColor={isSelected ? '#2563eb' : riskColor(segment.risk_score)}
              strokeWidth={isSelected ? 7 : 5}
              tappable
              onPress={() => onSegmentPress(segment)}
            />
          );
        })}

        {origin && <Marker coordinate={origin} pinColor="#16a34a" title="Origin" />}
        {destination && <Marker coordinate={destination} pinColor="#dc2626" title="Destination" />}

        {showPublicToilets && publicToilets.map((toilet) => (
          <Marker
            key={toilet.id}
            coordinate={{ latitude: toilet.latitude, longitude: toilet.longitude }}
            pinColor="#7c3aed"
            title={toilet.name}
            description={[toilet.type, toilet.address, toilet.district].filter(Boolean).join(' · ')}
          />
        ))}
      </MapView>
      <View pointerEvents="none" style={styles.legend}>
        <Text style={styles.legendTitle}>SAKHI RISK MAP</Text>
        <Text style={styles.legendText}>● Green low   ● Amber moderate   ● Red high</Text>
        {showPublicToilets && <Text style={styles.legendText}>● Purple public toilet</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    borderRadius: 8,
    overflow: 'hidden',
    marginVertical: 10,
    backgroundColor: '#e5e7eb',
  },
  map: {
    width: '100%',
    height: '100%',
  },
  legend: {
    position: 'absolute',
    right: 10,
    top: 10,
    backgroundColor: 'rgba(255,255,255,0.94)',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 6,
    elevation: 2,
  },
  legendTitle: {
    color: '#111827',
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 2,
  },
  legendText: {
    color: '#374151',
    fontSize: 10,
    lineHeight: 15,
  },
});
