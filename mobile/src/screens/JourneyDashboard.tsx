import React, { useState } from 'react';
import { ScrollView, StyleSheet, View, Text } from 'react-native';
import JourneyForm from '../components/JourneyForm';
import JourneyMap from '../components/JourneyMap';
import RouteOptionsList from '../components/RouteOptionsList';
import SegmentSafetyPanel from '../components/SegmentSafetyPanel';
import ContextUpdatePanel from '../components/ContextUpdatePanel';
import EmergencyPanel from '../components/EmergencyPanel';
import { sakhiApi } from '../api/sakhiApi';
import { JourneyResponse, Location, RouteOption, JourneySegment, ContextUpdateResponse } from '../types/api';

export default function JourneyDashboard() {
  const [loading, setLoading] = useState(false);
  const [journey, setJourney] = useState<JourneyResponse | null>(null);
  const [selectedRoute, setSelectedRoute] = useState<RouteOption | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<JourneySegment | null>(null);
  
  const [updateResult, setUpdateResult] = useState<ContextUpdateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (origin: Location, destination: Location) => {
    setLoading(true);
    setError(null);
    setUpdateResult(null);
    try {
      const response = await sakhiApi.createJourney(origin, destination);
      setJourney(response);
      
      // Default to safest route if ranking available
      if (response.ranking && response.ranking.safest_route) {
        setSelectedRoute(response.ranking.safest_route);
      } else {
        // Fallback for missing ranking
        const mockOption: RouteOption = {
          route_id: 'primary', mode: 'safest', rank: 1, 
          distance_m: response.distance_m, duration_s: response.duration_s,
          risk_score: 0, confidence: 0, max_segment_risk: 0, uncertainty_penalty: 0,
          route_cost: 0, segments: response.segments
        };
        setSelectedRoute(mockOption);
      }
      setSelectedSegment(null);
    } catch (err: any) {
      setError(err.message || 'Error creating journey');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateComplete = (response: ContextUpdateResponse) => {
    setUpdateResult(response);
    
    // We should refetch the journey to get the new routes, or simulate it.
    // For prototype simplicity, we inform the user in the UI.
    if (response.rerouted) {
      // In a real app, we'd fetch the updated journey object here to refresh the route geometry on the map.
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <JourneyForm onAnalyze={handleAnalyze} loading={loading} />
      
      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {journey && (
        <>
          <View style={styles.mapContainer}>
            <JourneyMap 
              origin={journey.origin}
              destination={journey.destination}
              segments={selectedRoute?.segments || journey.segments}
              selectedSegmentId={selectedSegment?.segment_id || null}
              onSegmentPress={setSelectedSegment}
            />
          </View>

          {journey.ranking && (
            <RouteOptionsList 
              ranking={journey.ranking}
              selectedRouteId={selectedRoute?.route_id || null}
              onSelectRoute={(route) => {
                setSelectedRoute(route);
                setSelectedSegment(null);
              }}
            />
          )}

          {selectedSegment && (
            <>
              <SegmentSafetyPanel segment={selectedSegment} />
              
              <ContextUpdatePanel 
                journeyId={journey.journey_id} 
                segmentId={selectedSegment.segment_id} 
                onUpdateComplete={handleUpdateComplete} 
              />
            </>
          )}

          {updateResult && (
            <View style={styles.updateResultBox}>
              <Text style={styles.updateResultTitle}>
                {updateResult.rerouted ? '✓ Route recommendation updated' : '✓ Current route remains preferred'}
              </Text>
              <Text style={styles.updateReason}>{updateResult.reason}</Text>
              
              <View style={styles.beforeAfterRow}>
                <View style={styles.beforeBox}>
                  <Text style={styles.baLabel}>BEFORE</Text>
                  <Text style={styles.baValue}>Risk: {updateResult.before.risk.toFixed(1)}</Text>
                </View>
                <Text style={styles.arrow}>→</Text>
                <View style={styles.afterBox}>
                  <Text style={styles.baLabel}>AFTER</Text>
                  <Text style={styles.baValue}>Risk: {updateResult.after.risk.toFixed(1)}</Text>
                </View>
              </View>
            </View>
          )}
        </>
      )}

      <EmergencyPanel />
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
  }
});
