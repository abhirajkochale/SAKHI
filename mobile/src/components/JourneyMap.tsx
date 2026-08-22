import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { WebView, WebViewMessageEvent } from 'react-native-webview';

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

function createMapHtml(
  origin: Location | null,
  destination: Location | null,
  segments: JourneySegment[],
  selectedSegmentId: string | null,
  publicToilets: PublicToilet[],
  showPublicToilets: boolean,
): string {
  const payload = JSON.stringify({ origin, destination, segments, selectedSegmentId, publicToilets, showPublicToilets })
    .replace(/</g, '\\u003c');

  return `<!doctype html><html><head>
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>html,body,#map{height:100%;width:100%;margin:0}.leaflet-control-attribution{font-size:9px}</style>
</head><body><div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const data = ${payload};
    const map = L.map('map', { zoomControl: true, attributionControl: true });
    const bounds = [];
    const post = (message) => window.ReactNativeWebView.postMessage(JSON.stringify(message));
    const addPoint = (point) => { if (point) bounds.push([point.latitude, point.longitude]); };
    const marker = (point, label, color) => {
      if (!point) return;
      addPoint(point);
      L.circleMarker([point.latitude, point.longitude], { radius: 8, color, fillColor: color, fillOpacity: 1, weight: 2 })
        .addTo(map).bindPopup(label);
    };
    data.segments.forEach((segment) => {
      const coordinates = (segment.geometry.coordinates || [])
        .filter((coordinate) => Array.isArray(coordinate) && coordinate.length >= 2)
        .map(([longitude, latitude]) => [latitude, longitude]);
      if (coordinates.length < 2) return;
      coordinates.forEach((coordinate) => bounds.push(coordinate));
      const risk = segment.risk_score || 0;
      const color = risk > 65 ? '#ef4444' : risk >= 35 ? '#f59e0b' : '#10b981';
      const selected = segment.segment_id === data.selectedSegmentId;
      L.polyline(coordinates, { color: selected ? '#2563eb' : color, weight: selected ? 7 : 5, opacity: 0.9 })
        .addTo(map).bindPopup('Risk score: ' + risk.toFixed(1))
        .on('click', () => post({ type: 'segment', id: segment.segment_id }));
    });
    marker(data.origin, 'Origin', '#16a34a');
    marker(data.destination, 'Destination', '#dc2626');
    if (data.showPublicToilets) data.publicToilets.forEach((toilet) => {
      addPoint(toilet);
      L.circleMarker([toilet.latitude, toilet.longitude], { radius: 6, color: '#7c3aed', fillColor: '#7c3aed', fillOpacity: 1 })
        .addTo(map).bindPopup('<b>' + toilet.name + '</b><br>' + [toilet.type, toilet.address, toilet.district].filter(Boolean).join(' · '));
    });
    if (bounds.length) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 16 });
    else map.setView([20.5937, 78.9629], 4);
    map.on('click', () => post({ type: 'navigate' }));
  </script>
</body></html>`;
}

export default function JourneyMap(props: JourneyMapProps) {
  const html = useMemo(
    () => createMapHtml(props.origin, props.destination, props.segments, props.selectedSegmentId, props.publicToilets, props.showPublicToilets),
    [props.origin, props.destination, props.segments, props.selectedSegmentId, props.publicToilets, props.showPublicToilets],
  );

  const handleMessage = (event: WebViewMessageEvent) => {
    try {
      const message = JSON.parse(event.nativeEvent.data);
      if (message.type === 'navigate') props.onNavigateRequest();
      if (message.type === 'segment') {
        const segment = props.segments.find((item) => item.segment_id === message.id);
        if (segment) props.onSegmentPress(segment);
      }
    } catch {
      // Ignore malformed messages from the embedded map.
    }
  };

  return (
    <View style={styles.container}>
      <WebView originWhitelist={['*']} source={{ html }} onMessage={handleMessage} javaScriptEnabled domStorageEnabled startInLoadingState renderLoading={() => <Text style={styles.loading}>Loading OpenStreetMap…</Text>} />
      <View pointerEvents="none" style={styles.legend}>
        <Text style={styles.legendTitle}>SAKHI RISK MAP</Text>
        <Text style={styles.legendText}>● Green low   ● Amber moderate   ● Red high</Text>
        {props.showPublicToilets && <Text style={styles.legendText}>● Purple public toilet</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, borderRadius: 8, overflow: 'hidden', marginVertical: 10, backgroundColor: '#e5e7eb' },
  loading: { flex: 1, textAlign: 'center', textAlignVertical: 'center', color: '#4b5563' },
  legend: { position: 'absolute', right: 10, top: 10, backgroundColor: 'rgba(255,255,255,0.94)', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 6, elevation: 2 },
  legendTitle: { color: '#111827', fontSize: 10, fontWeight: 'bold', marginBottom: 2 },
  legendText: { color: '#374151', fontSize: 10, lineHeight: 15 },
});
