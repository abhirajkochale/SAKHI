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
import { SakhiCard } from '../components/ui/SakhiCard';

 // 5 seconds cooldown between SOS triggers

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
  
  const [showRouteOptions, setShowRouteOptions] = useState(false);

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

  const handleAnalyze = async (origin: ApiLocation, destination: ApiLocation, originName: string, destName: string) => {
    setLoading(true);
    setError(null);
    setUpdateResult(null);
    setIsOffline(false);
    setShowSafetyDetails(false);
    setShowRouteOptions(false);
    setRouteLabels({ origin: originName, destination: destName });
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
      setIsActiveJourney(true);
      if (navigationRef.isReady()) navigationRef.navigate('Journeys' as never);
    } catch (err: any) {
      console.error(err);
      // Try offline fallback
      const cached = await getCachedJourney();
      if (cached) {
        setIsOffline(true);
        setJourney(cached);
        if (cached.ranking && cached.ranking.safest_route) {
          setSelectedRoute(cached.ranking.safest_route);
          setSelectedSegment(cached.ranking.safest_route.segments?.[0] || null);
          setIsActiveJourney(true);
        } else {
          setSelectedRoute(null);
          setSelectedSegment(null);
        }

        if (navigationRef.isReady()) {
          navigationRef.navigate('Journeys' as never);
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

  const currentStyles = styles;

  const openQuickFind = (category?: string) => {
    setQuickFindInitialCategory(category || null);
    setShowQuickFindModal(true);
  };

  const handleSOSTap = () => {
    Alert.alert(
      "Trigger SOS",
      "Are you sure you want to trigger SOS?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "SEND SOS", style: "destructive", onPress: () => {
            Alert.alert("SOS Triggered", "Emergency contacts have been notified.");
          }
        }
      ]
    );
  };

  const renderHome = () => (
    <View style={currentStyles.homeBackground}>
      {/* Background Skyline (Absolute positioned) */}
      <View style={currentStyles.skylineWrapper}>
         <View style={currentStyles.skylineDome1} />
         <View style={currentStyles.skylineDome2} />
         <View style={currentStyles.skylineDome3} />
         <View style={currentStyles.skylineDome4} />
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={currentStyles.homeScrollContent}>
      {/* Custom Home Header */}
      <View style={currentStyles.homeHeaderRow}>
        <View style={currentStyles.logoRow}>
          <View style={currentStyles.logoShield}>
            <Text style={currentStyles.logoShieldIcon}>👤</Text>
          </View>
          <View>
            <Text style={currentStyles.logoTitle}>SAKHI</Text>
            <Text style={currentStyles.logoSubtitle}>Travel Safer. Together.</Text>
          </View>
        </View>
        <TouchableOpacity style={currentStyles.profileBtn} onPress={() => {}}>
          <Text style={{fontSize: 24}}>👤</Text>
          <View style={currentStyles.profileDot} />
        </TouchableOpacity>
      </View>

      {/* Hero Typography */}
      <View style={currentStyles.heroContainer}>
        <Text style={currentStyles.heroTextDark}>Your Safety,</Text>
        <View style={{flexDirection: 'row', alignItems: 'center'}}>
          <Text style={currentStyles.heroTextRed}>Our Priority.</Text>
          <Text style={currentStyles.heroHeart}> ♡</Text>
        </View>
        <Text style={currentStyles.heroSubtitle}>Find the safest way, wherever you go.</Text>
      </View>

      {/* Journey Form Card */}
      <View style={{zIndex: 10, marginTop: 10}}>
        <JourneyForm onAnalyze={handleAnalyze} loading={loading} />
      </View>
      
      {error && (
        <View style={[currentStyles.errorBox, {marginTop: -10, marginBottom: 20}]}>
          <Text style={currentStyles.errorText}>{error}</Text>
        </View>
      )}

      {/* Quick Access Tiles */}
      <View style={currentStyles.quickAccessContainer}>
        <View style={currentStyles.quickAccessHeader}>
          <Text style={currentStyles.quickAccessLabel}>Quick Access</Text>
          <Text style={currentStyles.quickAccessSeeAll}>See all</Text>
        </View>
        
        <View style={currentStyles.quickAccessRow3}>
          <TouchableOpacity style={currentStyles.qaTileSquare} onPress={() => openQuickFind('Washroom')}>
            <View style={[currentStyles.qaIconContainer, {backgroundColor: '#DC2626'}]}>
              <Text style={currentStyles.qaTileIconWhite}>🚻</Text>
            </View>
            <Text style={currentStyles.qaTileText}>Washroom</Text>
          </TouchableOpacity>
          <TouchableOpacity style={currentStyles.qaTileSquare} onPress={() => openQuickFind('Medical Clinic')}>
            <View style={[currentStyles.qaIconContainer, {backgroundColor: '#14B8A6'}]}>
              <Text style={currentStyles.qaTileIconWhite}>🏥</Text>
            </View>
            <Text style={currentStyles.qaTileText}>Medical</Text>
          </TouchableOpacity>
          <TouchableOpacity style={currentStyles.qaTileSquare} onPress={() => openQuickFind('Police Station')}>
            <View style={[currentStyles.qaIconContainer, {backgroundColor: '#1E40AF'}]}>
              <Text style={currentStyles.qaTileIconWhite}>🚓</Text>
            </View>
            <Text style={currentStyles.qaTileText}>Police</Text>
          </TouchableOpacity>
        </View>
        <TouchableOpacity onPress={handleSOSTap} style={currentStyles.sosButton}>
          <View style={currentStyles.sosTextContainer}>
            <Text style={currentStyles.sosTitle}>EMERGENCY SOS</Text>
            <Text style={currentStyles.sosSubtitle}>Tap for immediate help</Text>
          </View>
          <Text style={currentStyles.sosArrow}>→</Text>
        </TouchableOpacity>
      </View>
      </ScrollView>
    </View>
  );



  const renderActiveJourney = () => {
    if (!journey || !selectedRoute) return null;

    const riskColor = selectedRoute.risk_score >= 70 ? '#DC2626' : (selectedRoute.risk_score >= 40 ? '#F59E0B' : '#10B981');
    const riskLabel = selectedRoute.risk_score >= 70 ? 'High' : (selectedRoute.risk_score >= 40 ? 'Moderate' : 'Low');

    return (
      <View style={{flex: 1, paddingBottom: 20}}>
        {/* Active Journey Header */}
        <View style={currentStyles.ajHeader}>
          <View style={{flexDirection: 'row', alignItems: 'center'}}>
            <TouchableOpacity onPress={() => setJourney(null)} style={{marginRight: 16}}>
              <Text style={currentStyles.ajBackArrow}>←</Text>
            </TouchableOpacity>
            <View>
              <Text style={currentStyles.ajTitle}>Active Journey</Text>
              <Text style={currentStyles.ajSubtitle}>You're on your way</Text>
            </View>
          </View>
          <TouchableOpacity style={currentStyles.ajHeaderSosBtn} onPress={handleSOSTap}>
            <Text style={currentStyles.ajHeaderSosIcon}>📞</Text>
            <Text style={currentStyles.ajHeaderSosText}>SOS</Text>
          </TouchableOpacity>
        </View>

        {/* Compact Journey Form */}
        <JourneyForm 
          onAnalyze={handleAnalyze} 
          loading={loading}
          compact={true}
          initialOriginText={routeLabels.origin || ''}
          initialDestinationText={routeLabels.destination || ''}
        />

        {/* Map Container */}
        <View style={currentStyles.ajMapContainer}>
          <JourneyMap 
            origin={journey.origin}
            destination={journey.destination}
            segments={selectedRoute.segments}
            selectedSegmentId={selectedSegment?.segment_id || null}
            onSegmentPress={setSelectedSegment}
            washrooms={washrooms}
            showWashrooms={showWashrooms}
            onNavigateRequest={openSelectedRouteInGoogleMaps}
            onWashroomPress={(washroom) => setSelectedWashroom(washroom)}
          />
        </View>

        <View style={currentStyles.amenityToggleRow}>
          <View style={{ flex: 1 }}>
            <Text style={currentStyles.amenityToggleTitle}>Right to PEE</Text>
            <Text style={currentStyles.amenityToggleCaption}>
              {washroomsLoading ? 'Loading nearby washrooms…' : washroomsError || (washrooms.length ? `${washrooms.length} nearby washrooms available on the map` : 'Show nearby washroom locations on the map')}
            </Text>
          </View>
          <TouchableOpacity
            accessibilityRole="switch"
            accessibilityState={{ checked: showWashrooms }}
            accessibilityLabel="Show nearby washroom locations"
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

        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel="Navigate selected safe route in Google Maps"
          onPress={openSelectedRouteInGoogleMaps}
          style={currentStyles.googleMapsButton}
        >
          <Text style={currentStyles.googleMapsButtonText}>NAVIGATE SAFE ROUTE IN GOOGLE MAPS</Text>
        </TouchableOpacity>
        <Text style={currentStyles.googleMapsHint}>Tap an empty map area or this button to open the selected route in Google Maps.</Text>

        {/* Safety Summary Card */}
        <View style={currentStyles.ajSafetyCard}>
          <View style={currentStyles.ajSafetyLeft}>
            <View style={[currentStyles.ajSafetyShield, {borderColor: riskColor}]}>
              <Text style={{fontSize: 24, color: riskColor, fontWeight: 'bold'}}>!</Text>
            </View>
            <View style={{flex: 1, paddingLeft: 12}}>
              <Text style={[currentStyles.ajSafetyTitle, {color: riskColor}]}>{riskLabel} Risk</Text>
              <Text style={currentStyles.ajSafetyDesc}>Stay alert and aware of your surroundings.</Text>
            </View>
          </View>
          <View style={currentStyles.ajSafetyDivider} />
          <View style={currentStyles.ajSafetyMiddle}>
            <View style={{flexDirection: 'row', alignItems: 'baseline'}}>
              <Text style={[currentStyles.ajSafetyScore, {color: riskColor}]}>{selectedRoute.risk_score.toFixed(0)}</Text>
              <Text style={currentStyles.ajSafetyScoreMax}> / 100</Text>
            </View>
            <Text style={currentStyles.ajSafetyLabel}>Risk Score</Text>
          </View>
          <View style={currentStyles.ajSafetyDivider} />
          <View style={currentStyles.ajSafetyRight}>
            <Text style={currentStyles.ajSafetyStatVal}>{Math.round(selectedRoute.duration_s / 60)} <Text style={currentStyles.ajSafetyStatUnit}>min</Text></Text>
            <Text style={currentStyles.ajSafetyLabel}>ETA</Text>
            <Text style={[currentStyles.ajSafetyStatVal, {marginTop: 6}]}>{(selectedRoute.distance_m / 1000).toFixed(1)} <Text style={currentStyles.ajSafetyStatUnit}>km</Text></Text>
            <Text style={currentStyles.ajSafetyLabel}>Distance</Text>
          </View>
        </View>

        {/* Route Options List injected into Active Journey */}
        {journey.ranking && (
          <View style={{ marginBottom: 16 }}>
            {showRouteOptions ? (
              <RouteOptionsList 
                ranking={journey.ranking}
                selectedRouteId={selectedRoute?.route_id || null}
                onSelectRoute={(route) => {
                  setSelectedRoute(route);
                  setSelectedSegment(route.segments && route.segments.length > 0 ? route.segments[0] : null);
                  setShowRouteOptions(false);
                }}
                onOpenMaps={openSelectedRouteInGoogleMaps}
              />
            ) : (
              <SakhiButton 
                title="Change route ▾" 
                variant="secondary" 
                onPress={() => setShowRouteOptions(true)} 
              />
            )}
          </View>
        )}

        {/* Quick Actions */}
        <Text style={currentStyles.ajSectionTitle}>Quick Actions</Text>
        <View style={currentStyles.ajQuickActionsRow}>
          <TouchableOpacity style={currentStyles.ajQaTile} onPress={() => openQuickFind('Washroom')}>
            <Text style={currentStyles.ajQaIcon}>🚻</Text>
            <Text style={currentStyles.ajQaText}>Washroom</Text>
          </TouchableOpacity>
          <TouchableOpacity style={currentStyles.ajQaTile} onPress={() => openQuickFind('Medical Clinic')}>
            <Text style={currentStyles.ajQaIcon}>🏥</Text>
            <Text style={currentStyles.ajQaText}>Medical</Text>
          </TouchableOpacity>
          <TouchableOpacity style={currentStyles.ajQaTile} onPress={() => openQuickFind('Police Station')}>
            <Text style={currentStyles.ajQaIcon}>🚓</Text>
            <Text style={currentStyles.ajQaText}>Police</Text>
          </TouchableOpacity>
          <TouchableOpacity style={currentStyles.ajQaTile} onPress={() => openQuickFind()}>
            <Text style={currentStyles.ajQaIcon}>🔍</Text>
            <Text style={currentStyles.ajQaText}>Quick Find</Text>
          </TouchableOpacity>
        </View>

        {/* Action Cards */}
        <TouchableOpacity style={currentStyles.ajActionCardRed} onPress={() => setShowReportModal(true)}>
          <Text style={currentStyles.ajActionIconRed}>⚠️</Text>
          <View style={currentStyles.ajActionTextCont}>
            <Text style={currentStyles.ajActionTitleRed}>Report an incident</Text>
            <Text style={currentStyles.ajActionDescRed}>Help us make journeys safer for everyone.</Text>
          </View>
          <Text style={currentStyles.ajActionArrowRed}>→</Text>
        </TouchableOpacity>

        <TouchableOpacity style={currentStyles.ajActionCardWhite} onPress={() => setShowSafetyDetails(!showSafetyDetails)}>
          <Text style={currentStyles.ajActionIconGray}>🛡️</Text>
          <View style={currentStyles.ajActionTextCont}>
            <Text style={currentStyles.ajActionTitleDark}>View safety details</Text>
            <Text style={currentStyles.ajActionDescGray}>See risk factors and recommendations</Text>
          </View>
          <Text style={currentStyles.ajActionArrowGray}>{showSafetyDetails ? '↓' : '→'}</Text>
        </TouchableOpacity>

        {showSafetyDetails && selectedSegment && (
          <View style={{ marginTop: 8, marginBottom: 16 }}>
            <SegmentSafetyPanel 
              segment={selectedSegment} 
              onReportIncident={() => setShowReportModal(true)}
            />
          </View>
        )}

        <TouchableOpacity style={currentStyles.ajActionCardSos} onPress={handleSOSTap}>
          <View style={currentStyles.ajSosSquare}>
            <Text style={currentStyles.ajSosSquareText}>SOS</Text>
          </View>
          <View style={currentStyles.ajActionTextCont}>
            <Text style={currentStyles.ajActionTitleSos}>EMERGENCY SOS</Text>
            <Text style={currentStyles.ajActionDescSos}>Tap for immediate help</Text>
          </View>
          <Text style={currentStyles.ajActionArrowSos}>📞</Text>
        </TouchableOpacity>

        <View style={currentStyles.ajFooter}>
          <Text style={currentStyles.ajFooterText}>🔒 Your location is being shared with trusted contacts</Text>
        </View>
      </View>
    );
  };

  return (
    <NavigationContainer ref={navigationRef}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarIcon: ({ focused, color, size }) => {
            let iconName = 'home';
            if (route.name === 'Home') iconName = focused ? 'home' : 'home-outline';
            else if (route.name === 'Journeys') iconName = focused ? 'map' : 'map-outline';
            else if (route.name === 'Amenities') iconName = focused ? 'business' : 'business-outline';
            else if (route.name === 'Profile') iconName = focused ? 'person' : 'person-outline';
            return <Ionicons name={iconName as any} size={size} color={color} />;
          },
          tabBarActiveTintColor: '#DC2626',
          tabBarInactiveTintColor: '#9CA3AF',
          tabBarStyle: {
            backgroundColor: '#ffffff',
            borderTopWidth: 1,
            borderColor: '#F3F4F6',
            height: 60,
            paddingBottom: 5,
          }
        })}
      >
        <Tab.Screen name="Home">
          {() => renderHome()}
        </Tab.Screen>
        <Tab.Screen name="Journeys">
          {() => (
            <View style={currentStyles.container}>
              {journey && isActiveJourney ? (
                <ScrollView 
                  style={{flex: 1}} 
                  contentContainerStyle={[currentStyles.content, { paddingHorizontal: spacing.screenHorizontal }]}
                  keyboardShouldPersistTaps="handled"
                >
                  {renderActiveJourney()}
                </ScrollView>
              ) : journey ? (
                <View style={{flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, backgroundColor: '#FDFCFD'}}>
                  <View style={{ width: 80, height: 80, borderRadius: 40, backgroundColor: '#FEF2F2', justifyContent: 'center', alignItems: 'center', marginBottom: 24 }}>
                    <Ionicons name="navigate" size={36} color="#DC2626" />
                  </View>
                  <SakhiText variant="h2" style={{marginBottom: 12}}>Active Journey</SakhiText>
                  <SakhiText variant="body" color="secondary" style={{textAlign: 'center', marginBottom: 32, maxWidth: 280, lineHeight: 22}}>
                    You currently have an ongoing journey in progress.
                  </SakhiText>
                  <View style={{ width: '100%', maxWidth: 320 }}>
                    <SakhiButton title="Continue journey →" onPress={() => setIsActiveJourney(true)} />
                    <SakhiButton title="End journey" variant="secondary" style={{marginTop: 16}} onPress={() => { setJourney(null); setIsActiveJourney(false); }} />
                  </View>
                </View>
              ) : (
                <View style={{flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, backgroundColor: '#FDFCFD'}}>
                  <View style={{ width: 80, height: 80, borderRadius: 40, backgroundColor: '#F3F4F6', justifyContent: 'center', alignItems: 'center', marginBottom: 24 }}>
                    <Ionicons name="map-outline" size={36} color="#9CA3AF" />
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
            const amenityCardStyle = { width: '47%' as const, backgroundColor: '#FFF', padding: 16, borderRadius: 16, shadowColor: '#000', shadowOffset: {width: 0, height: 2}, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2, borderWidth: 1, borderColor: '#F3F4F6', alignItems: 'center' as const, marginBottom: 16 };
            const amenityIconBoxStyle = { width: 48, height: 48, borderRadius: 12, justifyContent: 'center' as const, alignItems: 'center' as const };
            return (
              <View style={{flex: 1, padding: 24, paddingTop: 60, backgroundColor: '#FDFCFD'}}>
                <View style={{marginBottom: 32}}>
                  <SakhiText variant="h1" style={{marginBottom: 8}}>Amenities</SakhiText>
                  <SakhiText variant="body" color="secondary" style={{lineHeight: 22}}>
                    Find help and essential facilities quickly along your route or nearby.
                  </SakhiText>
                </View>
                
                <View style={{flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between'}}>
                  <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind('Washroom')}>
                    <View style={[amenityIconBoxStyle, {backgroundColor: '#DC2626'}]}>
                      <Ionicons name="water" size={24} color="#FFF" />
                    </View>
                    <SakhiText variant="body" style={{marginTop: 12, fontWeight: '600'}}>Washrooms</SakhiText>
                  </TouchableOpacity>

                  <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind('Medical Clinic')}>
                    <View style={[amenityIconBoxStyle, {backgroundColor: '#14B8A6'}]}>
                      <Ionicons name="medkit" size={24} color="#FFF" />
                    </View>
                    <SakhiText variant="body" style={{marginTop: 12, fontWeight: '600'}}>Medical</SakhiText>
                  </TouchableOpacity>

                  <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind('Police Station')}>
                    <View style={[amenityIconBoxStyle, {backgroundColor: '#1E40AF'}]}>
                      <Ionicons name="shield-checkmark" size={24} color="#FFF" />
                    </View>
                    <SakhiText variant="body" style={{marginTop: 12, fontWeight: '600'}}>Police</SakhiText>
                  </TouchableOpacity>

                  <TouchableOpacity style={amenityCardStyle} onPress={() => openQuickFind()}>
                    <View style={[amenityIconBoxStyle, {backgroundColor: '#4B5563'}]}>
                      <Ionicons name="search" size={24} color="#FFF" />
                    </View>
                    <SakhiText variant="body" style={{marginTop: 12, fontWeight: '600'}}>Quick Find</SakhiText>
                  </TouchableOpacity>
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
                        <Ionicons name="eye" size={18} color="#4B5563" />
                      </View>
                      <SakhiText variant="body" style={{fontWeight: '500'}}>Accessibility Mode</SakhiText>
                    </View>
                    <Switch 
                      value={isAccessibleMode} 
                      onValueChange={toggleAccessibleMode} 
                      trackColor={{ true: '#DC2626', false: '#D1D5DB' }} 
                      thumbColor="#FFF"
                    />
                  </View>
                </SakhiCard>

                <SakhiText variant="h3" style={{marginBottom: 12, marginTop: 32}}>About</SakhiText>
                <SakhiCard>
                  <View style={{flexDirection: 'row', alignItems: 'center'}}>
                    <View style={{width: 36, height: 36, borderRadius: 18, backgroundColor: '#F3F4F6', justifyContent: 'center', alignItems: 'center', marginRight: 12}}>
                      <Ionicons name="information-circle" size={18} color="#4B5563" />
                    </View>
                    <View>
                      <SakhiText variant="body" style={{fontWeight: '500'}}>SAKHI</SakhiText>
                      <SakhiText variant="caption" color="secondary">Version 1.0.0</SakhiText>
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

      <WashroomFacilityCard
        visible={!!selectedWashroom}
        onClose={() => setSelectedWashroom(null)}
        washroom={selectedWashroom}
        distance={selectedWashroom && userLocation ? calculateDistance(userLocation.coords.latitude, userLocation.coords.longitude, selectedWashroom.latitude, selectedWashroom.longitude) : 0}
      />
    </NavigationContainer>
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
  },
  
  /* --- NEW HOME SCREEN STYLES --- */
  homeScrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 100, // Room for bottom nav
  },
  homeBackground: {
    flex: 1,
    backgroundColor: '#FDFCFD', // Very light off-white
    minHeight: '100%',
  },
  skylineWrapper: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 400,
    opacity: 0.1, // Very subtle
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  skylineDome1: {
    width: 150,
    height: 150,
    backgroundColor: '#DC2626',
    borderTopLeftRadius: 75,
    borderTopRightRadius: 75,
    position: 'absolute',
    bottom: 50,
    left: -20,
  },
  skylineDome2: {
    width: 200,
    height: 250,
    backgroundColor: '#DC2626',
    borderTopLeftRadius: 100,
    borderTopRightRadius: 100,
    position: 'absolute',
    bottom: 30,
    left: 80,
  },
  skylineDome3: {
    width: 120,
    height: 180,
    backgroundColor: '#DC2626',
    borderTopLeftRadius: 60,
    borderTopRightRadius: 60,
    position: 'absolute',
    bottom: 40,
    right: 40,
  },
  skylineDome4: {
    width: 80,
    height: 100,
    backgroundColor: '#DC2626',
    borderTopLeftRadius: 40,
    borderTopRightRadius: 40,
    position: 'absolute',
    bottom: 20,
    right: -10,
  },
  homeHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 30,
    zIndex: 10,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoShield: {
    width: 32,
    height: 40,
    backgroundColor: '#FEF2F2',
    borderWidth: 2,
    borderColor: '#DC2626',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  logoShieldIcon: {
    fontSize: 16,
    color: '#DC2626',
  },
  logoTitle: {
    fontSize: 22,
    fontWeight: '900',
    color: '#DC2626', // SAKHI Red
    letterSpacing: 1,
  },
  logoSubtitle: {
    fontSize: 10,
    color: '#4B5563',
    fontWeight: '500',
  },
  profileBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#ffffff',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  profileDot: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#DC2626',
    borderWidth: 1,
    borderColor: '#fff',
  },
  heroContainer: {
    alignItems: 'flex-start',
    marginBottom: 20,
    zIndex: 10,
  },
  heroTextDark: {
    fontSize: 32,
    fontWeight: '900',
    color: '#1F2937',
  },
  heroTextRed: {
    fontSize: 32,
    fontWeight: '900',
    color: '#DC2626', 
  },
  heroHeart: {
    fontSize: 28,
    color: '#DC2626',
    fontWeight: '300',
    marginLeft: 6,
  },
  heroSubtitle: {
    fontSize: 14,
    color: '#4B5563',
    marginTop: 8,
    fontWeight: '500',
  },
  quickAccessContainer: {
    marginTop: 10,
    paddingBottom: 20,
  },
  quickAccessHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  quickAccessLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  quickAccessSeeAll: {
    fontSize: 14,
    fontWeight: '600',
    color: '#DC2626',
  },
  quickAccessRow3: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 12,
  },
  quickAccessRow2: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 20,
  },
  qaTileSquare: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#F3F4F6',
    aspectRatio: 1, // Make it perfectly square
  },
  qaIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  qaTileIconWhite: {
    fontSize: 18,
    color: '#fff',
  },
  qaTileText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1F2937',
  },
  qaTilePill: {
    flex: 1,
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  qaTileIconSmall: {
    fontSize: 16,
    marginRight: 6,
  },
  qaTileTextDark: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1F2937',
  },
  qaTileTextRed: {
    fontSize: 13,
    fontWeight: '600',
    color: '#DC2626',
  },
  sosCard: {
    backgroundColor: '#FEF2F2', // Light red bg
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    flexDirection: 'row',
    shadowColor: '#DC2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 3,
  },
  sosIconBox: {
    backgroundColor: '#DC2626',
    borderRadius: 12,
    width: 50,
    height: 50,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  sosIconText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  sosTextContainer: {
    flex: 1,
  },
  sosTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#DC2626',
  },
  sosSubtitle: {
    fontSize: 12,
    color: '#F87171',
    marginTop: 2,
  },
  sosArrow: {
    fontSize: 20,
    color: '#DC2626',
  },
  bottomNavContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 80,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderColor: '#F3F4F6',
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingBottom: 20, // For safe area
  },
  navItem: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 70,
  },
  navIconActive: {
    fontSize: 24,
    color: '#DC2626',
    marginBottom: 4,
  },
  navIconInactive: {
    fontSize: 24,
    color: '#9CA3AF',
    marginBottom: 4,
  },
  navTextActive: {
    fontSize: 10,
    color: '#DC2626',
    fontWeight: '600',
  },
  navTextInactive: {
    fontSize: 10,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  navIndicator: {
    position: 'absolute',
    bottom: -8,
    width: 30,
    height: 3,
    backgroundColor: '#DC2626',
    borderRadius: 2,
  },
  /* --- ACTIVE JOURNEY STYLES --- */
  ajHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    marginTop: 10,
  },
  ajBackArrow: {
    fontSize: 24,
    color: '#DC2626',
    fontWeight: 'bold',
  },
  ajTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  ajSubtitle: {
    fontSize: 12,
    color: '#6B7280',
  },
  ajHeaderSosBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#DC2626',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#fff',
  },
  ajHeaderSosIcon: {
    fontSize: 14,
    marginRight: 4,
    color: '#DC2626',
  },
  ajHeaderSosText: {
    color: '#DC2626',
    fontWeight: 'bold',
    fontSize: 12,
  },
  ajRouteSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    paddingHorizontal: 30,
  },
  ajRouteSummaryDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#DC2626',
    marginRight: 8,
  },
  ajRouteSummaryText: {
    fontSize: 12,
    color: '#1F2937',
    flex: 1,
  },
  ajRouteSummaryArrow: {
    marginHorizontal: 8,
    color: '#1F2937',
  },
  ajRouteSummaryPin: {
    fontSize: 14,
    marginRight: 4,
  },
  ajMapContainer: {
    height: 300,
    borderRadius: 16, // Use borderRadius but no overflow: hidden to avoid clipping Leaflet controls if any stick out
    backgroundColor: '#E5E7EB',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  ajSafetyCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#F3F4F6',
    alignItems: 'center',
  },
  ajSafetyLeft: {
    flex: 2,
    flexDirection: 'row',
    alignItems: 'center',
  },
  ajSafetyShield: {
    width: 40,
    height: 40,
    borderRadius: 8,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ajSafetyTitle: {
    fontSize: 14,
    fontWeight: 'bold',
  },
  ajSafetyDesc: {
    fontSize: 10,
    color: '#4B5563',
    marginTop: 2,
  },
  ajSafetyDivider: {
    width: 1,
    height: '100%',
    backgroundColor: '#E5E7EB',
    marginHorizontal: 12,
  },
  ajSafetyMiddle: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ajSafetyScore: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  ajSafetyScoreMax: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: 'bold',
  },
  ajSafetyLabel: {
    fontSize: 10,
    color: '#6B7280',
    marginTop: 2,
  },
  ajSafetyRight: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ajSafetyStatVal: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  ajSafetyStatUnit: {
    fontSize: 10,
    fontWeight: 'normal',
    color: '#6B7280',
  },
  ajPrimaryBtn: {
    backgroundColor: '#DC2626',
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    marginBottom: 20,
  },
  ajPrimaryBtnIcon: {
    color: '#fff',
    fontSize: 16,
    marginRight: 8,
  },
  ajPrimaryBtnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
    letterSpacing: 0.5,
  },
  ajPrimaryBtnArrow: {
    color: '#fff',
    fontSize: 18,
    marginLeft: 8,
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
    backgroundColor: '#fff',
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
  ajQaIcon: {
    fontSize: 24,
    marginBottom: 6,
  },
  ajQaText: {
    fontSize: 10,
    color: '#1F2937',
    fontWeight: '600',
  },
  ajActionCardRed: {
    backgroundColor: '#FEF2F2',
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#FCA5A5',
  },
  ajActionIconRed: {
    fontSize: 24,
    marginRight: 16,
  },
  ajActionTextCont: {
    flex: 1,
  },
  ajActionTitleRed: {
    color: '#DC2626',
    fontWeight: 'bold',
    fontSize: 14,
  },
  ajActionDescRed: {
    color: '#DC2626',
    fontSize: 10,
    marginTop: 2,
    opacity: 0.8,
  },
  ajActionArrowRed: {
    color: '#DC2626',
    fontSize: 18,
  },
  ajActionCardWhite: {
    backgroundColor: '#fff',
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
  ajActionIconGray: {
    fontSize: 24,
    marginRight: 16,
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
  ajActionArrowGray: {
    color: '#6B7280',
    fontSize: 18,
  },
  ajActionCardSos: {
    backgroundColor: '#FEF2F2',
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 20,
    shadowColor: '#DC2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  ajSosSquare: {
    backgroundColor: '#DC2626',
    borderRadius: 8,
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  ajSosSquareText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  ajActionTitleSos: {
    color: '#DC2626',
    fontWeight: 'bold',
    fontSize: 14,
  },
  ajActionDescSos: {
    color: '#F87171',
    fontSize: 10,
    marginTop: 2,
  },
  ajActionArrowSos: {
    fontSize: 20,
    color: '#DC2626',
  },
  ajFooter: {
    alignItems: 'center',
    paddingTop: 10,
  },
  ajFooterText: {
    fontSize: 10,
    color: '#9CA3AF',
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



