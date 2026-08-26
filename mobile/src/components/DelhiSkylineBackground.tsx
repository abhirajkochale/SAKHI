import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';

const { width } = Dimensions.get('window');

export default function DelhiSkylineBackground() {
  return (
    <View style={styles.container} pointerEvents="none">
      {/* Soft Pastel Background Base */}
      <View style={styles.gradientBase} />

      {/* Soft Sun / Circle Element */}
      <View style={styles.sunCircle} />

      {/* Soft Cloud Shapes */}
      <View style={[styles.cloud, styles.cloud1]} />
      <View style={[styles.cloud, styles.cloud2]} />

      {/* Minarets / Qutub Minar Silhouette */}
      <View style={styles.monumentWrapper}>
        <View style={styles.towerLeft}>
          <View style={styles.towerTop} />
          <View style={styles.towerBody} />
        </View>

        {/* Dome / Tomb Silhouette (Humayun's Tomb / Lotus Temple / Dome) */}
        <View style={styles.domeCenter}>
          <View style={styles.domeFinial} />
          <View style={styles.domeCupola} />
          <View style={styles.domeBase} />
        </View>

        {/* Arch Silhouette (India Gate) */}
        <View style={styles.archRight}>
          <View style={styles.archTop} />
          <View style={styles.archPillars}>
            <View style={styles.archPillar} />
            <View style={styles.archOpening} />
            <View style={styles.archPillar} />
          </View>
        </View>
      </View>

      {/* Trees Silhouette */}
      <View style={styles.treesRow}>
        <View style={[styles.tree, styles.tree1]} />
        <View style={[styles.tree, styles.tree2]} />
        <View style={[styles.tree, styles.tree3]} />
      </View>

      {/* Winding Road / Horizon Path */}
      <View style={styles.roadPath} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 280,
    overflow: 'hidden',
    backgroundColor: '#FDF7F6', // Soft pastel pink/cream tone
  },
  gradientBase: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#FDF5F4',
  },
  sunCircle: {
    position: 'absolute',
    top: 90,
    right: width * 0.32,
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(235, 175, 160, 0.28)', // Soft pastel sun
  },
  cloud: {
    position: 'absolute',
    backgroundColor: 'rgba(255, 255, 255, 0.6)',
    borderRadius: 20,
  },
  cloud1: {
    top: 60,
    left: 30,
    width: 70,
    height: 18,
  },
  cloud2: {
    top: 85,
    right: 40,
    width: 90,
    height: 22,
  },
  monumentWrapper: {
    position: 'absolute',
    bottom: 50,
    left: 20,
    right: 20,
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    opacity: 0.18, // Very subtle, low contrast pastel silhouette
  },
  towerLeft: {
    alignItems: 'center',
    marginBottom: 5,
  },
  towerTop: {
    width: 6,
    height: 12,
    backgroundColor: '#9E4A48',
    borderTopLeftRadius: 3,
    borderTopRightRadius: 3,
  },
  towerBody: {
    width: 14,
    height: 70,
    backgroundColor: '#9E4A48',
    borderTopLeftRadius: 4,
    borderTopRightRadius: 4,
  },
  domeCenter: {
    alignItems: 'center',
  },
  domeFinial: {
    width: 4,
    height: 10,
    backgroundColor: '#9E4A48',
  },
  domeCupola: {
    width: 42,
    height: 30,
    borderTopLeftRadius: 21,
    borderTopRightRadius: 21,
    backgroundColor: '#9E4A48',
  },
  domeBase: {
    width: 58,
    height: 35,
    backgroundColor: '#9E4A48',
    borderTopLeftRadius: 6,
    borderTopRightRadius: 6,
  },
  archRight: {
    alignItems: 'center',
  },
  archTop: {
    width: 50,
    height: 14,
    backgroundColor: '#9E4A48',
    borderRadius: 2,
  },
  archPillars: {
    flexDirection: 'row',
    width: 46,
    height: 45,
    backgroundColor: '#9E4A48',
    justifyContent: 'space-between',
    paddingHorizontal: 10,
  },
  archPillar: {
    width: 10,
    height: '100%',
    backgroundColor: '#FDF5F4',
  },
  archOpening: {
    width: 16,
    height: 30,
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
    backgroundColor: '#FDF5F4',
    alignSelf: 'flex-end',
  },
  treesRow: {
    position: 'absolute',
    bottom: 45,
    left: 10,
    right: 10,
    flexDirection: 'row',
    justifyContent: 'space-around',
    opacity: 0.14,
  },
  tree: {
    backgroundColor: '#8B4240',
    borderRadius: 15,
  },
  tree1: {
    width: 22,
    height: 22,
  },
  tree2: {
    width: 28,
    height: 28,
  },
  tree3: {
    width: 24,
    height: 24,
  },
  roadPath: {
    position: 'absolute',
    bottom: -15,
    left: -20,
    right: -20,
    height: 70,
    backgroundColor: 'rgba(242, 220, 218, 0.45)', // Soft curving road pastel tint
    borderTopLeftRadius: 180,
    borderTopRightRadius: 100,
    transform: [{ rotate: '-2deg' }],
  },
});
