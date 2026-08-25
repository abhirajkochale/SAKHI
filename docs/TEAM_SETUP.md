# SAKHI Team Setup Guide

Welcome to the SAKHI development repository! Follow these instructions to set up your environment for local development and testing.

## A. Prerequisites
- **Node.js** (v18+)
- **npm**
- **Python** (v3.9+)
- **Java 17** (Required for Android builds, ensure JAVA_HOME is set)
- **Android Studio / Android SDK** (Required for native Android development)
- **Expo CLI** (Usage through 
px)

## B. Clone and Setup
`ash
git clone <repo-url>
cd SAKHI
`

## C. Mobile Dependencies
`ash
cd mobile
npm install
`

## D. Environment Configuration (Mobile)
We support two isolated app identities on Android:
- **SAKHI** (Standalone Release) -> com.anonymous.mobile
- **SAKHI Dev** (Development Build) -> com.sakhi.app.dev

To run the app in development mode, you **MUST** export the environment variable before starting Expo or performing native builds:
`powershell
$env:EXPO_PUBLIC_APP_ENV="development"
`

Create a .env file in the mobile directory using the .env.example as a template. Do **NOT** commit your .env file to version control.

## E. Start the Metro Bundler
Start the development server with the dev-client configuration:
`powershell
$env:EXPO_PUBLIC_APP_ENV="development"
npx expo start --dev-client --lan -c
`

## F. Build and Install the Android Development App
To test natively on an Android device or emulator, you must compile and push the SAKHI Dev app:
`powershell
$env:EXPO_PUBLIC_APP_ENV="development"
npx expo run:android -d
`
*Note: Android development can run locally via Android Studio/emulator or a physical Android device connected via USB with USB Debugging enabled.*

## G. Backend Setup
The backend is a FastAPI application running on Python.
`powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
`

## H. Backend Environment Variables
Create a local .env file inside the ackend directory. Do **NOT** commit it.
It should include:
`env
SUPABASE_URL=<your value>
SUPABASE_KEY=<your value>
DATABASE_URL=<your value>
# Add additional required API keys based on backend documentation
`

## I. Testing on iOS (iPhone)
iPhone testing relies on an iOS development/TestFlight workflow and requires a macOS machine with Xcode. This is managed separately from the Android local build pipeline.

## J. Supabase Development Redirect Requirement
For Google OAuth login to work correctly in the development client, the following URI **MUST** be added to your Supabase project's Authentication -> URL Configuration -> Additional Redirect URLs:
`
sakhi-dev://auth/callback
`
If this is missing, the OAuth popup will not redirect back to the SAKHI Dev app.

