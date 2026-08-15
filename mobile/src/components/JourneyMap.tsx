import React, { useMemo } from 'react';
import { StyleSheet, View } from 'react-native';
import { WebView } from 'react-native-webview';
import { JourneySegment, Location } from '../types/api';

interface JourneyMapProps {
  origin: Location | null;
  destination: Location | null;
  segments: JourneySegment[];
  onSegmentPress: (segment: JourneySegment) => void;
  selectedSegmentId: string | null;
}

export default function JourneyMap({ origin, destination, segments, selectedSegmentId }: JourneyMapProps) {
  const html = useMemo(() => {
    // Build center from origin or default to New Delhi
    const centerLat = origin?.latitude ?? 28.6139;
    const centerLon = origin?.longitude ?? 77.2090;

    // Build GeoJSON FeatureCollection for all segments
    const features = segments.map((seg) => {
      const isSelected = seg.segment_id === selectedSegmentId;
      return {
        type: 'Feature',
        properties: {
          color: isSelected ? '#3b82f6' : '#6b7280',
          weight: isSelected ? 5 : 3,
          opacity: 1.0,
        },
        geometry: seg.geometry, // already a GeoJSON LineString in [lon, lat]
      };
    });

    const geojsonString = JSON.stringify({ type: 'FeatureCollection', features });
    const originJson = origin ? JSON.stringify([origin.latitude, origin.longitude]) : 'null';
    const destinationJson = destination ? JSON.stringify([destination.latitude, destination.longitude]) : 'null';

    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body, #map { width: 100%; height: 100%; }
    .leaflet-control-attribution { font-size: 9px; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    const map = L.map('map', { zoomControl: true }).setView([${centerLat}, ${centerLon}], 14);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Add route segments as GeoJSON (swap lon/lat for Leaflet)
    const data = ${geojsonString};
    if (data.features && data.features.length > 0) {
      const routeLayer = L.geoJSON(data, {
        coordsToLatLng: function(coords) {
          return L.latLng(coords[1], coords[0]); // GeoJSON is [lon, lat], Leaflet needs [lat, lon]
        },
        style: function(feature) {
          return {
            color: feature.properties.color,
            weight: feature.properties.weight,
            opacity: feature.properties.opacity,
          };
        }
      }).addTo(map);

      // Fit map to the route bounds
      try {
        const bounds = routeLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [30, 30] });
        }
      } catch(e) {}
    }

    // Origin marker (green)
    const originCoord = ${originJson};
    if (originCoord) {
      const greenIcon = L.divIcon({
        html: '<div style="background:#16a34a;width:14px;height:14px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,0.4)"></div>',
        iconSize: [14, 14], iconAnchor: [7, 7], className: ''
      });
      L.marker(originCoord, { icon: greenIcon }).addTo(map).bindPopup('Origin');
    }

    // Destination marker (red)
    const destCoord = ${destinationJson};
    if (destCoord) {
      const redIcon = L.divIcon({
        html: '<div style="background:#dc2626;width:14px;height:14px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,0.4)"></div>',
        iconSize: [14, 14], iconAnchor: [7, 7], className: ''
      });
      L.marker(destCoord, { icon: redIcon }).addTo(map).bindPopup('Destination');
    }
  </script>
</body>
</html>`;
  }, [origin, destination, segments, selectedSegmentId]);

  return (
    <View style={styles.container}>
      <WebView
        style={styles.webview}
        source={{ html }}
        scrollEnabled={false}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        originWhitelist={['*']}
      />
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
  webview: {
    width: '100%',
    height: '100%',
  },
});
