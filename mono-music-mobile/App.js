import React, { useRef, useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  ActivityIndicator,
  BackHandler,
  Platform,
  SafeAreaView,
  StatusBar as RNStatusBar,
  AppState,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { WebView } from 'react-native-webview';
import { VolumeManager } from 'react-native-volume-manager';
import {
  setAudioModeAsync,
  createAudioPlayer,
  requestNotificationPermissionsAsync,
} from 'expo-audio';

const MOBILE_PLAYER_URL = 'https://mono-music-778r.vercel.app/mobile';

export default function App() {
  const webViewRef = useRef(null);
  const playerRef = useRef(null);
  const currentTrackRef = useRef(null);
  const queueRef = useRef([]);
  const isPlayingRef = useRef(false);
  const repeatModeRef = useRef(0); // 0: OFF, 1: ALL, 2: ONE
  const [canGoBack, setCanGoBack] = useState(false);
  const [currentVolume, setCurrentVolume] = useState(0.8);

  // 1. Initialize Native Background Audio & Android Permissions
  useEffect(() => {
    async function initAudio() {
      try {
        if (Platform.OS === 'android') {
          await requestNotificationPermissionsAsync().catch(() => {});
        }
        await setAudioModeAsync({
          playsInSilentMode: true,
          shouldPlayInBackground: true,
          interruptionMode: 'doNotMix',
        });
      } catch (err) {
        console.warn('Audio initialization error:', err);
      }
    }
    initAudio();

    return () => {
      if (playerRef.current) {
        try { playerRef.current.remove(); } catch (e) {}
        playerRef.current = null;
      }
    };
  }, []);

  // 2. Hardware Back Button Handling
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

  // 3. Two-way synchronization with Real Phone Hardware Volume
  useEffect(() => {
    let volumeListener = null;

    VolumeManager.getVolume().then((result) => {
      const vol = typeof result === 'number' ? result : (result && typeof result.volume === 'number' ? result.volume : 0.8);
      setCurrentVolume(vol);
      if (playerRef.current) playerRef.current.volume = vol;
      if (webViewRef.current) {
        webViewRef.current.postMessage(JSON.stringify({ type: 'VOLUME_CHANGED', volume: vol }));
      }
    }).catch(() => {});

    try {
      volumeListener = VolumeManager.addVolumeListener((result) => {
        const vol = typeof result === 'number' ? result : (result && typeof result.volume === 'number' ? result.volume : 0.8);
        setCurrentVolume(vol);
        if (playerRef.current) playerRef.current.volume = vol;
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

  // 4. Foreground AppState Synchronization (Sync instantly when unlocked or returned to)
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState) => {
      if (nextAppState === 'active' && webViewRef.current && currentTrackRef.current) {
        webViewRef.current.postMessage(JSON.stringify({
          type: 'SYNC_CURRENT_TRACK',
          track: currentTrackRef.current,
          isPlaying: isPlayingRef.current,
        }));
      }
    });
    return () => subscription.remove();
  }, []);

  // 5. Play Next Track in Queue (Runs seamlessly in foreground AND background)
  const playNextSong = () => {
    // If Repeat One is active, replay current track
    if (repeatModeRef.current === 2 && currentTrackRef.current) {
      if (playerRef.current) {
        playerRef.current.seekTo(0).catch(() => {});
        playerRef.current.play();
        isPlayingRef.current = true;
      }
      return;
    }

    if (!queueRef.current || queueRef.current.length === 0) {
      if (webViewRef.current) {
        webViewRef.current.postMessage(JSON.stringify({ type: 'REQUEST_MORE_QUEUE' }));
      }
      return;
    }

    const nextTrack = queueRef.current.shift();
    if (!nextTrack || !nextTrack.audioUrl) return;

    currentTrackRef.current = nextTrack;
    startNativePlayback(nextTrack);

    // Sync with WebView UI
    if (webViewRef.current) {
      webViewRef.current.postMessage(JSON.stringify({
        type: 'SYNC_CURRENT_TRACK',
        track: nextTrack,
      }));
    }

    // Auto-replenish queue if running low
    if (queueRef.current.length < 5 && webViewRef.current) {
      webViewRef.current.postMessage(JSON.stringify({
        type: 'REQUEST_MORE_QUEUE',
        currentTrack: nextTrack,
      }));
    }
  };

  // 6. Start or Replace Native Audio Playback
  const startNativePlayback = (track, playbackRate = 1.0) => {
    if (!track || !track.audioUrl) return;

    try {
      if (!playerRef.current) {
        const player = createAudioPlayer(track.audioUrl, {
          updateInterval: 500,
          keepAudioSessionActive: true,
        });

        player.addListener('playbackStatusUpdate', (status) => {
          if (!status) return;
          isPlayingRef.current = status.playing;

          // Broadcast playback status to WebView
          if (webViewRef.current && status.isLoaded) {
            webViewRef.current.postMessage(JSON.stringify({
              type: 'NATIVE_PLAYBACK_STATUS',
              currentTime: status.currentTime,
              duration: status.duration,
              isPlaying: status.playing,
            }));
          }

          // Continuous Chained Playback: when song finishes, automatically advance to next song!
          if (status.didJustFinish) {
            playNextSong();
          }

          // In case of an unexpected stream error, gracefully skip to next song
          if (status.error) {
            console.warn('Playback error detected, skipping to next song:', status.error);
            playNextSong();
          }
        });

        playerRef.current = player;
      } else {
        playerRef.current.replace(track.audioUrl);
      }

      playerRef.current.volume = currentVolume;
      playerRef.current.playbackRate = playbackRate;
      playerRef.current.play();
      isPlayingRef.current = true;

      // Register Android Lock Screen & Notification Center Controls
      try {
        playerRef.current.setActiveForLockScreen(
          true,
          {
            title: track.title || 'mono Music',
            artist: track.singers || track.composer || track.movie || 'Tollywood Artists',
            albumTitle: track.movie || 'Telugu Hits',
            artworkUrl: track.image || 'https://mono-music-778r.vercel.app/assets/icon.png',
          },
          {
            showNextTrack: true,
            showPreviousTrack: true,
            showSeekForward: true,
            showSeekBackward: true,
          }
        );
      } catch (e) {}
    } catch (err) {
      console.warn('Failed to start native playback:', err);
    }
  };

  // 7. Handle messages from WebView
  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (!data) return;

      if (data.type === 'PLAY_TRACK') {
        currentTrackRef.current = data.track;
        queueRef.current = Array.isArray(data.queue) ? [...data.queue] : [];
        startNativePlayback(data.track, data.playbackRate || 1.0);
      } else if (data.type === 'PAUSE') {
        if (playerRef.current) {
          playerRef.current.pause();
          isPlayingRef.current = false;
        }
      } else if (data.type === 'RESUME') {
        if (playerRef.current) {
          playerRef.current.play();
          isPlayingRef.current = true;
        }
      } else if (data.type === 'SEEK') {
        if (playerRef.current && typeof data.position === 'number') {
          playerRef.current.seekTo(data.position).catch(() => {});
        }
      } else if (data.type === 'SET_PLAYBACK_RATE') {
        if (playerRef.current && typeof data.rate === 'number') {
          playerRef.current.playbackRate = data.rate;
        }
      } else if (data.type === 'SET_REPEAT_MODE') {
        repeatModeRef.current = data.repeatMode || 0;
      } else if (data.type === 'APPEND_QUEUE') {
        if (Array.isArray(data.queue) && data.queue.length > 0) {
          queueRef.current = [...queueRef.current, ...data.queue];
        }
      } else if (data.type === 'SET_VOLUME') {
        const targetVol = Math.max(0, Math.min(1, parseFloat(data.volume)));
        setCurrentVolume(targetVol);
        if (playerRef.current) playerRef.current.volume = targetVol;
        VolumeManager.setVolume(targetVol).catch(() => {});
      } else if (data.type === 'REQUEST_INITIAL_VOLUME') {
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
        mixedContentMode="always"
        applicationNameForUserAgent="monoMusicApp/1.0.0"
        onLoadEnd={() => {
          // Send phone volume once page finishes loading
          VolumeManager.getVolume().then((result) => {
            const vol = typeof result === 'number' ? result : (result && typeof result.volume === 'number' ? result.volume : 0.8);
            if (webViewRef.current) {
              webViewRef.current.postMessage(JSON.stringify({ type: 'VOLUME_CHANGED', volume: vol }));
            }
          }).catch(() => {});

          // If a track is already playing natively, immediately sync with WebView
          if (currentTrackRef.current && webViewRef.current) {
            webViewRef.current.postMessage(JSON.stringify({
              type: 'SYNC_CURRENT_TRACK',
              track: currentTrackRef.current,
              isPlaying: isPlayingRef.current,
            }));
          }
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
