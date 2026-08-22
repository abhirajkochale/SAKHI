import React, { useState, useEffect } from 'react';
import { Alert, Linking, ScrollView, StyleSheet, View, Text, TouchableOpacity } from 'react-native';
import * as Location from 'expo-location';
import JourneyForm from '../components/JourneyForm';
import JourneyMap from '../components/JourneyMap';
import RouteOptionsList from '../components/RouteOptionsList';
import SegmentSafetyPanel from '../components/SegmentSafetyPanel';
import ContextUpdatePanel from '../components/ContextUpdatePanel';
import EmergencyPanel from '../components/EmergencyPanel';
import DeadManSwitchPanel from '../components/DeadManSwitchPanel';
import ReportIncidentModal from '../components/ReportIncidentModal';
import QuickFindModal from '../components/QuickFindModal';
import WashroomFacilityCard from '../components/WashroomFacilityCard';
import { sakhiApi } from '../api/sakhiApi';
import { cacheJourney, getCachedJourney } from '../api/cache';
import { useAccessibility } from '../contexts/AccessibilityContext';
import { JourneyResponse, RouteOption, JourneySegment, ContextUpdateResponse, WashroomResponse, Location as ApiLocation } from '../types/api';
import { calculateDistance } from '../utils/distance';
import { useTheme } from '../theme';
import { SakhiText } from '../components/ui/SakhiText';
import { SakhiButton } from '../components/ui/SakhiButton';

 // 5 seconds cooldown between SOS triggers

export default function JourneyDashboard() {
  const { isAccessibleMode, toggleAccessibleMode } = useAccessibility();
  const { colors, spacing } = useTheme();
  const [loading, setLoading] = useState(false);
  const [journey, setJourney] = useState<JourneyResponse | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<RouteOption | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<JourneySegment | null>(null);
  
  const [showReportModal, setShowReportModal] = useState(false);
  const [showQuickFindModal, setShowQuickFindModal] = useState(false);

  const [updateResult, setUpdateResult] = useState<ContextUpdateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  
  const [showWashrooms, setShowWashrooms] = useState(false);
  const [washrooms, setWashrooms] = useState<WashroomResponse[]>([]);
  const [washroomsLoading, setWashroomsLoading] = useState(false);
  const [washroomsError, setWashroomsError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<Location.LocationObject | null>(null);
  const [selectedWashroom, setSelectedWashroom] = useState<WashroomResponse | null>(null);


  useEffect(() => {
    (async () => {
      try {
        let { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          console.warn('Permission to access location was denied');
          return;
        }
        
        let location = await Location.getCurrentPositionAsync({});
        setUserLocation(location);

        const locationSubscription = await Location.watchPositionAsync(
          { accuracy: Location.Accuracy.High, timeInterval: 5000, distanceInterval: 10 },
          (loc) => { setUserLocation(loc); }
        );
        
        return () => { locationSubscription.remove(); };
      } catch (err) {
        console.warn('Could not fetch location:', err);
      }
    })();
  }, []);

  useEffect(() => {
    if (!showWashrooms || washrooms.length || washroomsLoading || washroomsError) return;
    
    // Determine center for washroom search
    let lat: number;
    let lon: number;
    if (userLocation) {
      lat = userLocation.coords.latitude;
      lon = userLocation.coords.longitude;
    } else if (journey) {
      lat = journey.origin.latitude;
      lon = journey.origin.longitude;
    } else {
      // Default to Delhi if no location available
      lat = 28.6139;
      lon = 77.2090;
    }

    let cancelled = false;
    setWashroomsLoading(true);
    // Fetch washrooms using location
    sakhiApi.getWashrooms(lat, lon, 10.0)
      .then((data) => { if (!cancelled) setWashrooms(data); })
      .catch(() => { if (!cancelled) setWashroomsError('Washroom locations are unavailable right now.'); })
      .finally(() => { if (!cancelled) setWashroomsLoading(false); });
    return () => { cancelled = true; };
  }, [showWashrooms, washrooms.length, washroomsLoading, washroomsError, userLocation, journey]);

  const handleAnalyze = async (origin: ApiLocation, destination: ApiLocation) => {
    setLoading(true);
    setError(null);
    setUpdateResult(null);
    setIsOffline(false);
    try {
      const response = await sakhiApi.createJourney(origin, destination);
      setJourney(response);
      const initialRoute: RouteOption = response.ranking?.safest_route ?? {
        route_id: 'primary', mode: 'safest', rank: 1, distance_m: response.distance_m, duration_s: response.duration_s,
        risk_score: 0, confidence: 0, max_segment_risk: 0, uncertainty_penalty: 0, route_cost: 0, segments: response.segments,
      };
      setSelectedRoute(initialRoute);
      setSelectedSegment(initialRoute.segments && initialRoute.segments.length > 0 ? initialRoute.segments[0] : null);
      void cacheJourney(response);
    } catch (err: any) {
      console.error(err);
      // Try offline fallback
      const cached = await getCachedJourney();
      if (cached) {
        setIsOffline(true);
        setJourney(cached);
        if (cached.ranking && cached.ranking.safest_route) {
          setSelectedRoute(cached.ranking.safest_route);
          setSelectedSegment(cached.ranking.safest_route.segments.length > 0 ? cached.ranking.safest_route.segments[0] : null);
        }
      } else {
        setError(sakhiApi.getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const openSelectedRouteInGoogleMaps = async () => {
    if (!journey) return;

    const routeSegments = selectedRoute?.segments || journey.segments;
    const coordinates = routeSegments.flatMap((segment) => segment.geometry.coordinates || []);
    const waypointIndexes = [0.25, 0.5, 0.75]
      .map((position) => coordinates[Math.round((coordinates.length - 1) * position)])
      .filter((coordinate): coordinate is number[] => Array.isArray(coordinate) && coordinate.length >= 2);

    const params = new URLSearchParams({
      api: '1',
      origin: `${journey.origin.latitude},${journey.origin.longitude}`,
      destination: `${journey.destination.latitude},${journey.destination.longitude}`,
      travelmode: 'walking',
      dir_action: 'navigate',
    });
    if (waypointIndexes.length) {
      params.set('waypoints', waypointIndexes.map(([longitude, latitude]) => `${latitude},${longitude}`).join('|'));
    }

    const url = `https://www.google.com/maps/dir/?${params.toString()}`;
    if (!await Linking.canOpenURL(url)) {
      Alert.alert('Google Maps unavailable', 'Unable to open navigation on this device.');
      return;
    }
    await Linking.openURL(url);
  };

  const currentStyles = isAccessibleMode ? accessibleStyles : styles;

  const renderHome = () => (
    <>
      <View style={{ marginBottom: spacing.xl, marginTop: spacing.lg }}>
        <SakhiText variant="h1" color="primary" style={{ fontSize: 32, marginBottom: spacing.sm }}>
          Your Safety,{"\n"}Our Priority. ♥
        </SakhiText>
        <SakhiText variant="body" color="secondary" style={{ fontSize: 16 }}>
          Find the safest way, wherever you go.
        </SakhiText>
      </View>

      <JourneyForm onAnalyze={handleAnalyze} loading={loading} />
      
      {error && (
        <View style={currentStyles.errorBox}>
          <Text style={currentStyles.errorText}>{error}</Text>
        </View>
      )}

      <View style={{ marginTop: spacing.xl, paddingHorizontal: spacing.sm }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md }}>
          <Text style={{ fontSize: 24, marginRight: spacing.md }}>🛡</Text>
          <View>
            <SakhiText variant="body" style={{ fontWeight: 'bold' }}>Safe Routes</SakhiText>
            <SakhiText variant="caption" color="muted">Live contextual safety analysis</SakhiText>
          </View>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md }}>
          <Text style={{ fontSize: 24, marginRight: spacing.md }}>📍</Text>
          <View>
            <SakhiText variant="body" style={{ fontWeight: 'bold' }}>Real-time Alerts</SakhiText>
            <SakhiText variant="caption" color="muted">Stay informed while travelling</SakhiText>
          </View>
        </View>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md }}>
          <Text style={{ fontSize: 24, marginRight: spacing.md }}>♡</Text>
          <View>
            <SakhiText variant="body" style={{ fontWeight: 'bold' }}>Always With You</SakhiText>
            <SakhiText variant="caption" color="muted">Quick access to help</SakhiText>
          </View>
        </View>
      </View>
    </>
  );

  const renderDashboard = () => {
    if (!journey) return null;
    return (
      <>
        {isOffline && (
          <View style={currentStyles.offlineBanner}>
            <Text style={currentStyles.offlineBannerText}>⚠️ OFFLINE MODE: Using cached route data. Live context updates unavailable.</Text>
          </View>
        )}

        <View style={currentStyles.mapContainer}>
          <JourneyMap 
            origin={journey.origin}
            destination={journey.destination}
            segments={selectedRoute?.segments || journey.segments}
            selectedSegmentId={selectedSegment?.segment_id || null}
            onSegmentPress={setSelectedSegment}
            washrooms={washrooms}
            showWashrooms={showWashrooms}
            onNavigateRequest={openSelectedRouteInGoogleMaps}
            onWashroomPress={(washroom) => {
              setSelectedWashroom(washroom);
            }}
          />
        </View>

        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Navigate selected safe route in Google Maps"
          onPress={openSelectedRouteInGoogleMaps}
          style={currentStyles.googleMapsButton}
        >
          <Text style={currentStyles.googleMapsButtonText}>NAVIGATE SAFE ROUTE IN GOOGLE MAPS</Text>
        </TouchableOpacity>
        <Text style={currentStyles.googleMapsHint}>Tap the map or this button to open the selected route in Google Maps.</Text>

        <View style={currentStyles.amenityToggleRow}>
          <View style={{ flex: 1 }}>
            <Text style={currentStyles.amenityToggleTitle}>Right to PEE (Washrooms)</Text>
            <Text style={currentStyles.amenityToggleCaption}>
              {washroomsLoading ? 'Loading washroom locations…' : washroomsError || (washrooms.length ? `${washrooms.length} washrooms available nearby` : 'Turn on to find nearby washrooms')}
            </Text>
          </View>
          <TouchableOpacity
            accessibilityRole="switch"
            accessibilityState={{ checked: showWashrooms }}
            accessibilityLabel="Show washroom locations"
            onPress={() => {
              if (!showWashrooms) setWashroomsError(null);
              setShowWashrooms((visible) => !visible);
            }}
            style={[currentStyles.amenityToggle, showWashrooms && currentStyles.amenityToggleActive]}
          >
            <Text style={[currentStyles.amenityToggleText, showWashrooms && currentStyles.amenityToggleTextActive]}>
              {showWashrooms ? 'LOCATIONS ON' : 'SHOW LOCATIONS'}
            </Text>
          </TouchableOpacity>
        </View>
        
        {isAccessibleMode && (
          <View style={{backgroundColor: '#fff', padding: 8, borderWidth: 2, borderColor: '#000', marginBottom: 10}}>
            <Text style={{fontWeight: 'bold', fontSize: 18, color: '#000'}}>Map Legend:</Text>
            <Text style={{fontSize: 18, color: '#000'}}>{"• Green line = Low Risk (<35)"}</Text>
            <Text style={{fontSize: 18, color: '#000'}}>• Orange/Amber line = Moderate Risk (35-65)</Text>
            <Text style={{fontSize: 18, color: '#000'}}>{"• Red line = High Risk (>65)"}</Text>
            <Text style={{fontSize: 18, color: '#000'}}>• Thick blue line = Currently selected segment</Text>
          </View>
        )}

        {journey.ranking && (
          <RouteOptionsList 
            ranking={journey.ranking}
            selectedRouteId={selectedRoute?.route_id || null}
            onSelectRoute={(route) => {
              setSelectedRoute(route);
              setSelectedSegment(route.segments && route.segments.length > 0 ? route.segments[0] : null);
            }}
          />
        )}

        {selectedSegment ? (
          <>
            <SegmentSafetyPanel 
              segment={selectedSegment} 
              onReportIncident={() => setShowReportModal(true)}
            />
            
            <ContextUpdatePanel 
              segmentId={selectedSegment.segment_id}
              journeyId={journey.journey_id}
              onUpdateResult={(result) => {
                setUpdateResult(result);
              }}
            />

            {updateResult && (
              <View style={currentStyles.updateResultBox}>
                <Text style={currentStyles.updateResultTitle}>🔄 Dynamic Route Re-Ranking</Text>
                <Text style={currentStyles.updateReason}>{updateResult.reason}</Text>
                <View style={currentStyles.beforeAfterRow}>
                  <View style={currentStyles.beforeBox}>
                    <Text style={currentStyles.baLabel}>BEFORE</Text>
                    <Text style={currentStyles.baValue}>{updateResult.before.safest_route_id?.substring(0,6) || "N/A"}</Text>
                  </View>
                  <Text style={currentStyles.arrow}>→</Text>
                  <View style={currentStyles.afterBox}>
                    <Text style={currentStyles.baLabel}>AFTER</Text>
                    <Text style={currentStyles.baValue}>{updateResult.after.safest_route_id?.substring(0,6) || "N/A"}</Text>
                  </View>
                </View>
                {updateResult.after && (
                  <Text style={{fontSize: isAccessibleMode ? 16 : 12, marginTop: 8, color: isAccessibleMode ? '#000' : '#065f46'}}>
                    New risk score: {updateResult.after.risk.toFixed(1)}
                  </Text>
                )}
              </View>
            )}
          </>
        ) : (
          <View style={currentStyles.noSegmentBox}>
            <Text style={currentStyles.noSegmentText}>Segment safety details unavailable.</Text>
          </View>
        )}

        <EmergencyPanel journeyId={journey?.journey_id} />
        
        {journey?.journey_id && (
          <DeadManSwitchPanel journeyId={journey.journey_id} />
        )}
      </>
    );
  };

  return (
    <View style={[currentStyles.container, { backgroundColor: colors.background }]}>
      <ScrollView style={{flex: 1}} contentContainerStyle={[currentStyles.content, { paddingHorizontal: spacing.screenHorizontal }]}>
        <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.md}}>
          <SakhiText variant="h1" color="primary">SAKHI</SakhiText>
          <SakhiButton 
            title={isAccessibleMode ? 'ACCESSIBILITY: ON' : 'ACCESSIBILITY: OFF'}
            variant={isAccessibleMode ? 'primary' : 'outline'}
            onPress={toggleAccessibleMode}
            style={{ paddingVertical: spacing.sm, paddingHorizontal: spacing.md }}
          />
        </View>

        {!journey ? renderHome() : renderDashboard()}
      </ScrollView>

      {journey && (
        <TouchableOpacity 
          style={currentStyles.fab} 
          onPress={() => setShowQuickFindModal(true)}
        >
          <Text style={currentStyles.fabIcon}>🔍</Text>
        </TouchableOpacity>
      )}

      {selectedSegment && (
        <ReportIncidentModal
          visible={showReportModal}
          onClose={() => setShowReportModal(false)}
          segmentId={selectedSegment.segment_id}
          latitude={selectedSegment.start_location.latitude}
          longitude={selectedSegment.start_location.longitude}
        />
      )}

      <QuickFindModal 
        visible={showQuickFindModal} 
        onClose={() => setShowQuickFindModal(false)} 
      />

      <WashroomFacilityCard
        visible={!!selectedWashroom}
        onClose={() => setSelectedWashroom(null)}
        washroom={selectedWashroom}
        distance={selectedWashroom && userLocation ? calculateDistance(userLocation.coords.latitude, userLocation.coords.longitude, selectedWashroom.latitude, selectedWashroom.longitude) : 0}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  content: {
    padding: 16,
    paddingTop: 50,
    paddingBottom: 40,
  },
  mapContainer: {
    height: 300,
  },
  googleMapsButton: {
    backgroundColor: '#1a73e8',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 2,
  },
  googleMapsButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  googleMapsHint: {
    color: '#6b7280',
    fontSize: 12,
    lineHeight: 17,
    marginTop: 6,
    marginBottom: 10,
    textAlign: 'center',
  },
  amenityToggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f3ff',
    borderWidth: 1,
    borderColor: '#c4b5fd',
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
  },
  amenityToggleTitle: {
    color: '#5b21b6',
    fontWeight: 'bold',
    fontSize: 15,
  },
  amenityToggleCaption: {
    color: '#6b7280',
    fontSize: 12,
    marginTop: 2,
  },
  amenityToggle: {
    backgroundColor: '#fff',
    borderColor: '#7c3aed',
    borderWidth: 1,
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  amenityToggleActive: {
    backgroundColor: '#7c3aed',
  },
  amenityToggleText: {
    color: '#6d28d9',
    fontSize: 11,
    fontWeight: 'bold',
  },
  amenityToggleTextActive: {
    color: '#fff',
  },
  errorBox: {
    backgroundColor: '#fee2e2',
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
  },
  errorText: {
    color: '#b91c1c',
  },
  updateResultBox: {
    backgroundColor: '#ecfdf5',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#10b981',
    marginVertical: 10,
  },
  updateResultTitle: {
    fontWeight: 'bold',
    fontSize: 16,
    color: '#065f46',
    marginBottom: 4,
  },
  updateReason: {
    color: '#047857',
    fontSize: 14,
    marginBottom: 12,
  },
  beforeAfterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  beforeBox: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 8,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  afterBox: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 8,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#34d399',
  },
  arrow: {
    fontSize: 20,
    color: '#9ca3af',
    marginHorizontal: 12,
  },
  baLabel: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#6b7280',
    marginBottom: 2,
  },
  baValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#111827',
  },
  noSegmentBox: {
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    marginVertical: 10,
    alignItems: 'center',
  },
  noSegmentText: {
    color: '#6b7280',
    fontStyle: 'italic',
  },
  offlineBanner: {
    backgroundColor: '#374151',
    padding: 12,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
  },
  offlineBannerText: {
    color: '#f9fafb',
    fontWeight: 'bold',
    fontSize: 12,
  },
  fab: {
    position: 'absolute',
    bottom: 30,
    right: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
    elevation: 8,
  },
  fabIcon: {
    fontSize: 24,
    color: '#fff',
  }
});

const accessibleStyles = StyleSheet.create({
  ...styles,
  fab: {
    position: 'absolute',
    bottom: 30,
    right: 20,
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#000',
    borderWidth: 3,
    borderColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 10,
  },
  fabIcon: {
    fontSize: 30,
    color: '#fff',
  },
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    padding: 16,
    paddingTop: 50,
    paddingBottom: 40,
  },
  errorBox: {
    backgroundColor: '#000',
    padding: 16,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: '#ff0000',
  },
  errorText: {
    color: '#ff0000',
    fontSize: 18,
    fontWeight: 'bold',
  },
  updateResultBox: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    borderWidth: 3,
    borderColor: '#000',
    marginVertical: 10,
  },
  updateResultTitle: {
    fontWeight: 'bold',
    fontSize: 20,
    color: '#000',
    marginBottom: 4,
  },
  updateReason: {
    color: '#000',
    fontSize: 18,
    marginBottom: 12,
  },
  baLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 2,
  },
  baValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
  },
  offlineBanner: {
    backgroundColor: '#000',
    padding: 16,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#fff',
  },
  offlineBannerText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  amenityToggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderWidth: 3,
    borderColor: '#000',
    borderRadius: 8,
    padding: 14,
    marginBottom: 10,
  },
  amenityToggleTitle: {
    color: '#000',
    fontWeight: 'bold',
    fontSize: 18,
  },
  amenityToggleCaption: {
    color: '#000',
    fontSize: 15,
    marginTop: 2,
  },
  amenityToggle: {
    backgroundColor: '#fff',
    borderColor: '#000',
    borderWidth: 2,
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  amenityToggleActive: {
    backgroundColor: '#000',
  },
  amenityToggleText: {
    color: '#000',
    fontSize: 13,
    fontWeight: 'bold',
  },
  amenityToggleTextActive: {
    color: '#fff',
  },
  googleMapsButton: {
    backgroundColor: '#000',
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#000',
    marginTop: 2,
  },
  googleMapsButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  googleMapsHint: {
    color: '#000',
    fontSize: 15,
    lineHeight: 20,
    marginTop: 6,
    marginBottom: 10,
    textAlign: 'center',
  },
});



