import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { WebView, WebViewMessageEvent } from 'react-native-webview';
import { JourneySegment, Location, WashroomResponse } from '../types/api';

interface JourneyMapProps { origin: Location | null; destination: Location | null; segments: JourneySegment[]; selectedSegmentId: string | null; onSegmentPress: (segment: JourneySegment) => void; washrooms: WashroomResponse[]; showWashrooms: boolean; onNavigateRequest: () => void; onWashroomPress: (washroom: WashroomResponse) => void; }

const MAP_HTML = `<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" /><link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" /><style>html,body,#map{height:100%;width:100%;margin:0}.leaflet-control-attribution{font-size:9px}</style></head><body><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script><script>
const map=L.map('map',{zoomControl:true,attributionControl:true}).setView([20.5937,78.9629],4);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);let routeLayer=L.layerGroup().addTo(map),amenityLayer=L.layerGroup().addTo(map);const post=(message)=>window.ReactNativeWebView.postMessage(JSON.stringify(message));const stop=(event)=>{if(event&&event.originalEvent)L.DomEvent.stopPropagation(event.originalEvent)};const riskColor=(risk)=>risk>65?'#ef4444':risk>=35?'#f59e0b':'#10b981';
window.updateSakhiMap=(data)=>{routeLayer.clearLayers();amenityLayer.clearLayers();const bounds=[];const addBound=(point)=>{if(point)bounds.push([point.latitude,point.longitude])};const marker=(point,label,color)=>{if(!point)return;L.circleMarker([point.latitude,point.longitude],{radius:8,color,fillColor:color,fillOpacity:1,weight:2}).addTo(routeLayer).bindPopup(label).on('click',stop)};const toiletIcon=L.divIcon({className:'sakhi-toilet-marker',html:'<div style="background:#7c3aed;border:2px solid white;border-radius:16px;color:white;font-size:17px;line-height:28px;text-align:center;width:30px;height:30px;box-shadow:0 1px 4px #444">🚻</div>',iconSize:[30,30],iconAnchor:[15,15],popupAnchor:[0,-15]});(data.segments||[]).forEach((segment)=>{const coordinates=(segment.geometry.coordinates||[]).filter((coordinate)=>Array.isArray(coordinate)&&coordinate.length>=2).map(([longitude,latitude])=>[latitude,longitude]);if(coordinates.length<2)return;coordinates.forEach((coordinate)=>bounds.push(coordinate));const selected=segment.segment_id===data.selectedSegmentId;L.polyline(coordinates,{color:selected?'#2563eb':riskColor(segment.risk_score||0),weight:selected?7:5,opacity:.9}).addTo(routeLayer).bindPopup('Risk score: '+(segment.risk_score||0).toFixed(1)).on('click',(event)=>{stop(event);post({type:'segment',id:segment.segment_id})})});marker(data.origin,'Origin','#16a34a');marker(data.destination,'Destination','#dc2626');addBound(data.origin);addBound(data.destination);if(data.showWashrooms)(data.washrooms||[]).forEach((washroom)=>{addBound(washroom);L.marker([washroom.latitude,washroom.longitude],{icon:toiletIcon}).addTo(amenityLayer).on('click',(event)=>{stop(event);post({type:'washroom',id:washroom.id})})});if(data.shouldFitBounds&&bounds.length>1)map.fitBounds(bounds,{padding:[24,24],maxZoom:16})};map.on('click',()=>post({type:'navigate'}));post({type:'ready'});
</script></body></html>`;

function updateScript(props: JourneyMapProps, shouldFitBounds: boolean): string {
  const data = JSON.stringify({ origin: props.origin, destination: props.destination, segments: props.segments, selectedSegmentId: props.selectedSegmentId, washrooms: props.washrooms, showWashrooms: props.showWashrooms, shouldFitBounds }).replace(/</g, '\\u003c');
  return `window.updateSakhiMap(${data}); true;`;
}

export default function JourneyMap(props: JourneyMapProps) {
  const mapRef = useRef<WebView>(null);
  const [ready, setReady] = useState(false);
  const lastRouteKey = useRef<string | null>(null);
  const lastToiletVisibility = useRef<boolean | null>(null);
  const lastToiletCount = useRef(0);
  const routeKey = props.segments.map((segment) => segment.segment_id).join('|');
  useEffect(() => {
    if (!ready) return;
    const shouldFitBounds = lastRouteKey.current !== routeKey
      || (props.showWashrooms && (lastToiletVisibility.current !== props.showWashrooms || lastToiletCount.current !== props.washrooms.length));
    mapRef.current?.injectJavaScript(updateScript(props, shouldFitBounds));
    lastRouteKey.current = routeKey;
    lastToiletVisibility.current = props.showWashrooms;
    lastToiletCount.current = props.washrooms.length;
  }, [ready, routeKey, props.origin, props.destination, props.segments, props.selectedSegmentId, props.washrooms, props.showWashrooms]);

  const handleMessage = (event: WebViewMessageEvent) => {
    try { 
      const message = JSON.parse(event.nativeEvent.data); 
      if (message.type === 'ready') setReady(true); 
      if (message.type === 'navigate') props.onNavigateRequest(); 
      if (message.type === 'segment') { 
        const segment = props.segments.find((item) => item.segment_id === message.id); 
        if (segment) props.onSegmentPress(segment); 
      }
      if (message.type === 'washroom') {
        const washroom = props.washrooms.find((item) => item.id === message.id);
        if (washroom) props.onWashroomPress(washroom);
      }
    } catch { /* Ignore malformed map messages. */ }
  };
  return <View style={styles.container}><WebView ref={mapRef} originWhitelist={['*']} source={{ html: MAP_HTML }} onMessage={handleMessage} javaScriptEnabled domStorageEnabled startInLoadingState renderLoading={() => <Text style={styles.loading}>Loading OpenStreetMap…</Text>} /><View pointerEvents="none" style={styles.legend}><Text style={styles.legendTitle}>SAKHI RISK MAP</Text><Text style={styles.legendText}>● Green low   ● Amber moderate   ● Red high</Text>{props.showWashrooms && <Text style={styles.legendText}>● Purple washroom</Text>}</View></View>;
}

const styles = StyleSheet.create({ container: { flex: 1, borderRadius: 8, overflow: 'hidden', marginVertical: 10, backgroundColor: '#e5e7eb' }, loading: { flex: 1, textAlign: 'center', textAlignVertical: 'center', color: '#4b5563' }, legend: { position: 'absolute', right: 10, top: 10, backgroundColor: 'rgba(255,255,255,0.94)', borderRadius: 6, paddingHorizontal: 8, paddingVertical: 6, elevation: 2 }, legendTitle: { color: '#111827', fontSize: 10, fontWeight: 'bold', marginBottom: 2 }, legendText: { color: '#374151', fontSize: 10, lineHeight: 15 } });
