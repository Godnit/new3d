package com.mastermedia.quranoffline;

import android.Manifest;
import android.app.Activity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.AssetManager;
import android.hardware.GeomagneticField;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.location.Location;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.Surface;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.io.IOException;
import java.io.InputStream;
import java.net.URLConnection;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class MainActivityV410 extends Activity implements SensorEventListener {
    private static final int LOCATION_REQUEST = 1001;
    private static final int NOTIFICATION_REQUEST = 1002;
    private static final String APP_HOST = "app.local";
    private static final long COMPASS_DISPATCH_INTERVAL_MS = 75L;
    private static final String LOCATION_PREFS = "qibla_location_v410";

    private WebView webView;
    private SensorManager sensorManager;
    private Sensor rotationVector;
    private Sensor accelerometer;
    private Sensor magnetometer;
    private final float[] gravity = new float[3];
    private final float[] geomagnetic = new float[3];
    private boolean hasGravity;
    private boolean hasGeomagnetic;
    private int compassAccuracy = SensorManager.SENSOR_STATUS_UNRELIABLE;
    private long lastCompassDispatch;
    private float filteredHeading = Float.NaN;
    private float magneticDeclination;
    private boolean audioReceiverRegistered;

    private final BroadcastReceiver audioStateReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (webView == null) return;
            boolean active = intent.getBooleanExtra("active", false);
            boolean playing = intent.getBooleanExtra("playing", false);
            boolean buffering = intent.getBooleanExtra("buffering", false);
            int surah = intent.getIntExtra("surah", 1);
            int position = intent.getIntExtra("position", 0);
            int duration = intent.getIntExtra("duration", 0);
            String name = intent.getStringExtra("name");
            String error = intent.getStringExtra("error");
            if (name == null) name = "الفاتحة";
            if (error == null) error = "";
            final String script = "window.onNativeAudioState&&window.onNativeAudioState(" +
                    playing + "," + surah + "," + JSONObject.quote(name) + "," + buffering + "," +
                    position + "," + duration + "," + active + "," + JSONObject.quote(error) + ")";
            webView.post(() -> webView.evaluateJavascript(script, null));
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);

        webView.addJavascriptInterface(new NativeBridge(), "AndroidBridge");
        webView.setWebViewClient(new LocalAssetClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(
                    String origin,
                    GeolocationPermissions.Callback callback
            ) {
                boolean granted = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                        == PackageManager.PERMISSION_GRANTED;
                callback.invoke(origin, granted, false);
            }
        });

        sensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
        if (sensorManager != null) {
            rotationVector = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);
            accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
            magnetometer = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
        }

        loadSavedCompassLocation();
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
            }, LOCATION_REQUEST);
        } else {
            updateFromLastKnownLocation();
        }

        IntentFilter audioFilter = new IntentFilter(AudioServiceV410.BROADCAST_STATE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            registerReceiver(audioStateReceiver, audioFilter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            registerReceiver(audioStateReceiver, audioFilter);
        }
        audioReceiverRegistered = true;
        webView.loadUrl("https://" + APP_HOST + "/index.html");
    }

    public final class NativeBridge {
        @JavascriptInterface
        public void playSurah(int number, String name) {
            Intent intent = new Intent(MainActivityV410.this, AudioServiceV410.class)
                    .setAction(AudioServiceV410.ACTION_PLAY_SURAH)
                    .putExtra(AudioServiceV410.EXTRA_SURAH, number)
                    .putExtra(AudioServiceV410.EXTRA_NAME, name == null ? "" : name);
            startAudioService(intent, true);
        }

        @JavascriptInterface
        public void audioAction(String action) {
            String nativeAction;
            boolean foreground = false;
            if ("toggle".equals(action)) {
                nativeAction = AudioServiceV410.ACTION_TOGGLE;
                foreground = true;
            } else if ("next".equals(action)) {
                nativeAction = AudioServiceV410.ACTION_NEXT;
                foreground = true;
            } else if ("previous".equals(action)) {
                nativeAction = AudioServiceV410.ACTION_PREVIOUS;
                foreground = true;
            } else if ("stop".equals(action)) {
                nativeAction = AudioServiceV410.ACTION_STOP;
            } else {
                nativeAction = AudioServiceV410.ACTION_QUERY;
            }
            startAudioService(new Intent(MainActivityV410.this, AudioServiceV410.class)
                    .setAction(nativeAction), foreground);
        }

        @JavascriptInterface
        public void requestNotificationPermission() {
            runOnUiThread(() -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                        checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                                != PackageManager.PERMISSION_GRANTED) {
                    requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},
                            NOTIFICATION_REQUEST);
                }
            });
        }

        @JavascriptInterface
        public void setPrayerNotificationsEnabled(boolean enabled) {
            PrayerScheduler.setEnabled(getApplicationContext(), enabled);
        }

        @JavascriptInterface
        public void schedulePrayerNotifications(String json) {
            PrayerScheduler.schedule(getApplicationContext(), json == null ? "[]" : json);
        }

        @JavascriptInterface
        public void testPrayerNotification(long delayMillis) {
            PrayerScheduler.scheduleTest(getApplicationContext(), delayMillis);
        }

        @JavascriptInterface
        public void updateCompassLocation(double latitude, double longitude, double altitude) {
            if (!Double.isFinite(latitude) || !Double.isFinite(longitude) ||
                    latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return;
            updateDeclination((float) latitude, (float) longitude, (float) altitude, true);
        }
    }

    private void startAudioService(Intent intent, boolean needsForeground) {
        try {
            if (needsForeground && Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(intent);
            } else {
                startService(intent);
            }
        } catch (RuntimeException ignored) {}
    }

    private void loadSavedCompassLocation() {
        SharedPreferences prefs = getSharedPreferences(LOCATION_PREFS, MODE_PRIVATE);
        float lat = prefs.getFloat("lat", 15.3694f);
        float lon = prefs.getFloat("lon", 44.1910f);
        float altitude = prefs.getFloat("altitude", 0f);
        updateDeclination(lat, lon, altitude, false);
    }

    private void updateDeclination(float latitude, float longitude, float altitude, boolean save) {
        try {
            GeomagneticField field = new GeomagneticField(
                    latitude, longitude, altitude, System.currentTimeMillis());
            magneticDeclination = field.getDeclination();
            if (save) {
                getSharedPreferences(LOCATION_PREFS, MODE_PRIVATE).edit()
                        .putFloat("lat", latitude)
                        .putFloat("lon", longitude)
                        .putFloat("altitude", altitude)
                        .apply();
            }
        } catch (RuntimeException ignored) {}
    }

    private void updateFromLastKnownLocation() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED &&
                checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                        != PackageManager.PERMISSION_GRANTED) return;
        try {
            LocationManager manager = (LocationManager) getSystemService(LOCATION_SERVICE);
            if (manager == null) return;
            Location best = null;
            List<String> providers = manager.getProviders(true);
            for (String provider : providers) {
                Location location;
                try { location = manager.getLastKnownLocation(provider); }
                catch (SecurityException denied) { continue; }
                if (location == null) continue;
                if (best == null || location.getTime() > best.getTime() ||
                        location.getAccuracy() < best.getAccuracy()) best = location;
            }
            if (best != null) {
                updateDeclination((float) best.getLatitude(), (float) best.getLongitude(),
                        (float) best.getAltitude(), true);
            }
        } catch (RuntimeException ignored) {}
    }

    @Override
    protected void onResume() {
        super.onResume();
        filteredHeading = Float.NaN;
        updateFromLastKnownLocation();
        if (sensorManager != null) {
            if (rotationVector != null) {
                sensorManager.registerListener(this, rotationVector, SensorManager.SENSOR_DELAY_UI);
            } else {
                if (accelerometer != null) sensorManager.registerListener(
                        this, accelerometer, SensorManager.SENSOR_DELAY_UI);
                if (magnetometer != null) sensorManager.registerListener(
                        this, magnetometer, SensorManager.SENSOR_DELAY_UI);
            }
        }
        startAudioService(new Intent(this, AudioServiceV410.class)
                .setAction(AudioServiceV410.ACTION_QUERY), false);
    }

    @Override
    protected void onPause() {
        if (sensorManager != null) sensorManager.unregisterListener(this);
        super.onPause();
    }

    private static void lowPass(float[] source, float[] target) {
        final float alpha = 0.16f;
        for (int i = 0; i < 3; i++) target[i] += alpha * (source[i] - target[i]);
    }

    private float smoothHeading(float heading) {
        if (Float.isNaN(filteredHeading)) {
            filteredHeading = heading;
            return heading;
        }
        float delta = ((heading - filteredHeading + 540f) % 360f) - 180f;
        delta = Math.max(-42f, Math.min(42f, delta));
        filteredHeading = (filteredHeading + delta * 0.32f + 360f) % 360f;
        return filteredHeading;
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (webView == null) return;
        float[] rotationMatrix = new float[9];
        if (event.sensor.getType() == Sensor.TYPE_ROTATION_VECTOR) {
            SensorManager.getRotationMatrixFromVector(rotationMatrix, event.values);
            compassAccuracy = event.accuracy;
        } else {
            if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
                lowPass(event.values, gravity);
                hasGravity = true;
            } else if (event.sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD) {
                lowPass(event.values, geomagnetic);
                hasGeomagnetic = true;
                compassAccuracy = event.accuracy;
            }
            if (!hasGravity || !hasGeomagnetic ||
                    !SensorManager.getRotationMatrix(rotationMatrix, null, gravity, geomagnetic)) return;
        }
        dispatchHeading(rotationMatrix);
    }

    private void dispatchHeading(float[] rotationMatrix) {
        float[] remapped = new float[9];
        float[] orientation = new float[3];
        int axisX = SensorManager.AXIS_X;
        int axisY = SensorManager.AXIS_Y;
        int displayRotation = getWindowManager().getDefaultDisplay().getRotation();
        if (displayRotation == Surface.ROTATION_90) {
            axisX = SensorManager.AXIS_Y;
            axisY = SensorManager.AXIS_MINUS_X;
        } else if (displayRotation == Surface.ROTATION_180) {
            axisX = SensorManager.AXIS_MINUS_X;
            axisY = SensorManager.AXIS_MINUS_Y;
        } else if (displayRotation == Surface.ROTATION_270) {
            axisX = SensorManager.AXIS_MINUS_Y;
            axisY = SensorManager.AXIS_X;
        }
        if (!SensorManager.remapCoordinateSystem(rotationMatrix, axisX, axisY, remapped)) return;
        SensorManager.getOrientation(remapped, orientation);
        float magneticHeading = (float) Math.toDegrees(orientation[0]);
        float trueHeading = (magneticHeading + magneticDeclination + 360f) % 360f;
        float heading = smoothHeading(trueHeading);
        long now = SystemClock.elapsedRealtime();
        if (now - lastCompassDispatch < COMPASS_DISPATCH_INTERVAL_MS) return;
        lastCompassDispatch = now;
        final float finalHeading = heading;
        final int finalAccuracy = compassAccuracy;
        webView.post(() -> webView.evaluateJavascript(
                "window.onNativeHeading&&window.onNativeHeading(" +
                        String.format(Locale.US, "%.2f", finalHeading) + "," + finalAccuracy + ")", null));
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
        if (sensor != null && (sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD ||
                sensor.getType() == Sensor.TYPE_ROTATION_VECTOR)) compassAccuracy = accuracy;
    }

    private final class LocalAssetClient extends WebViewClient {
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            return loadLocalAsset(request.getUrl());
        }

        @Override
        @SuppressWarnings("deprecation")
        public WebResourceResponse shouldInterceptRequest(WebView view, String url) {
            return loadLocalAsset(Uri.parse(url));
        }

        private WebResourceResponse loadLocalAsset(Uri uri) {
            if (!"https".equalsIgnoreCase(uri.getScheme()) ||
                    !APP_HOST.equalsIgnoreCase(uri.getHost())) return null;
            String path = uri.getPath();
            if (path == null || path.isEmpty() || "/".equals(path)) path = "/index.html";
            path = Uri.decode(path.substring(1));
            if (path.contains("..") || path.startsWith("/")) return notFound();
            try {
                InputStream stream = getAssets().open(path, AssetManager.ACCESS_STREAMING);
                WebResourceResponse response = new WebResourceResponse(mimeType(path), "UTF-8", stream);
                Map<String, String> headers = new HashMap<>();
                headers.put("Cache-Control", "public, max-age=31536000, immutable");
                headers.put("Access-Control-Allow-Origin", "https://" + APP_HOST);
                response.setResponseHeaders(headers);
                return response;
            } catch (IOException ignored) {
                return notFound();
            }
        }

        private WebResourceResponse notFound() {
            return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found", null,
                    new java.io.ByteArrayInputStream(new byte[0]));
        }

        private String mimeType(String path) {
            String lower = path.toLowerCase(Locale.ROOT);
            if (lower.endsWith(".html")) return "text/html";
            if (lower.endsWith(".css")) return "text/css";
            if (lower.endsWith(".js")) return "application/javascript";
            if (lower.endsWith(".json")) return "application/json";
            if (lower.endsWith(".woff2")) return "font/woff2";
            if (lower.endsWith(".ttf")) return "font/ttf";
            if (lower.endsWith(".svg")) return "image/svg+xml";
            if (lower.endsWith(".png")) return "image/png";
            if (lower.endsWith(".webp")) return "image/webp";
            if (lower.endsWith(".ogg") || lower.endsWith(".oga") ||
                    lower.endsWith(".opus")) return "audio/ogg";
            String guessed = URLConnection.guessContentTypeFromName(path);
            return guessed != null ? guessed : "application/octet-stream";
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }

    @Override
    protected void onDestroy() {
        if (sensorManager != null) sensorManager.unregisterListener(this);
        if (audioReceiverRegistered) {
            try { unregisterReceiver(audioStateReceiver); } catch (RuntimeException ignored) {}
            audioReceiverRegistered = false;
        }
        if (webView != null) {
            webView.removeJavascriptInterface("AndroidBridge");
            webView.loadUrl("about:blank");
            webView.stopLoading();
            webView.setWebChromeClient(null);
            webView.setWebViewClient(null);
            webView.destroy();
        }
        super.onDestroy();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == LOCATION_REQUEST) {
            updateFromLastKnownLocation();
            if (webView != null) webView.reload();
        }
    }
}
