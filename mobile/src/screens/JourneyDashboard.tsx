import React, { useState, useEffect } from 'react';
import { Alert, Linking, ScrollView, StyleSheet, View, Text, TouchableOpacity, Switch } from 'react-native';
import * as Location from 'expo-location';
import { NavigationContainer, createNavigationContainerRef } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import JourneyForm from '../components/JourneyForm';
import JourneyMap from '../components/JourneyMap';
import RouteOptionsList from '../components/RouteOptionsList';
import SegmentSafetyPanel from '../components/SegmentSafetyPanel';
import ReportIncidentModal from '../components/ReportIncidentModal';
import ProfileModal from '../components/ProfileModal';
import DelhiSkylineBackground from '../components/DelhiSkylineBackground';
import { supabase } from '../api/supabase';
import QuickFindModal from '../components/QuickFindModal';
import WashroomFacilityCard from '../components/WashroomFacilityCard';
import { sakhiApi } from '../api/sakhiApi';
import { useAccessibility } from '../contexts/AccessibilityContext';
import { JourneyResponse, RouteOption, JourneySegment, ContextUpdateResponse, WashroomResponse, Location as ApiLocation } from '../types/api';
import { calculateDistance } from '../utils/distance';
import { useTheme } from '../theme';
import { SakhiText } from '../components/ui/SakhiText';
import { SakhiButton } from '../components/ui/SakhiButton';
import { SakhiCard } from '../components/ui/SakhiCard';

const Tab = createBottomTabNavigator();
const navigationRef = createNavigationContainerRef();

export default function JourneyDashboard() {
  const { colors, spacing } = useTheme();
  const { isAccessibleMode, toggleAccessibleMode } = useAccessibility();
  const [loading, setLoading] = useState(false);
  const [journey, setJourney] = useState<JourneyResponse | null>(null);
  const [isActiveJourney, setIsActiveJourney] = useState(false);
  const [showSafetyDetails, setShowSafetyDetails] = useState(false);
  const [routeLabels, setRouteLabels] = useState({ origin: '', destination: '' });
  const [selectedRoute, setSelectedRoute] = useState<RouteOption | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<JourneySegment | null>(null);
  
  const [showReportModal, setShowReportModal] = useState(false);
  const [showQuickFindModal, setShowQuickFindModal] = useState(false);
  const [quickFindInitialCategory, setQuickFindInitialCategory] = useState<string | null>(null);
  
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [hasUser, setHasUser] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setHasUser(!!session?.user);
    });
    supabase.auth.onAuthStateChange((_event, session) => {
      setHasUser(!!session?.user);
    });
  }, []);

  const [updateResult, setUpdateResult] = useState<ContextUpdateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const [showWashrooms, setShowWashrooms] = useState(false);
  const [washrooms, setWashrooms] = useState<WashroomResponse[]>([]);
  const [washroomsLoading, setWashroomsLoading] = useState(false);
  const [hasLoadedWashrooms, setHasLoadedWashrooms] = useState(false);
  const [washroomsError, setWashroomsError] = useState<string | null>(null);
  const [washroomsRefreshKey, setWashroomsRefreshKey] = useState(0);
  const [userLocation, setUserLocation] = useState<Location.LocationObject | null>(null);
  const [selectedWashroom, setSelectedWashroom] = useState<WashroomResponse | null>(null);

  useEffect(() => {
    let active = true;
    let locationSubscription: Location.LocationSubscription | null = null;

    const startLocationTracking = async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          console.warn('Permission to access location was denied');
          return;
        }

        const location = await Location.getCurrentPositionAsync({});
        if (!active) return;
        setUserLocation(location);

        locationSubscription = await Location.watchPositionAsync(
          { accuracy: Location.Accuracy.High, timeInterval: 5000, distanceInterval: 10 },
          (loc) => { if (active) setUserLocation(loc); }
        );
      } catch (err) {
        if (active) {
          setUserLocation({
            coords: {
              latitude: 28.6328,
              longitude: 77.2197,
              altitude: null,
              accuracy: 5,
              altitudeAccuracy: null,
              heading: null,
              speed: null,
            },
            timestamp: Date.now(),
          });
        }
      }
    };

    startLocationTracking();

    return () => {
      active = false;
      if (locationSubscription) {
        locationSubscription.remove();
      }
    };
  }, []);

  const fetchWashrooms = async (lat: number, lon: number) => {
    setWashroomsLoading(true);
    setWashroomsError(null);
    try {
      const data = await sakhiApi.getOsmAmenities(lat, lon, 'washroom', 200);
      setWashrooms(data.map(d => ({
        ...d,
        verified_count: d.rating_count || 0
      })) as any);
      setHasLoadedWashrooms(true);
    } catch (err) {
      setWashroomsError('Could not fetch nearby washrooms.');
    } finally {
      setWashroomsLoading(false);
    }
  };

  useEffect(() => {
    if (!showWashrooms) return;
    const centerLat = journey?.origin.latitude ?? userLocation?.coords.latitude;
    const centerLon = journey?.origin.longitude ?? userLocation?.coords.longitude;
    if (centerLat && centerLon) {
      fetchWashrooms(centerLat, centerLon);
    }
  }, [showWashrooms, journey?.origin.latitude, journey?.origin.longitude, userLocation?.coords.latitude, userLocation?.coords.longitude, washroomsRefreshKey]);

  const handleAnalyze = async (origin: ApiLocation, destination: ApiLocation, originName: string, destName: string) => {
    setLoading(true);
    setError(null);
    setRouteLabels({ origin: originName, destination: destName });

    try {
      const data = await sakhiApi.createJourney(origin, destination);
      setJourney(data);
      setIsActiveJourney(true);
      setShowWashrooms(false);
      
      let bestRoute: RouteOption | null = null;
      if (data.ranking) {
        bestRoute = data.ranking.safest_route || data.ranking.balanced_route || data.ranking.fastest_route;
      }
      if (!bestRoute && data.segments && data.segments.length > 0) {
        bestRoute = {
          route_id: 'default',
          mode: 'walking',
          rank: 1,
          distance_m: data.distance_m,
          duration_s: data.duration_s,
          risk_score: 25.0,
          confidence: 85.0,
          max_segment_risk: 30.0,
          uncertainty_penalty: 0,
          route_cost: 25.0,
          segments: data.segments,
        };
      }

      setSelectedRoute(bestRoute);
      setSelectedSegment(bestRoute?.segments && bestRoute.segments.length > 0 ? bestRoute.segments[0] : null);

      if (navigationRef.isReady()) {
        navigationRef.navigate('Journeys' as never);
      }
    } catch (err: any) {
      setError(sakhiApi.getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const openSelectedRouteInGoogleMaps = async () => {
    if (!journey) return;

    const routeSegments = selectedRoute?.segments || journey.segments;
    const coordinates = routeSegments.flatMap((segment) => segment.geometry.coordinates || []);
    
    const waypoints: string[] = [];
    if (coordinates.length > 5) {
      [0.25, 0.5, 0.75].forEach((fraction) => {
        const index = Math.round((coordinates.length - 1) * fraction);
        const pt = coordinates[index];
        if (Array.isArray(pt) && pt.length >= 2) {
          const wp = `${pt[1]},${pt[0]}`;
          if (!waypoints.includes(wp)) {
            waypoints.push(wp);
          }
        }
      });
    }

    const params = new URLSearchParams({
      api: '1',
      origin: `${journey.origin.latitude},${journey.origin.longitude}`,
      destination: `${journey.destination.latitude},${journey.destination.longitude}`,
      travelmode: 'walking'
    });
    
    if (waypoints.length > 0) {
      params.set('waypoints', waypoints.join('|'));
    }

    const url = `https://www.google.com/maps/dir/?${params.toString()}`;
    
    try {
      await Linking.openURL(url);
    } catch (error) {
      Alert.alert('Navigation unavailable', 'Unable to open Google Maps or a browser on this device.');
    }
  };

  const openQuickFind = (category?: string) => {
    setQuickFindInitialCategory(category || null);
    setShowQuickFindModal(true);
  };

  const renderHome = () => (
    <View style={styles.homeBackground}>
      {/* Background Skyline */}
      <DelhiSkylineBackground />

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.homeScrollContent}>
        {/* Custom Header */}
        <View style={styles.homeHeaderRow}>
          <View>
            <Text style={styles.logoTitle}>SAKHI</Text>
            <Text style={styles.logoSubtitle}>Travel safer. Together.</Text>
          </View>
          <TouchableOpacity style={styles.profileBtn} onPress={() => setShowProfileModal(true)}>
            <Ionicons name="person-outline" size={20} color="#374151" />
            {hasUser && <View style={styles.profileDot} />}
          </TouchableOpacity>
        </View>

        {/* Journey Form Card */}
        <View style={{ zIndex: 10, marginTop: 10 }}>
          <JourneyForm onAnalyze={handleAnalyze} loading={loading} />
        </View>
        
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {/* Quick Actions Grid (6 cards in 2 rows x 3 columns) */}
        <View style={styles.sectionContainer}>
          <Text style={styles.sectionTitle}>Quick actions</Text>
          
          <View style={styles.quickGrid}>
            {/* 1. Right to Pee */}
            <TouchableOpacity style={[styles.gridCard, { backgroundColor: '#F3E8FF' }]} onPress={() => openQuickFind('Washroom')}>
              <View style={styles.gridIconCircle}>
                <Ionicons name="map-outline" size={20} color="#7E22CE" />
              </View>
              <Text style={styles.gridCardTitle}>Right to Pee</Text>
              <Text style={styles.gridCardSub}>Find washrooms</Text>
            </TouchableOpacity>

            {/* 2. Call a Friend */}
            <TouchableOpacity style={[styles.gridCard, { backgroundColor: '#E0F2FE' }]} onPress={() => openQuickFind('Call a Friend')}>
              <View style={styles.gridIconCircle}>
                <Ionicons name="call-outline" size={20} color="#0284C7" />
              </View>
              <Text style={styles.gridCardTitle}>Call a Friend</Text>
              <Text style={styles.gridCardSub}>Simulated call</Text>
            </TouchableOpacity>

            {/* 3. Report Incident */}
            <TouchableOpacity style={[styles.gridCard, { backgroundColor: '#FFEDD5' }]} onPress={() => setShowReportModal(true)}>
              <View style={styles.gridIconCircle}>
                <Ionicons name="warning-outline" size={20} color="#EA580C" />
              </View>
              <Text style={styles.gridCardTitle}>Report Incident</Text>
              <Text style={styles.gridCardSub}>Share & help</Text>
            </TouchableOpacity>

            {/* 4. Police Stations */}
            <TouchableOpacity style={[styles.gridCard, { backgroundColor: '#ECFDF5' }]} onPress={() => openQuickFind('Police Station')}>
              <View style={styles.gridIconCircle}>
                <Ionicons name="shield-outline" size={20} color="#059669" />
              </View>
              <Text style={styles.gridCardTitle}>Police Stations</Text>
              <Text style={styles.gridCardSub}>Find nearby</Text>
            </TouchableOpacity>

            {/* 5. Medical Clinics */}
            <TouchableOpacity style={[styles.gridCard, { backgroundColor: '#FCE7F3' }]} onPress={() => openQuickFind('Medical Clinic')}>
              <View style={styles.gridIconCircle}>
                <Ionicons name="medical-outline" size={20} color="#DB2777" />
              </View>
              <Text style={styles.gridCardTitle}>Medical Clinics</Text>
              <Text style={styles.gridCardSub}>Find nearby</Text>
            </TouchableOpacity>

            {/* 6. Quick Find */}
            <TouchableOpacity style={[styles.gridCard, { backgroundColor: '#E0F2FE' }]} onPress={() => openQuickFind()}>
              <View style={styles.gridIconCircle}>
                <Ionicons name="location-outline" size={20} color="#0891B2" />
              </View>
              <Text style={styles.gridCardTitle}>Quick Find</Text>
              <Text style={styles.gridCardSub}>All in one search</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Helplines Section */}
        <View style={[styles.sectionContainer, { marginTop: 24, marginBottom: 32 }]}>
          <Text style={styles.sectionTitle}>Helplines</Text>
          
          <View style={styles.helplinesCard}>
            {/* Row 1: Women Helpline */}
            <View style={styles.helplineRow}>
              <View style={styles.helplineLeft}>
                <View style={[styles.helplineIconBox, { backgroundColor: '#FCE7F3' }]}>
                  <Ionicons name="call-outline" size={18} color="#DB2777" />
                </View>
                <View>
                  <Text style={styles.helplineName}>Women Helpline</Text>
                  <Text style={styles.helplineNumber}>181</Text>
                </View>
              </View>
              <TouchableOpacity style={styles.callBtn} onPress={() => Linking.openURL('tel:181')}>
                <Ionicons name="call-outline" size={14} color="#8B1E1E" style={{ marginRight: 4 }} />
                <Text style={styles.callBtnText}>Call</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.helplineDivider} />

            {/* Row 2: Police Helpline */}
            <View style={styles.helplineRow}>
              <View style={styles.helplineLeft}>
                <View style={[styles.helplineIconBox, { backgroundColor: '#E0F2FE' }]}>
                  <Ionicons name="shield-outline" size={18} color="#0284C7" />
                </View>
                <View>
                  <Text style={styles.helplineName}>Police Helpline</Text>
                  <Text style={styles.helplineNumber}>112</Text>
                </View>
              </View>
              <TouchableOpacity style={styles.callBtn} onPress={() => Linking.openURL('tel:112')}>
                <Ionicons name="call-outline" size={14} color="#8B1E1E" style={{ marginRight: 4 }} />
                <Text style={styles.callBtnText}>Call</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.helplineDivider} />

            {/* Row 3: Mental Health Support */}
            <View style={styles.helplineRow}>
              <View style={styles.helplineLeft}>
                <View style={[styles.helplineIconBox, { backgroundColor: '#ECFDF5' }]}>
                  <Ionicons name="medical-outline" size={18} color="#059669" />
                </View>
                <View>
                  <Text style={styles.helplineName}>Mental Health Support</Text>
                  <Text style={styles.helplineNumber}>9152987821</Text>
                </View>
              </View>
              <TouchableOpacity style={styles.callBtn} onPress={() => Linking.openURL('tel:9152987821')}>
                <Ionicons name="call-outline" size={14} color="#8B1E1E" style={{ marginRight: 4 }} />
                <Text style={styles.callBtnText}>Call</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.viewMoreRow} onPress={() => openQuickFind()}>
              <Text style={styles.viewMoreText}>View more helplines</Text>
              <Ionicons name="chevron-forward" size={14} color="#8B1E1E" />
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </View>
  );

  const renderActiveJourney = () => {
    if (!journey || !selectedRoute) return null;

    return (
      <View style={{flex: 1, paddingBottom: 20}}>
        {/* Active Journey Header */}
        <View style={styles.ajHeader}>
          <View style={{flexDirection: 'row', alignItems: 'center'}}>
            <TouchableOpacity onPress={() => setJourney(null)} style={{marginRight: 16, backgroundColor: '#FDF2F2', padding: 8, borderRadius: 20}}>
              <Ionicons name="arrow-back" size={24} color="#8B1E1E" />
            </TouchableOpacity>
            <View>
              <Text style={styles.ajTitle}>Active Journey</Text>
              <Text style={styles.ajSubtitle}>You're on your way</Text>
            </View>
          </View>
        </View>

        {/* Compact Journey Form */}
        <JourneyForm 
          onAnalyze={handleAnalyze} 
          loading={loading}
          compact={true}
          initialOriginText={routeLabels.origin || ''}
          initialDestinationText={routeLabels.destination || ''}
          initialOrigin={journey?.origin || null}
          initialDestination={journey?.destination || null}
        />

        {/* Map Container */}
        <View style={[styles.ajMapContainer, { minHeight: 300 }]}>
          <JourneyMap 
            origin={journey.origin}
            destination={journey.destination}
            segments={selectedRoute.segments || []}
            selectedSegmentId={selectedSegment?.segment_id || null}
            onSegmentPress={setSelectedSegment}
            washrooms={washrooms}
            showWashrooms={showWashrooms}
            onNavigateRequest={openSelectedRouteInGoogleMaps}
            onWashroomPress={(washroom) => setSelectedWashroom(washroom)}
          />
        </View>

        <TouchableOpacity
          style={styles.amenityToggleRow}
          onPress={() => {
            if (!showWashrooms) {
              setWashroomsError(null);
              setWashrooms([]);
              setHasLoadedWashrooms(false);
            }
            setShowWashrooms((visible) => !visible);
          }}
        >
          <View style={[styles.amenityIconCircle, showWashrooms ? { backgroundColor: '#FDF2F2' } : { backgroundColor: '#F3F4F6' }]}>
            <Ionicons name="water" size={18} color={showWashrooms ? '#8B1E1E' : '#9CA3AF'} />
          </View>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={[styles.amenityToggleTitle, { color: showWashrooms ? '#8B1E1E' : '#1F2937' }]}>
              Nearby Washrooms
            </Text>
            <Text style={styles.amenityToggleCaption}>
              {washroomsLoading ? 'Loading...' : washroomsError || (showWashrooms && washrooms.length ? `${washrooms.length} locations visible` : 'Tap to show on map')}
            </Text>
          </View>
          <View style={[styles.customSwitchBg, showWashrooms ? {backgroundColor: '#8B1E1E', borderColor: '#8B1E1E'} : {}]}>
            <View style={[styles.customSwitchHandle, showWashrooms ? {transform: [{translateX: 14}]} : {}]} />
          </View>
        </TouchableOpacity>

        {/* Route Options List injected into Active Journey */}
        {journey.ranking && (
          <View style={{ marginBottom: 16 }}>
            <Text style={[styles.ajSectionTitle, {marginTop: 8}]}>Choose a different route</Text>
            <RouteOptionsList 
              ranking={journey.ranking}
              selectedRouteId={selectedRoute?.route_id || null}
              onSelectRoute={(route) => {
                setSelectedRoute(route);
                setSelectedSegment(route.segments && route.segments.length > 0 ? route.segments[0] : null);
              }}
              onOpenMaps={openSelectedRouteInGoogleMaps}
            />
          </View>
        )}

        {/* Quick Actions */}
        <Text style={styles.ajSectionTitle}>Quick Actions</Text>
        <View style={styles.ajQuickActionsRow}>
          <TouchableOpacity style={styles.ajQaTile} onPress={() => openQuickFind('Washroom')}>
            <Ionicons name="map-outline" size={20} color="#7E22CE" />
            <Text style={styles.ajQaText}>Washroom</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.ajQaTile} onPress={() => openQuickFind('Medical Clinic')}>
            <Ionicons name="medical-outline" size={20} color="#DB2777" />
            <Text style={styles.ajQaText}>Medical</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.ajQaTile} onPress={() => openQuickFind('Police Station')}>
            <Ionicons name="shield-outline" size={20} color="#059669" />
            <Text style={styles.ajQaText}>Police</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.ajQaTile} onPress={() => openQuickFind('Call a Friend')}>
            <Ionicons name="call-outline" size={20} color="#0284C7" />
            <Text style={styles.ajQaText}>Call Friend</Text>
          </TouchableOpacity>
        </View>

        {/* Action Cards */}
        <TouchableOpacity style={styles.ajActionCardRed} onPress={() => setShowReportModal(true)}>
          <Ionicons name="warning-outline" size={22} color="#8B1E1E" style={{ marginRight: 12 }} />
          <View style={styles.ajActionTextCont}>
            <Text style={styles.ajActionTitleRed}>Report an incident</Text>
            <Text style={styles.ajActionDescRed}>Help us make journeys safer for everyone.</Text>
          </View>
          <Ionicons name="chevron-forward" size={18} color="#8B1E1E" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.ajActionCardWhite} onPress={() => setShowSafetyDetails(!showSafetyDetails)}>
          <Ionicons name="shield-checkmark-outline" size={22} color="#4B5563" style={{ marginRight: 12 }} />
          <View style={styles.ajActionTextCont}>
            <Text style={styles.ajActionTitleDark}>View safety details</Text>
            <Text style={styles.ajActionDescGray}>See risk factors and recommendations</Text>
          </View>
          <Ionicons name={showSafetyDetails ? "chevron-down" : "chevron-forward"} size={18} color="#6B7280" />
        </TouchableOpacity>

        {showSafetyDetails && selectedSegment && (
          <View style={{ marginTop: 8, marginBottom: 16 }}>
            <SegmentSafetyPanel 
              segment={selectedSegment} 
              onReportIncident={() => setShowReportModal(true)}
            />
          </View>
        )}
      </View>
    );
  };

  return (
    <NavigationContainer ref={navigationRef}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarIcon: ({ focused, color, size }) => {
            let iconName = 'home-outline';
            if (route.name === 'Home') iconName = focused ? 'home' : 'home-outline';
            else if (route.name === 'Journeys') iconName = focused ? 'map' : 'map-outline';
            else if (route.name === 'Amenities') iconName = focused ? 'business' : 'business-outline';
            else if (route.name === 'Profile') iconName = focused ? 'person' : 'person-outline';

            if (route.name === 'Home' && focused) {
              return (
                <View style={styles.activeTabPill}>
                  <Ionicons name="home" size={18} color="#8B1E1E" />
                  <Text style={styles.activeTabText}>Home</Text>
                </View>
              );
            }

            return <Ionicons name={iconName as any} size={size} color={color} />;
          },
          tabBarLabel: ({ focused, color }) => {
            if (focused && route.name === 'Home') return null; // Pill shows label inside
            return <Text style={{ fontSize: 11, color, fontWeight: focused ? '600' : '400', marginTop: -2 }}>{route.name}</Text>;
          },
          tabBarActiveTintColor: '#8B1E1E',
          tabBarInactiveTintColor: '#6B7280',
          tabBarStyle: {
            backgroundColor: '#ffffff',
            borderTopWidth: 1,
            borderColor: '#F3F4F6',
            height: 65,
            paddingBottom: 8,
            paddingTop: 6,
          }
        })}
      >
        <Tab.Screen name="Home">
          {() => renderHome()}
        </Tab.Screen>
        <Tab.Screen name="Journeys">
          {() => (
            <View style={styles.homeBackground}>
              <DelhiSkylineBackground />
              {journey && isActiveJourney ? (
                <ScrollView 
                  style={{flex: 1}} 
                  contentContainerStyle={[styles.content, { paddingHorizontal: spacing.screenHorizontal }]}
                  keyboardShouldPersistTaps="handled"
                >
                  {renderActiveJourney()}
                </ScrollView>
              ) : journey ? (
                <View style={{flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24}}>
                  <View style={{ width: 80, height: 80, borderRadius: 40, backgroundColor: '#FDF2F2', justifyContent: 'center', alignItems: 'center', marginBottom: 24 }}>
                    <Ionicons name="navigate" size={36} color="#8B1E1E" />
                  </View>
                  <SakhiText variant="h2" style={{marginBottom: 12}}>Active Journey</SakhiText>
                  <SakhiText variant="body" color="secondary" style={{textAlign: 'center', marginBottom: 32, maxWidth: 280, lineHeight: 22}}>
                    You currently have an ongoing journey in progress.
                  </SakhiText>
                  <View style={{ width: '100%', maxWidth: 320 }}>
                    <SakhiButton title="Continue journey" onPress={() => setIsActiveJourney(true)} />
                    <SakhiButton title="End journey" variant="secondary" style={{marginTop: 16}} onPress={() => { setJourney(null); setIsActiveJourney(false); }} />
                  </View>
                </View>
              ) : (
                <View style={{flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24}}>
                  <View style={{ width: 80, height: 80, borderRadius: 40, backgroundColor: '#FDF2F2', justifyContent: 'center', alignItems: 'center', marginBottom: 24 }}>
                    <Ionicons name="map-outline" size={36} color="#8B1E1E" />
                  </View>
                  <SakhiText variant="h2" style={{marginBottom: 12}}>Journey History</SakhiText>
                  <SakhiText variant="body" color="secondary" style={{textAlign: 'center', maxWidth: 280, marginBottom: 8}}>
                    No journeys yet.
                  </SakhiText>
                  <SakhiText variant="body" color="secondary" style={{textAlign: 'center', maxWidth: 280, lineHeight: 22}}>
                    Your analyzed and completed journeys will appear here when available.
                  </SakhiText>
                </View>
              )}
            </View>
          )}
        </Tab.Screen>
        <Tab.Screen name="Amenities">
          {() => {
            const amenityCardStyle = { width: '48%' as const, backgroundColor: '#FFFFFF', padding: 20, borderRadius: 24, shadowColor: '#000', shadowOffset: {width: 0, height: 4}, shadowOpacity: 0.03, shadowRadius: 12, elevation: 2, borderWidth: 1, borderColor: '#F3F4F6', alignItems: 'flex-start' as const, marginBottom: 16 };
            const iconBgStyle = { width: 48, height: 48, borderRadius: 24, justifyContent: 'center' as const, alignItems: 'center' as const, marginBottom: 16 };
            return (
              <View style={styles.homeBackground}>
                <DelhiSkylineBackground />
                <View style={{flex: 1, padding: 24, paddingTop: 60}}>
                  <View style={{marginBottom: 32}}>
                    <SakhiText variant="h1" style={{marginBottom: 8, color: '#8B1E1E'}}>Amenities</SakhiText>
                    <SakhiText variant="body" color="secondary" style={{lineHeight: 22}}>
                      Find help and essential facilities quickly along your route or nearby.
                    </SakhiText>
                  </View>
                  
                  <View style={{flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between'}}>
                    <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind('Washroom')}>
                      <View style={[iconBgStyle, {backgroundColor: '#F3E8FF'}]}>
                        <Ionicons name="water" size={24} color="#7E22CE" />
                      </View>
                      <SakhiText variant="body" style={{fontWeight: '700', fontSize: 16}}>Washrooms</SakhiText>
                      <SakhiText variant="caption" color="secondary" style={{marginTop: 4}}>Find nearby toilets</SakhiText>
                    </TouchableOpacity>

                    <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind('Medical Clinic')}>
                      <View style={[iconBgStyle, {backgroundColor: '#FCE7F3'}]}>
                        <Ionicons name="add" size={32} color="#DB2777" />
                      </View>
                      <SakhiText variant="body" style={{fontWeight: '700', fontSize: 16}}>Medical</SakhiText>
                      <SakhiText variant="caption" color="secondary" style={{marginTop: 4}}>Clinics & Hospitals</SakhiText>
                    </TouchableOpacity>

                    <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind('Police Station')}>
                      <View style={[iconBgStyle, {backgroundColor: '#ECFDF5'}]}>
                        <Ionicons name="shield-checkmark" size={24} color="#059669" />
                      </View>
                      <SakhiText variant="body" style={{fontWeight: '700', fontSize: 16}}>Police</SakhiText>
                      <SakhiText variant="caption" color="secondary" style={{marginTop: 4}}>Nearest stations</SakhiText>
                    </TouchableOpacity>

                    <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind()}>
                      <View style={[iconBgStyle, {backgroundColor: '#E0F2FE'}]}>
                        <Ionicons name="search" size={24} color="#0284C7" />
                      </View>
                      <SakhiText variant="body" style={{fontWeight: '700', fontSize: 16}}>Quick Find</SakhiText>
                      <SakhiText variant="caption" color="secondary" style={{marginTop: 4}}>Search all types</SakhiText>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            );
          }}
        </Tab.Screen>
        <Tab.Screen name="Profile">
          {() => {
            return (
              <View style={{flex: 1, padding: 24, paddingTop: 60, backgroundColor: '#FDFCFD'}}>
                <View style={{marginBottom: 32}}>
                  <SakhiText variant="h1" style={{marginBottom: 8}}>Profile</SakhiText>
                  <SakhiText variant="body" color="secondary" style={{lineHeight: 22}}>
                    Manage your app preferences and settings.
                  </SakhiText>
                </View>
                
                <SakhiText variant="h3" style={{marginBottom: 12}}>Accessibility</SakhiText>
                <SakhiCard>
                  <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
                    <View style={{flexDirection: 'row', alignItems: 'center'}}>
                      <View style={{width: 36, height: 36, borderRadius: 18, backgroundColor: '#F3F4F6', justifyContent: 'center', alignItems: 'center', marginRight: 12}}>
                        <Ionicons name="eye-outline" size={18} color="#4B5563" />
                      </View>
                      <SakhiText variant="body" style={{fontWeight: '500'}}>Accessibility Mode</SakhiText>
                    </View>
                    <Switch 
                      value={isAccessibleMode} 
                      onValueChange={toggleAccessibleMode} 
                      trackColor={{ true: '#8B1E1E', false: '#D1D5DB' }} 
                      thumbColor="#FFF"
                    />
                  </View>
                </SakhiCard>

                <SakhiText variant="h3" style={{marginBottom: 12, marginTop: 32}}>About</SakhiText>
                <SakhiCard>
                  <View style={{flexDirection: 'row', alignItems: 'center'}}>
                    <View style={{width: 36, height: 36, borderRadius: 18, backgroundColor: '#F3F4F6', justifyContent: 'center', alignItems: 'center', marginRight: 12}}>
                      <Ionicons name="information-circle-outline" size={18} color="#4B5563" />
                    </View>
                    <View>
                      <SakhiText variant="body" style={{fontWeight: '500'}}>SAKHI</SakhiText>
                      <SakhiText variant="caption" color="secondary">Version 1.0.0 — Contextual Safety Intelligence</SakhiText>
                    </View>
                  </View>
                </SakhiCard>
              </View>
            );
          }}
        </Tab.Screen>
      </Tab.Navigator>

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
        onClose={() => {
          setShowQuickFindModal(false);
          setQuickFindInitialCategory(null);
        }} 
        initialCategory={quickFindInitialCategory}
      />
      
      <ProfileModal
        visible={showProfileModal}
        onClose={() => setShowProfileModal(false)}
      />

      <WashroomFacilityCard
        visible={!!selectedWashroom}
        onClose={() => setSelectedWashroom(null)}
        washroom={selectedWashroom}
        distance={selectedWashroom && userLocation ? calculateDistance(userLocation.coords.latitude, userLocation.coords.longitude, selectedWashroom.latitude, selectedWashroom.longitude) : 0}
        onFeedbackSubmitted={() => setWashroomsRefreshKey(k => k + 1)}
      />
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FDFCFD',
  },
  content: {
    padding: 16,
    paddingTop: 50,
    paddingBottom: 40,
  },
  homeBackground: {
    flex: 1,
    backgroundColor: '#FDF7F6',
  },
  homeScrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 40,
  },
  homeHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  logoTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#8B1E1E',
    letterSpacing: 0.5,
  },
  logoSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  profileBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  profileDot: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
    borderWidth: 1,
    borderColor: '#FFF',
  },
  errorBox: {
    backgroundColor: '#FEF2F2',
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FEE2E2',
  },
  errorText: {
    color: '#991B1B',
    fontSize: 13,
  },
  sectionContainer: {
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 12,
  },
  quickGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    rowGap: 12,
  },
  gridCard: {
    width: '31%',
    borderRadius: 16,
    padding: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 110,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1,
  },
  gridIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  gridCardTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#1F2937',
    textAlign: 'center',
  },
  gridCardSub: {
    fontSize: 10,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 2,
  },
  helplinesCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#F3F4F6',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  helplineRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  helplineLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  helplineIconBox: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  helplineName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  helplineNumber: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 1,
  },
  callBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#8B1E1E',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 6,
    backgroundColor: '#FFFFFF',
  },
  callBtnText: {
    color: '#8B1E1E',
    fontWeight: '600',
    fontSize: 12,
  },
  helplineDivider: {
    height: 1,
    backgroundColor: '#F3F4F6',
    marginVertical: 4,
  },
  viewMoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 12,
    marginTop: 4,
  },
  viewMoreText: {
    color: '#8B1E1E',
    fontWeight: 'bold',
    fontSize: 13,
    marginRight: 4,
  },
  activeTabPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  activeTabText: {
    color: '#8B1E1E',
    fontWeight: 'bold',
    fontSize: 12,
    marginLeft: 6,
  },
  ajHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    marginTop: 10,
  },
  ajBackArrow: {
    fontSize: 24,
    color: '#8B1E1E',
    fontWeight: 'bold',
  },
  ajTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#8B1E1E',
  },
  ajSubtitle: {
    fontSize: 12,
    color: '#6B7280',
  },
  ajMapContainer: {
    height: 300,
    borderRadius: 16,
    backgroundColor: '#E5E7EB',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  amenityToggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#F3F4F6',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1,
  },
  amenityIconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  amenityToggleTitle: {
    fontWeight: '700',
    fontSize: 15,
  },
  amenityToggleCaption: {
    color: '#6B7280',
    fontSize: 12,
    marginTop: 2,
  },
  customSwitchBg: {
    width: 40,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  customSwitchHandle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  ajSectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 12,
  },
  ajQuickActionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    gap: 8,
  },
  ajQaTile: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  ajQaText: {
    fontSize: 10,
    color: '#1F2937',
    fontWeight: '600',
    marginTop: 4,
  },
  ajActionCardRed: {
    backgroundColor: '#FDF2F2',
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#FAD1D1',
  },
  ajActionTextCont: {
    flex: 1,
  },
  ajActionTitleRed: {
    color: '#8B1E1E',
    fontWeight: 'bold',
    fontSize: 14,
  },
  ajActionDescRed: {
    color: '#8B1E1E',
    fontSize: 10,
    marginTop: 2,
    opacity: 0.8,
  },
  ajActionCardWhite: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  ajActionTitleDark: {
    color: '#1F2937',
    fontWeight: 'bold',
    fontSize: 14,
  },
  ajActionDescGray: {
    color: '#6B7280',
    fontSize: 10,
    marginTop: 2,
  },
});
