import React, { useRef, useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ActivityIndicator,
  BackHandler,
  Platform,
  SafeAreaView,
  StatusBar as RNStatusBar
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { WebView } from 'react-native-webview';

import { VolumeManager } from 'react-native-volume-manager';

const MOBILE_PLAYER_URL = 'https://mono-music-778r.vercel.app/mobile';

export default function App() {
  const webViewRef = useRef(null);
  const [canGoBack, setCanGoBack] = useState(false);
  const [currentVolume, setCurrentVolume] = useState(0.8);

  useEffect(() => {
    if (Platform.OS === 'android') {
      const onBackPress = () => {
        if (canGoBack && webViewRef.current) {
          webViewRef.current.goBack();
          return true;
        }
        return false;
      };

      const subscription = BackHandler.addEventListener('hardwareBackPress', onBackPress);
      return () => subscription.remove();
    }
  }, [canGoBack]);

  // Two-way synchronization with Real Phone Hardware Volume
  useEffect(() => {
    let volumeListener = null;

    // Fetch initial phone volume
    VolumeManager.getVolume().then((result) => {
      const vol = typeof result === 'number' ? result : (result && typeof result.volume === 'number' ? result.volume : 0.8);
      setCurrentVolume(vol);
      if (webViewRef.current) {
        webViewRef.current.postMessage(JSON.stringify({ type: 'VOLUME_CHANGED', volume: vol }));
      }
    }).catch(() => {});

    // Listen for physical hardware volume buttons (Volume Up / Down)
    try {
      volumeListener = VolumeManager.addVolumeListener((result) => {
        const vol = typeof result === 'number' ? result : (result && typeof result.volume === 'number' ? result.volume : 0.8);
        setCurrentVolume(vol);
        if (webViewRef.current) {
          webViewRef.current.postMessage(JSON.stringify({ type: 'VOLUME_CHANGED', volume: vol }));
        }
      });
    } catch (err) {
      console.warn('Volume listener error:', err);
    }

    return () => {
      if (volumeListener && typeof volumeListener.remove === 'function') {
        volumeListener.remove();
      }
    };
  }, []);

  // Handle messages from WebView (e.g. user drags in-app volume slider)
  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data && data.type === 'SET_VOLUME') {
        const targetVol = Math.max(0, Math.min(1, parseFloat(data.volume)));
        VolumeManager.setVolume(targetVol).catch(() => {});
      } else if (data && data.type === 'REQUEST_INITIAL_VOLUME') {
        VolumeManager.getVolume().then((result) => {
          const vol = typeof result === 'number' ? result : (result && typeof result.volume === 'number' ? result.volume : 0.8);
          if (webViewRef.current) {
            webViewRef.current.postMessage(JSON.stringify({ type: 'VOLUME_CHANGED', volume: vol }));
          }
        }).catch(() => {});
      }
    } catch (e) {}
  };

  const renderLoadingView = () => (
    <View style={styles.loadingContainer}>
      <View style={styles.recordCircle}>
        <View style={styles.recordInner} />
      </View>
      <Text style={styles.loadingTitle}>mono Music</Text>
      <Text style={styles.loadingSubtitle}>AUTHENTIC TELUGU AUDIO ENGINE (2000–2026)</Text>
      <ActivityIndicator size="small" color="#faf9f5" style={{ marginTop: 20 }} />
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" backgroundColor="#111111" />
      <WebView
        ref={webViewRef}
        source={{ uri: MOBILE_PLAYER_URL }}
        style={styles.webview}
        allowsInlineMediaPlayback={true}
        mediaPlaybackRequiresUserAction={false}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        cacheEnabled={true}
        allowFileAccess={true}
        allowsFullscreenVideo={true}
        scalesPageToFit={true}
        startInLoadingState={true}
        renderLoading={renderLoadingView}
        onNavigationStateChange={(navState) => setCanGoBack(navState.canGoBack)}
        onMessage={handleMessage}
        androidLayerType="hardware"
        applicationNameForUserAgent="monoMusicApp/1.0.0"
        onLoadEnd={() => {
          // Send phone volume once page finishes loading
          VolumeManager.getVolume().then((result) => {
            const vol = typeof result === 'number' ? result : (result && typeof result.volume === 'number' ? result.volume : 0.8);
            if (webViewRef.current) {
              webViewRef.current.postMessage(JSON.stringify({ type: 'VOLUME_CHANGED', volume: vol }));
            }
          }).catch(() => {});
        }}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111111',
    paddingTop: Platform.OS === 'android' ? RNStatusBar.currentHeight : 0,
  },
  webview: {
    flex: 1,
    backgroundColor: '#111111',
  },
  loadingContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#111111',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 999,
  },
  recordCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: '#1a1a1a',
    borderWidth: 2,
    borderColor: '#333333',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  recordInner: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#faf9f5',
  },
  loadingTitle: {
    color: '#faf9f5',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 22,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  loadingSubtitle: {
    color: '#888888',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    fontSize: 10,
    letterSpacing: 1,
    marginTop: 6,
  },
});
