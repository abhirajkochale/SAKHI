import React, { useState } from 'react';
import { ScrollView, StyleSheet, View, Text, TouchableOpacity } from 'react-native';
import JourneyForm from '../components/JourneyForm';
import JourneyMap from '../components/JourneyMap';
import RouteOptionsList from '../components/RouteOptionsList';
import SegmentSafetyPanel from '../components/SegmentSafetyPanel';
import ContextUpdatePanel from '../components/ContextUpdatePanel';
import EmergencyPanel from '../components/EmergencyPanel';
import DeadManSwitchPanel from '../components/DeadManSwitchPanel';
import { sakhiApi } from '../api/sakhiApi';
import { cacheJourney, getCachedJourney } from '../api/cache';
import { useAccessibility } from '../contexts/AccessibilityContext';
import { JourneyResponse, Location, RouteOption, JourneySegment, ContextUpdateResponse, Amenity } from '../types/api';
import { Accelerometer } from 'expo-sensors';
import AmenityCard from '../components/AmenityCard';

const SHAKE_THRESHOLD = 1.8; // g-force threshold for a shake (lowered for easier testing)
const SHAKE_COOLDOWN_MS = 5000; // 5 seconds cooldown between SOS triggers

export default function JourneyDashboard() {
  const { isAccessibleMode, toggleAccessibleMode } = useAccessibility();
  const [loading, setLoading] = useState(false);
  const [journey, setJourney] = useState<JourneyResponse | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<RouteOption | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<JourneySegment | null>(null);
  
  const [updateResult, setUpdateResult] = useState<ContextUpdateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [isShakeEnabled, setIsShakeEnabled] = useState(true);
  const lastShakeTime = React.useRef(0);

  const [showWashrooms, setShowWashrooms] = useState(false);
  const [washrooms, setWashrooms] = useState<Amenity[]>([]);
  const [selectedAmenity, setSelectedAmenity] = useState<Amenity | null>(null);

  const fetchWashrooms = async () => {
    try {
      if (selectedRoute && selectedRoute.segments && selectedRoute.segments.length > 0) {
        const coords: Location[] = [];
        selectedRoute.segments.forEach(seg => {
          if (seg.geometry && seg.geometry.coordinates) {
            seg.geometry.coordinates.forEach(c => {
              coords.push({ longitude: c[0], latitude: c[1] });
            });
          } else {
            coords.push(seg.start_location);
          }
        });
        const lastSeg = selectedRoute.segments[selectedRoute.segments.length - 1];
        coords.push(lastSeg.end_location);

        const results = await sakhiApi.getAmenitiesAlongRoute(coords, 200, 'TOILET');
        setWashrooms(results);
      } else if (journey?.origin) {
        const results = await sakhiApi.getNearbyAmenities(journey.origin.latitude, journey.origin.longitude, 1500, 'TOILET');
        setWashrooms(results);
      } else {
        const results = await sakhiApi.getNearbyAmenities(28.6139, 77.2090, 2000, 'TOILET');
        setWashrooms(results);
      }
    } catch (err) {
      console.error("Error fetching washrooms:", err);
    }
  };

  React.useEffect(() => {
    if (showWashrooms) {
      fetchWashrooms();
    } else {
      setWashrooms([]);
      setSelectedAmenity(null);
    }
  }, [showWashrooms, selectedRoute, journey?.origin]);

  React.useEffect(() => {
    let subscription: any;
    if (isShakeEnabled) {
      Accelerometer.setUpdateInterval(400); // 400ms interval is enough for a shake detection without draining battery
      subscription = Accelerometer.addListener(accelerometerData => {
        const { x, y, z } = accelerometerData;
        const acceleration = Math.sqrt(x * x + y * y + z * z);
        
        if (acceleration > SHAKE_THRESHOLD) {
          const now = Date.now();
          if (now - lastShakeTime.current > SHAKE_COOLDOWN_MS) {
            lastShakeTime.current = now;
            console.log("Shake detected! Triggering SOS...");
            // Trigger SOS API
            const loc = { latitude: 28.6139, longitude: 77.2090 }; // Mock location
            sakhiApi.triggerSos(journey?.journey_id || null, loc)
              .then(res => console.log('Shake SOS Sent:', res.sos_id))
              .catch(err => console.error('Shake SOS Failed:', err));
          }
        }
      });
    }

    return () => {
      if (subscription) {
        subscription.remove();
      }
    };
  }, [isShakeEnabled, journey?.journey_id]);

  const handleAnalyze = async (origin: Location, destination: Location) => {
    setLoading(true);
    setError(null);
    setUpdateResult(null);
    setIsOffline(false);
    try {
      const response = await sakhiApi.createJourney(origin, destination);
      setJourney(response);
      
      // Cache the journey for offline use
      cacheJourney(response);
      
      // Default to safest route if ranking available
      let initialRoute = null;
      if (response.ranking && response.ranking.safest_route) {
        initialRoute = response.ranking.safest_route;
      } else {
        // Fallback for missing ranking
        const mockOption: RouteOption = {
          route_id: 'primary', mode: 'safest', rank: 1, 
          distance_m: response.distance_m, duration_s: response.duration_s,
          risk_score: 0, confidence: 0, max_segment_risk: 0, uncertainty_penalty: 0,
          route_cost: 0, segments: response.segments
        };
        initialRoute = mockOption;
      }
      setSelectedRoute(initialRoute);
      setSelectedSegment(initialRoute.segments && initialRoute.segments.length > 0 ? initialRoute.segments[0] : null);
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
        setError(err.message || 'Error creating journey and no cached data available.');
      }
    } finally {
      setLoading(false);
    }
  };

  const currentStyles = isAccessibleMode ? accessibleStyles : styles;

  return (
    <ScrollView style={currentStyles.container} contentContainerStyle={currentStyles.content}>
      <View style={{flexDirection: 'row', justifyContent: 'flex-end', marginBottom: 10}}>
        <TouchableOpacity 
          onPress={toggleAccessibleMode}
          style={{backgroundColor: isAccessibleMode ? '#1e3a8a' : '#d1d5db', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: isAccessibleMode ? 2 : 0, borderColor: '#fff'}}
        >
          <Text style={{color: isAccessibleMode ? '#fff' : '#374151', fontWeight: 'bold', fontSize: isAccessibleMode ? 16 : 12}}>
            {isAccessibleMode ? 'ACCESSIBILITY: ON' : 'ACCESSIBILITY: OFF'}
          </Text>
        </TouchableOpacity>
      </View>

      <JourneyForm onAnalyze={handleAnalyze} loading={loading} />
      
      {error && (
        <View style={currentStyles.errorBox}>
          <Text style={currentStyles.errorText}>{error}</Text>
        </View>
      )}

      {isOffline && (
        <View style={currentStyles.offlineBanner}>
          <Text style={currentStyles.offlineBannerText}>⚠️ OFFLINE MODE: Using cached route data. Live context updates unavailable.</Text>
        </View>
      )}

      {journey && (
        <>
          {Math.abs(journey.origin.latitude - 28.6433) < 0.0001 && Math.abs(journey.origin.longitude - 77.2132) < 0.0001 && (
            <View style={currentStyles.demoWarningBox}>
              <Text style={currentStyles.demoWarningTitle}>⚠️ SIMULATED DEMO EVENT / SYNTHETIC SCENARIO</Text>
              <Text style={currentStyles.demoWarningText}>
                The following risk data uses synthetic contextual signals for demonstration purposes. 
                It does not reflect actual real-world crime data or predict crime in this area.
              </Text>
            </View>
          )}

          <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 8}}>
            <Text style={{fontWeight: 'bold', fontSize: 16, color: '#374151'}}>Map Layers</Text>
            <TouchableOpacity 
              onPress={() => setShowWashrooms(!showWashrooms)}
              style={{
                backgroundColor: showWashrooms ? '#0284c7' : '#e5e7eb', 
                paddingHorizontal: 12, 
                paddingVertical: 6, 
                borderRadius: 16,
                flexDirection: 'row',
                alignItems: 'center',
              }}
            >
              <Text style={{marginRight: 4}}>{showWashrooms ? '🚽' : '🚾'}</Text>
              <Text style={{color: showWashrooms ? '#fff' : '#374151', fontWeight: 'bold', fontSize: 12}}>
                {showWashrooms ? 'WASHROOMS ON' : 'SHOW WASHROOMS'}
              </Text>
            </TouchableOpacity>
          </View>

          {selectedAmenity && (
            <AmenityCard 
              amenity={selectedAmenity}
              onClose={() => setSelectedAmenity(null)}
              onNavigate={(amn) => {
                if (journey) {
                  const newDestination = { latitude: amn.lat, longitude: amn.lon };
                  setSelectedAmenity(null);
                  handleAnalyze(journey.origin, newDestination);
                }
              }}
            />
          )}

          <View style={currentStyles.mapContainer}>
            <JourneyMap 
              origin={journey.origin}
              destination={journey.destination}
              segments={selectedRoute?.segments || journey.segments}
              selectedSegmentId={selectedSegment?.segment_id || null}
              onSegmentPress={setSelectedSegment}
              showWashrooms={showWashrooms}
              washrooms={washrooms}
              onAmenityPress={setSelectedAmenity}
            />
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
              <SegmentSafetyPanel segment={selectedSegment} />
              
              <ContextUpdatePanel 
                segmentId={selectedSegment.segment_id}
                journeyId={journey.journey_id}
                onUpdateResult={(result) => {
                  setUpdateResult(result);
                  // Refresh journey data to show new routes
                  // Since the backend re-ranks everything, we would typically refetch or the backend returns the full new journey.
                  // For the prototype, we assume the backend returns the updated journey data in the result or we just trigger re-analyze.
                  // For now, just show the update UI
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
        </>
      )}

      <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 10, paddingHorizontal: 4}}>
        <Text style={{color: isAccessibleMode ? '#000' : '#4b5563', fontWeight: 'bold', fontSize: isAccessibleMode ? 18 : 14}}>Shake to SOS Feature</Text>
        <TouchableOpacity 
          onPress={() => setIsShakeEnabled(!isShakeEnabled)}
          style={{backgroundColor: isShakeEnabled ? '#10b981' : '#d1d5db', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, borderWidth: isAccessibleMode ? 2 : 0, borderColor: '#000'}}
        >
          <Text style={{color: '#fff', fontWeight: 'bold', fontSize: isAccessibleMode ? 16 : 12}}>{isShakeEnabled ? 'ENABLED' : 'DISABLED'}</Text>
        </TouchableOpacity>
      </View>

      <EmergencyPanel journeyId={journey?.journey_id} />
      
      {journey?.journey_id && (
        <DeadManSwitchPanel journeyId={journey.journey_id} />
      )}
    </ScrollView>
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
  demoWarningBox: {
    backgroundColor: '#fffbeb',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#f59e0b',
    marginBottom: 10,
  },
  demoWarningTitle: {
    fontWeight: 'bold',
    color: '#b45309',
    marginBottom: 4,
    fontSize: 14,
  },
  demoWarningText: {
    color: '#92400e',
    fontSize: 12,
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
  }
});

const accessibleStyles = StyleSheet.create({
  ...styles,
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
  demoWarningBox: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    borderWidth: 3,
    borderColor: '#000',
    marginBottom: 10,
  },
  demoWarningTitle: {
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 4,
    fontSize: 18,
  },
  demoWarningText: {
    color: '#000',
    fontSize: 16,
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
  }
});

