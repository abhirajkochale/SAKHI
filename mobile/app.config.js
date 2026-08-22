const appConfig = require('./app.json');

module.exports = {
  ...appConfig.expo,
  android: {
    ...appConfig.expo.android,
    package: 'com.shounak.sakhi',
  },
};
