#!/usr/bin/env python3
from pathlib import Path


def replace_exact(path: Path, old: str, new: str, expected_min: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count < expected_min:
        raise RuntimeError(f"Expected at least {expected_min} occurrence(s) in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"patched {path}: {count} occurrence(s)")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    java = root / "app/src/main/java/com/mastermedia/quranoffline"
    assets = root / "app/src/main/assets"
    audio = java / "AudioServiceV410.java"
    activity = java / "MainActivityV410.java"
    reader = assets / "app-v11.js"

    # Reader/audio source patches retained from v4.14-v4.15.
    replace_exact(audio, "ياسر الدوسري", "عادل ريان", expected_min=3)
    replace_exact(audio, "import java.io.IOException;\n", "import java.io.File;\nimport java.io.IOException;\n")

    old_source = '''        try (AssetFileDescriptor descriptor = getAssets().openFd(
                String.format(Locale.US, "quran-audio/%03d.ogg", currentSurah))) {
            created.setDataSource(descriptor.getFileDescriptor(), descriptor.getStartOffset(), descriptor.getLength());
            ensureForeground();
            created.prepareAsync();
            updatePlaybackState();
            broadcastState();
        } catch (IOException | RuntimeException error) {
            handlePlayerError("تعذر فتح تلاوة السورة داخل التطبيق.");
        }'''
    new_source = '''        try {
            File downloaded = AudioDownloadServiceV414.audioFile(this, currentSurah);
            if (downloaded.isFile() && downloaded.length() > 10_000L) {
                created.setDataSource(downloaded.getAbsolutePath());
            } else {
                try (AssetFileDescriptor descriptor = getAssets().openFd(
                        String.format(Locale.US, "quran-audio/%03d.ogg", currentSurah))) {
                    created.setDataSource(descriptor.getFileDescriptor(), descriptor.getStartOffset(), descriptor.getLength());
                }
            }
            ensureForeground();
            created.prepareAsync();
            updatePlaybackState();
            broadcastState();
        } catch (IOException | RuntimeException error) {
            handlePlayerError("هذه السورة غير محملة. افتح قائمة الاستماع واضغط تحميل.");
        }'''
    replace_exact(audio, old_source, new_source)

    # Native seek command used by the draggable timeline.
    replace_exact(audio,
                  '    public static final String ACTION_QUERY = "com.mastermedia.quranoffline.QUERY_AUDIO_V410";\n',
                  '    public static final String ACTION_QUERY = "com.mastermedia.quranoffline.QUERY_AUDIO_V410";\n'
                  '    public static final String ACTION_SEEK = "com.mastermedia.quranoffline.SEEK_AUDIO_V416";\n')
    replace_exact(audio,
                  '    public static final String EXTRA_NAME = "name";\n',
                  '    public static final String EXTRA_NAME = "name";\n'
                  '    public static final String EXTRA_POSITION = "position";\n')
    replace_exact(audio,
                  '''        } else if (ACTION_STOP.equals(action)) {
            stopSelfSafely("");
        } else if (ACTION_QUERY.equals(action)) {''',
                  '''        } else if (ACTION_STOP.equals(action)) {
            stopSelfSafely("");
        } else if (ACTION_SEEK.equals(action)) {
            if (active && prepared && player != null) {
                try {
                    int requested = intent.getIntExtra(EXTRA_POSITION, 0);
                    int safe = Math.max(0, Math.min(duration(), requested));
                    player.seekTo(safe);
                    updatePlaybackState();
                    updateNotification();
                    broadcastState();
                } catch (RuntimeException ignored) {}
            }
        } else if (ACTION_QUERY.equals(action)) {''')

    # Download receiver and bridge.
    replace_exact(activity,
                  "    private boolean audioReceiverRegistered;\n",
                  "    private boolean audioReceiverRegistered;\n    private boolean audioDownloadReceiverRegistered;\n")

    receiver_anchor = '''    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {'''
    download_receiver = '''    };

    private final BroadcastReceiver audioDownloadReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (webView == null || intent == null) return;
            int surah = intent.getIntExtra("surah", 0);
            String status = intent.getStringExtra("status");
            int progress = intent.getIntExtra("progress", 0);
            long bytes = intent.getLongExtra("bytes", 0L);
            long total = intent.getLongExtra("total", 0L);
            String error = intent.getStringExtra("error");
            if (status == null) status = "";
            if (error == null) error = "";
            final String script = "window.onNativeAudioDownloadState&&window.onNativeAudioDownloadState(" +
                    surah + "," + JSONObject.quote(status) + "," + progress + "," + bytes + "," + total + "," +
                    JSONObject.quote(error) + ")";
            webView.post(() -> webView.evaluateJavascript(script, null));
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {'''
    replace_exact(activity, receiver_anchor, download_receiver)

    replace_exact(activity,
                  '''        audioReceiverRegistered = true;
        webView.loadUrl("https://" + APP_HOST + "/index.html");''',
                  '''        audioReceiverRegistered = true;
        IntentFilter downloadFilter = new IntentFilter(AudioDownloadServiceV414.BROADCAST_DOWNLOAD);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(audioDownloadReceiver, downloadFilter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(audioDownloadReceiver, downloadFilter);
        }
        audioDownloadReceiverRegistered = true;
        webView.loadUrl("https://" + APP_HOST + "/index.html");''')

    bridge_anchor = '''        @JavascriptInterface
        public void requestNotificationPermission() {'''
    bridge_methods = '''        @JavascriptInterface
        public String getAudioAvailabilityJson() {
            return AudioDownloadServiceV414.availabilityJson(getApplicationContext());
        }

        @JavascriptInterface
        public void downloadSurahAudio(int number) {
            if (number < 1 || number > 114) return;
            Intent intent = new Intent(MainActivityV410.this, AudioDownloadServiceV414.class)
                    .setAction(AudioDownloadServiceV414.ACTION_DOWNLOAD)
                    .putExtra(AudioDownloadServiceV414.EXTRA_SURAH, number);
            runOnUiThread(() -> {
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(intent);
                    else startService(intent);
                } catch (RuntimeException ignored) {}
            });
        }

        @JavascriptInterface
        public void seekAudio(int positionMillis) {
            int safe = Math.max(0, positionMillis);
            Intent intent = new Intent(MainActivityV410.this, AudioServiceV410.class)
                    .setAction(AudioServiceV410.ACTION_SEEK)
                    .putExtra(AudioServiceV410.EXTRA_POSITION, safe);
            startAudioService(intent, false);
        }

        @JavascriptInterface
        public void refreshCompassLocation() {
            runOnUiThread(() -> {
                updateFromLastKnownLocation();
                requestFreshCompassLocation();
            });
        }

        @JavascriptInterface
        public void requestNotificationPermission() {'''
    replace_exact(activity, bridge_anchor, bridge_methods)

    replace_exact(activity,
                  '''        if (audioReceiverRegistered) {
            try { unregisterReceiver(audioStateReceiver); } catch (RuntimeException ignored) {}
            audioReceiverRegistered = false;
        }
        if (webView != null) {''',
                  '''        if (audioReceiverRegistered) {
            try { unregisterReceiver(audioStateReceiver); } catch (RuntimeException ignored) {}
            audioReceiverRegistered = false;
        }
        if (audioDownloadReceiverRegistered) {
            try { unregisterReceiver(audioDownloadReceiver); } catch (RuntimeException ignored) {}
            audioDownloadReceiverRegistered = false;
        }
        if (webView != null) {''')

    # Fresh location is used for both geomagnetic declination and the JS Qibla
    # bearing. This avoids a stale saved city being combined with a current sensor.
    replace_exact(activity,
                  'import android.location.Location;\nimport android.location.LocationManager;\n',
                  'import android.location.Location;\nimport android.location.LocationListener;\nimport android.location.LocationManager;\n')
    replace_exact(activity,
                  'import android.os.Bundle;\nimport android.os.SystemClock;\n',
                  'import android.os.Bundle;\nimport android.os.Looper;\nimport android.os.SystemClock;\n')
    replace_exact(activity,
                  '''        } else {
            updateFromLastKnownLocation();
        }

        IntentFilter audioFilter''',
                  '''        } else {
            updateFromLastKnownLocation();
            requestFreshCompassLocation();
        }

        IntentFilter audioFilter''')
    replace_exact(activity,
                  '''    @Override
    protected void onResume() {
        super.onResume();
        filteredHeading = Float.NaN;
        updateFromLastKnownLocation();''',
                  '''    @Override
    protected void onResume() {
        super.onResume();
        filteredHeading = Float.NaN;
        updateFromLastKnownLocation();
        requestFreshCompassLocation();''')

    method_anchor = '''    @Override
    protected void onResume() {'''
    fresh_method = '''    private void deliverFreshCompassLocation(Location location) {
        if (location == null) return;
        updateDeclination((float) location.getLatitude(), (float) location.getLongitude(),
                (float) location.getAltitude(), true);
        if (webView != null) {
            final double latitude = location.getLatitude();
            final double longitude = location.getLongitude();
            final double altitude = location.getAltitude();
            final float accuracy = location.hasAccuracy() ? location.getAccuracy() : -1f;
            webView.post(() -> webView.evaluateJavascript(
                    "window.onNativeCompassLocation&&window.onNativeCompassLocation(" +
                            String.format(Locale.US, "%.7f", latitude) + "," +
                            String.format(Locale.US, "%.7f", longitude) + "," +
                            String.format(Locale.US, "%.2f", altitude) + "," +
                            String.format(Locale.US, "%.1f", accuracy) + ")", null));
        }
    }

    private void requestFreshCompassLocation() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED &&
                checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                        != PackageManager.PERMISSION_GRANTED) return;
        try {
            LocationManager manager = (LocationManager) getSystemService(LOCATION_SERVICE);
            if (manager == null) return;
            String provider = null;
            if (manager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                provider = LocationManager.GPS_PROVIDER;
            } else if (manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {
                provider = LocationManager.NETWORK_PROVIDER;
            }
            if (provider == null) return;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                manager.getCurrentLocation(provider, null, getMainExecutor(), this::deliverFreshCompassLocation);
            } else {
                manager.requestSingleUpdate(provider, new LocationListener() {
                    @Override public void onLocationChanged(Location location) {
                        deliverFreshCompassLocation(location);
                    }
                    @Override public void onStatusChanged(String provider, int status, Bundle extras) {}
                    @Override public void onProviderEnabled(String provider) {}
                    @Override public void onProviderDisabled(String provider) {}
                }, Looper.getMainLooper());
            }
        } catch (RuntimeException ignored) {}
    }

    @Override
    protected void onResume() {'''
    replace_exact(activity, method_anchor, fresh_method)

    replace_exact(activity,
                  '''        if (requestCode == LOCATION_REQUEST) {
            updateFromLastKnownLocation();
            if (webView != null) webView.reload();
        }''',
                  '''        if (requestCode == LOCATION_REQUEST) {
            updateFromLastKnownLocation();
            requestFreshCompassLocation();
            if (webView != null) webView.reload();
        }''')

    old_page_source = '''  function pageSource(page){
    var style=localStorage.getItem('mushafImageStyle')||'blue';
    var directory=style==='gold'?'mushaf-pages-gold':(style==='plain'?'mushaf-pages':'mushaf-pages-blue');
    return directory+'/page'+pad3(page)+'.webp';
  }'''
    new_page_source = '''  function pageSource(page){
    return 'mushaf-pages/page'+pad3(page)+'.webp';
  }'''
    replace_exact(reader, old_page_source, new_page_source)


if __name__ == "__main__":
    main()
