const { getDefaultConfig } = require('expo/metro-config');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Add .ogg to the default asset extensions
config.resolver.assetExts.push('ogg');

module.exports = config;
