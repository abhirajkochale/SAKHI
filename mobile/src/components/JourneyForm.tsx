import React, { useState } from 'react';
import { View, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Location } from '../types/api';
import { SakhiText } from './ui/SakhiText';
import { Ionicons } from '@expo/vector-icons';

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
  const [geocodeLoading, setGeocodeLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const geocodeAddress = async (address: string): Promise<Location | null> => {
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address)}&format=json&limit=1`, {
        headers: { 'User-Agent': 'SAKHI-Hackathon-App' }
      });
      const data = await res.json();
      if (data && data.length > 0) {
        return { latitude: parseFloat(data[0].lat), longitude: parseFloat(data[0].lon) };
      }
      return null;
    } catch (e) {
      console.error(e);
      return null;
    }
  };

  const handleAnalyze = async () => {
    setError(null);
    if (!originText || !destinationText) {
      setError("Please enter origin and destination addresses.");
      return;
    }
    
    let currentOrig = origin;
    let currentDest = destination;

    if (!currentOrig) {
      setGeocodeLoading(true);
      currentOrig = await geocodeAddress(originText);
      setGeocodeLoading(false);
      if (!currentOrig) {
        setError(`Could not find location for: ${originText}`);
        return;
      }
      setOrigin(currentOrig);
    }
    
    if (!currentDest) {
      setGeocodeLoading(true);
      currentDest = await geocodeAddress(destinationText);
      setGeocodeLoading(false);
      if (!currentDest) {
        setError(`Could not find location for: ${destinationText}`);
        return;
      }
      setDestination(currentDest);
    }
    
    onAnalyze(currentOrig, currentDest, originText, destinationText);
  };

  const swapLocations = () => {
    const tempText = originText;
    setOriginText(destinationText);
    setDestinationText(tempText);
    const tempLoc = origin;
    setOrigin(destination);
    setDestination(tempLoc);
  };

  if (compact) {
    return (
      <View style={styles.compactOuterContainer}>
        {error && <SakhiText color="danger" variant="caption" style={styles.error}>{error}</SakhiText>}
        <View style={styles.compactRow}>
          <View style={[styles.card, styles.compactCard]}>
            <View style={styles.compactGoogleLayout}>
              {/* Left Column Icons */}
              <View style={styles.compactIconCol}>
                <View style={styles.compactCircleIcon} />
                <Ionicons name="ellipsis-vertical" size={16} color="#9CA3AF" style={{marginVertical: 4}} />
                <View style={styles.compactPinIconOutline}>
                  <View style={styles.compactPinIconDot} />
                </View>
              </View>
              
              {/* Middle Column Inputs */}
              <View style={styles.compactInputCol}>
                <TextInput
                  style={styles.compactInputText}
                  value={originText}
                  onChangeText={(t) => { setOriginText(t); setOrigin(null); }}
                  placeholder="Choose starting point"
                  placeholderTextColor="#6B7280"
                  onSubmitEditing={handleAnalyze}
                  returnKeyType="search"
                />
                <View style={styles.compactDivider} />
                <TextInput
                  style={styles.compactInputText}
                  value={destinationText}
                  onChangeText={(t) => { setDestinationText(t); setDestination(null); }}
                  placeholder="Choose destination"
                  placeholderTextColor="#6B7280"
                  onSubmitEditing={handleAnalyze}
                  returnKeyType="search"
                />
              </View>
              
              {/* Right Column Actions */}
              <View style={styles.compactActionCol}>
                <TouchableOpacity style={{padding: 4}}>
                  <Ionicons name="ellipsis-vertical" size={20} color="#9CA3AF" />
                </TouchableOpacity>
                <TouchableOpacity style={{padding: 4, marginTop: 12}} onPress={swapLocations}>
                  <Ionicons name="swap-vertical" size={24} color="#6B7280" />
                </TouchableOpacity>
              </View>
            </View>
          </View>
          
          <TouchableOpacity 
            style={styles.compactSearchBtn} 
            onPress={handleAnalyze}
            disabled={!originText || !destinationText || loading || geocodeLoading}
          >
            {loading || geocodeLoading ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Ionicons name="search" size={24} color="#ffffff" />
            )}
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      {error && <SakhiText color="danger" variant="caption" style={styles.error}>{error}</SakhiText>}

      <View style={styles.inputGroup}>
        {/* Origin Row */}
        <View style={styles.row}>
          <View style={styles.iconContainer}>
            <View style={styles.originIconOuter}>
              <View style={styles.originIconInner} />
            </View>
          </View>
          <View style={styles.fieldContainer}>
            <SakhiText variant="caption" style={styles.label}>From</SakhiText>
            <TextInput
              style={styles.input}
              placeholder="Enter starting point"
              placeholderTextColor="#9ca3af"
              value={originText}
              onChangeText={(t) => { setOriginText(t); setOrigin(null); }}
            />
          </View>
        </View>

        {/* Dotted Connection Line */}
        <View style={styles.dottedLineContainer}>
          <View style={styles.dottedLine} />
        </View>

        {/* Destination Row */}
        <View style={styles.row}>
          <View style={styles.iconContainer}>
            <View style={styles.destinationIcon}>
              <View style={styles.destinationIconHole} />
            </View>
          </View>
          <View style={styles.fieldContainer}>
            <SakhiText variant="caption" style={styles.label}>To</SakhiText>
            <TextInput
              style={styles.input}
              placeholder="Enter destination"
              placeholderTextColor="#9ca3af"
              value={destinationText}
              onChangeText={(t) => { setDestinationText(t); setDestination(null); }}
            />
          </View>
        </View>
      </View>

      <TouchableOpacity 
        style={[styles.primaryCTA, (!originText || !destinationText) && styles.disabledCTA]} 
        onPress={handleAnalyze}
        disabled={!originText || !destinationText || loading || geocodeLoading}
      >
        {loading || geocodeLoading ? (
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
  }
});
