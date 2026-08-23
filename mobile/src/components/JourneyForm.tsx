import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import { Location } from '../types/api';
import { SakhiText } from './ui/SakhiText';
import { Ionicons } from '@expo/vector-icons';

// Real Connaught Place pilot locations from verified datasets
const CP_LOCATIONS: { name: string; coords: Location }[] = [
  { name: 'Rajiv Chowk Metro Station', coords: { latitude: 28.6328, longitude: 77.2197 } },
  { name: 'Connaught Place Inner Circle', coords: { latitude: 28.6315, longitude: 77.2167 } },
  { name: 'Janpath Market', coords: { latitude: 28.6265, longitude: 77.2195 } },
  { name: 'Palika Bazaar', coords: { latitude: 28.6308, longitude: 77.2185 } },
  { name: 'Parliament Street', coords: { latitude: 28.6253, longitude: 77.2144 } },
  { name: 'Barakhamba Road', coords: { latitude: 28.6340, longitude: 77.2260 } },
  { name: 'Mandi House Metro', coords: { latitude: 28.6258, longitude: 77.2337 } },
];

interface Props {
  onAnalyze: (origin: Location, destination: Location, originName: string, destName: string) => void;
  loading: boolean;
  compact?: boolean;
  initialOriginText?: string;
  initialDestinationText?: string;
}

export default function JourneyForm({ 
  onAnalyze, 
  loading, 
  compact = false,
  initialOriginText = '',
  initialDestinationText = ''
}: Props) {
  const [originText, setOriginText] = useState(initialOriginText);
  const [destinationText, setDestinationText] = useState(initialDestinationText);
  const [origin, setOrigin] = useState<Location | null>(null);
  const [destination, setDestination] = useState<Location | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showOriginPicker, setShowOriginPicker] = useState(false);
  const [showDestPicker, setShowDestPicker] = useState(false);

  const selectOrigin = (loc: typeof CP_LOCATIONS[0]) => {
    setOriginText(loc.name);
    setOrigin(loc.coords);
    setShowOriginPicker(false);
    setError(null);
  };

  const selectDestination = (loc: typeof CP_LOCATIONS[0]) => {
    setDestinationText(loc.name);
    setDestination(loc.coords);
    setShowDestPicker(false);
    setError(null);
  };

  const handleAnalyze = async () => {
    setError(null);
    if (!origin || !destination) {
      setError("Please select both origin and destination from the list.");
      return;
    }
    if (origin.latitude === destination.latitude && origin.longitude === destination.longitude) {
      setError("Origin and destination cannot be the same.");
      return;
    }
    onAnalyze(origin, destination, originText, destinationText);
  };

  const swapLocations = () => {
    const tempText = originText;
    setOriginText(destinationText);
    setDestinationText(tempText);
    const tempLoc = origin;
    setOrigin(destination);
    setDestination(tempLoc);
  };

  const LocationPicker = ({ onSelect, exclude }: { onSelect: (loc: typeof CP_LOCATIONS[0]) => void; exclude?: string }) => (
    <View style={styles.pickerDropdown}>
      <ScrollView style={{ maxHeight: 200 }} nestedScrollEnabled>
        {CP_LOCATIONS.filter(l => l.name !== exclude).map((loc) => (
          <TouchableOpacity key={loc.name} style={styles.pickerItem} onPress={() => onSelect(loc)}>
            <Ionicons name="location-outline" size={16} color="#DC2626" style={{ marginRight: 8 }} />
            <SakhiText variant="body" style={{ color: '#1F2937' }}>{loc.name}</SakhiText>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );

  if (compact) {
    return (
      <View style={styles.compactOuterContainer}>
        {error && <SakhiText color="danger" variant="caption" style={styles.error}>{error}</SakhiText>}
        <View style={styles.compactRow}>
          <View style={[styles.card, styles.compactCard]}>
            <View style={styles.compactGoogleLayout}>
              <View style={styles.compactIconCol}>
                <View style={styles.compactCircleIcon} />
                <Ionicons name="ellipsis-vertical" size={16} color="#9CA3AF" style={{marginVertical: 4}} />
                <View style={styles.compactPinIconOutline}>
                  <View style={styles.compactPinIconDot} />
                </View>
              </View>
              <View style={styles.compactInputCol}>
                <TouchableOpacity onPress={() => { setShowOriginPicker(!showOriginPicker); setShowDestPicker(false); }}>
                  <SakhiText style={[styles.compactInputText, !originText && { color: '#6B7280' }]}>
                    {originText || 'Choose starting point'}
                  </SakhiText>
                </TouchableOpacity>
                <View style={styles.compactDivider} />
                <TouchableOpacity onPress={() => { setShowDestPicker(!showDestPicker); setShowOriginPicker(false); }}>
                  <SakhiText style={[styles.compactInputText, !destinationText && { color: '#6B7280' }]}>
                    {destinationText || 'Choose destination'}
                  </SakhiText>
                </TouchableOpacity>
              </View>
              <View style={styles.compactActionCol}>
                <TouchableOpacity style={{padding: 4}} onPress={swapLocations}>
                  <Ionicons name="swap-vertical" size={24} color="#6B7280" />
                </TouchableOpacity>
              </View>
            </View>
          </View>
          <TouchableOpacity 
            style={styles.compactSearchBtn} 
            onPress={handleAnalyze}
            disabled={!origin || !destination || loading}
          >
            {loading ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Ionicons name="search" size={24} color="#ffffff" />
            )}
          </TouchableOpacity>
        </View>
        {showOriginPicker && <LocationPicker onSelect={selectOrigin} exclude={destinationText} />}
        {showDestPicker && <LocationPicker onSelect={selectDestination} exclude={originText} />}
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <SakhiText variant="caption" style={styles.pilotLabel}>CONNAUGHT PLACE PILOT — Supported locations only</SakhiText>
      {error && <SakhiText color="danger" variant="caption" style={styles.error}>{error}</SakhiText>}

      <View style={styles.inputGroup}>
        <TouchableOpacity style={styles.row} onPress={() => { setShowOriginPicker(!showOriginPicker); setShowDestPicker(false); }}>
          <View style={styles.iconContainer}>
            <View style={styles.originIconOuter}>
              <View style={styles.originIconInner} />
            </View>
          </View>
          <View style={styles.fieldContainer}>
            <SakhiText variant="caption" style={styles.label}>From</SakhiText>
            <SakhiText style={[styles.input, !originText && { color: '#9ca3af' }]}>
              {originText || 'Select starting point'}
            </SakhiText>
          </View>
          <Ionicons name="chevron-down" size={20} color="#9CA3AF" />
        </TouchableOpacity>
        {showOriginPicker && <LocationPicker onSelect={selectOrigin} exclude={destinationText} />}

        <View style={styles.dottedLineContainer}>
          <View style={styles.dottedLine} />
        </View>

        <TouchableOpacity style={styles.row} onPress={() => { setShowDestPicker(!showDestPicker); setShowOriginPicker(false); }}>
          <View style={styles.iconContainer}>
            <View style={styles.destinationIcon}>
              <View style={styles.destinationIconHole} />
            </View>
          </View>
          <View style={styles.fieldContainer}>
            <SakhiText variant="caption" style={styles.label}>To</SakhiText>
            <SakhiText style={[styles.input, !destinationText && { color: '#9ca3af' }]}>
              {destinationText || 'Select destination'}
            </SakhiText>
          </View>
          <Ionicons name="chevron-down" size={20} color="#9CA3AF" />
        </TouchableOpacity>
        {showDestPicker && <LocationPicker onSelect={selectDestination} exclude={originText} />}
      </View>

      <TouchableOpacity 
        style={[styles.primaryCTA, (!origin || !destination) && styles.disabledCTA]} 
        onPress={handleAnalyze}
        disabled={!origin || !destination || loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <View style={styles.ctaContent}>
            <SakhiText style={styles.ctaText}>FIND SAFEST ROUTE</SakhiText>
            <SakhiText style={styles.ctaIconRight}>→</SakhiText>
          </View>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 24, // Increased to match reference
    padding: 20,
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08, // Softer shadow
    shadowRadius: 16,
    elevation: 6,
    width: '100%',
    marginBottom: 24,
    zIndex: 10,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  error: {
    marginBottom: 16,
    textAlign: 'center',
  },
  inputGroup: {
    marginBottom: 20,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  iconContainer: {
    width: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  originIconOuter: {
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#DC2626', // Changed to Red
    alignItems: 'center',
    justifyContent: 'center',
  },
  originIconInner: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#DC2626', // Changed to Red
  },
  destinationIcon: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#DC2626', // Red map pin
    alignItems: 'center',
    justifyContent: 'center',
    borderBottomRightRadius: 0,
    transform: [{ rotate: '45deg' }],
  },
  destinationIconHole: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#fff',
  },
  dottedLineContainer: {
    width: 32,
    alignItems: 'center',
    height: 24,
  },
  dottedLine: {
    height: '100%',
    borderLeftWidth: 2,
    borderColor: '#E5E7EB',
    borderStyle: 'dashed',
  },
  fieldContainer: {
    flex: 1,
    justifyContent: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    paddingBottom: 8,
  },
  label: {
    color: '#DC2626', // Red label
    fontSize: 12,
    marginBottom: 2,
    fontWeight: '600',
  },
  input: {
    fontSize: 16,
    color: '#1F2937',
    fontWeight: '500',
    padding: 0,
    margin: 0,
  },
  primaryCTA: {
    backgroundColor: '#DC2626', // Solid Red
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabledCTA: {
    backgroundColor: '#FCA5A5', // Lighter red
  },
  ctaContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
  },
  ctaIconLeft: {
    color: '#fff',
    fontSize: 16,
    position: 'absolute',
    left: 24,
  },
  ctaText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  ctaIconRight: {
    color: '#ffffff',
    fontSize: 18,
    position: 'absolute',
    right: 24,
  },
  compactOuterContainer: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  compactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
  },
  compactSearchBtn: {
    backgroundColor: '#DC2626',
    marginLeft: 8,
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
    shadowColor: '#DC2626',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
  },
  compactCard: {
    flex: 1,
    borderRadius: 16,
    padding: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginBottom: 0,
    marginHorizontal: 0,
  },
  compactGoogleLayout: {
    flexDirection: 'row',
  },
  compactIconCol: {
    width: 32,
    alignItems: 'center',
    paddingTop: 8,
  },
  compactCircleIcon: {
    width: 12,
    height: 12,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: '#374151',
    backgroundColor: '#fff',
  },
  compactDotsIcon: {
    color: '#9CA3AF',
    fontSize: 16,
    lineHeight: 18,
    marginVertical: 4,
  },
  compactPinIconOutline: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 1.5,
    borderColor: '#DC2626',
    alignItems: 'center',
    justifyContent: 'center',
  },
  compactPinIconDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: '#DC2626',
  },
  compactInputCol: {
    flex: 1,
    paddingHorizontal: 8,
  },
  compactInputText: {
    fontSize: 15,
    color: '#1F2937',
    paddingVertical: 4,
    minHeight: 32,
  },
  compactDivider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginVertical: 4,
  },
  compactActionCol: {
    width: 40,
    alignItems: 'center',
    paddingTop: 4,
  },
  compactRightDots: {
    color: '#6B7280',
    fontSize: 18,
    fontWeight: 'bold',
  },
  compactSwapIcon: {
    color: '#4B5563',
    fontSize: 16,
    fontWeight: 'bold',
  },
  pilotLabel: {
    color: '#DC2626',
    fontSize: 10,
    fontWeight: 'bold',
    letterSpacing: 1,
    textAlign: 'center',
    marginBottom: 12,
  },
  pickerDropdown: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    marginTop: 4,
    marginBottom: 8,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  pickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
});
