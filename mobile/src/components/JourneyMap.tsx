import React from 'react';
import { StyleSheet, View } from 'react-native';
import MapView, { Marker, Polyline } from 'react-native-maps';
import { JourneySegment, Location } from '../types/api';

interface JourneyMapProps {
  origin: Location | null;
  destination: Location | null;
  segments: JourneySegment[];
  onSegmentPress: (segment: JourneySegment) => void;
  selectedSegmentId: string | null;
}

export default function JourneyMap({ origin, destination, segments, onSegmentPress, selectedSegmentId }: JourneyMapProps) {
  // Center map on origin if available
  const region = origin ? {
    latitude: origin.latitude,
    longitude: origin.longitude,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  } : undefined;

  return (
    <View style={styles.container}>
      <MapView style={styles.map} region={region}>
        {origin && <Marker coordinate={origin} title="Origin" pinColor="green" />}
        {destination && <Marker coordinate={destination} title="Destination" pinColor="red" />}
        
        {segments.map((seg) => {
          // OSRM coordinates are [longitude, latitude] in GeoJSON
          const coordinates = seg.geometry.coordinates.map(coord => ({
            latitude: coord[1],
            longitude: coord[0],
          }));
          
          const isSelected = seg.segment_id === selectedSegmentId;
          const color = isSelected ? '#3b82f6' : '#9ca3af'; // Blue if selected, gray otherwise
          
          return (
            <Polyline
              key={seg.segment_id}
              coordinates={coordinates}
              strokeColor={color}
              strokeWidth={isSelected ? 6 : 4}
              tappable
              onPress={() => onSegmentPress(seg)}
            />
          );
        })}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: 'hidden',
    borderRadius: 8,
    marginVertical: 10,
  },
  map: {
    width: '100%',
    height: '100%',
  },
});
