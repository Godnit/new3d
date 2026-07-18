package com.mastermedia.quranoffline;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.content.res.AssetManager;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.Surface;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.IOException;
import java.io.InputStream;
import java.net.URLConnection;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public class MainActivity extends Activity implements SensorEventListener {
    private static final int LOCATION_REQUEST = 1001;
    private static final String APP_HOST = "app.local";
    private WebView webView;
    private SensorManager sensorManager;
    private Sensor accelerometer;
    private Sensor magnetometer;
    private final float[] gravity = new float[3];
    private final float[] geomagnetic = new float[3];
    private boolean hasGravity;
    private boolean hasGeomagnetic;
    private int compassAccuracy = SensorManager.SENSOR_STATUS_UNRELIABLE;
    private long lastCompassDispatch;
    private float filteredHeading = Float.NaN;

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
            accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
            magnetometer = sensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD);
        }

        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
            }, LOCATION_REQUEST);
        }

        webView.loadUrl("https://" + APP_HOST + "/index.html");
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (sensorManager != null) {
            if (accelerometer != null) {
                sensorManager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_GAME);
            }
            if (magnetometer != null) {
                sensorManager.registerListener(this, magnetometer, SensorManager.SENSOR_DELAY_GAME);
            }
        }
    }

    @Override
    protected void onPause() {
        if (sensorManager != null) {
            sensorManager.unregisterListener(this);
        }
        super.onPause();
    }

    private static void lowPass(float[] source, float[] target) {
        final float alpha = 0.18f;
        for (int i = 0; i < 3; i++) {
            target[i] += alpha * (source[i] - target[i]);
        }
    }

    private float smoothHeading(float heading) {
        if (Float.isNaN(filteredHeading)) {
            filteredHeading = heading;
            return heading;
        }
        float delta = ((heading - filteredHeading + 540f) % 360f) - 180f;
        filteredHeading = (filteredHeading + delta * 0.16f + 360f) % 360f;
        return filteredHeading;
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            lowPass(event.values, gravity);
            hasGravity = true;
        } else if (event.sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD) {
            lowPass(event.values, geomagnetic);
            hasGeomagnetic = true;
            compassAccuracy = event.accuracy;
        }
        if (!hasGravity || !hasGeomagnetic || webView == null) {
            return;
        }

        float[] rotation = new float[9];
        float[] remapped = new float[9];
        float[] orientation = new float[3];
        if (!SensorManager.getRotationMatrix(rotation, null, gravity, geomagnetic)) {
            return;
        }

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
        if (!SensorManager.remapCoordinateSystem(rotation, axisX, axisY, remapped)) {
            return;
        }
        SensorManager.getOrientation(remapped, orientation);
        float heading = (float) Math.toDegrees(orientation[0]);
        heading = (heading + 360f) % 360f;
        heading = smoothHeading(heading);

        long now = SystemClock.elapsedRealtime();
        if (now - lastCompassDispatch < 70L) {
            return;
        }
        lastCompassDispatch = now;
        final float finalHeading = heading;
        final int finalAccuracy = compassAccuracy;
        webView.post(() -> webView.evaluateJavascript(
                "window.onNativeHeading&&window.onNativeHeading(" +
                        String.format(Locale.US, "%.2f", finalHeading) + "," + finalAccuracy + ")",
                null
        ));
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {
        if (sensor != null && sensor.getType() == Sensor.TYPE_MAGNETIC_FIELD) {
            compassAccuracy = accuracy;
        }
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
            if (!"https".equalsIgnoreCase(uri.getScheme()) || !APP_HOST.equalsIgnoreCase(uri.getHost())) {
                return null;
            }

            String path = uri.getPath();
            if (path == null || path.isEmpty() || "/".equals(path)) {
                path = "/index.html";
            }
            path = Uri.decode(path.substring(1));
            if (path.contains("..") || path.startsWith("/")) {
                return notFound();
            }

            try {
                InputStream stream = getAssets().open(path, AssetManager.ACCESS_STREAMING);
                String mime = mimeType(path);
                WebResourceResponse response = new WebResourceResponse(mime, "UTF-8", stream);
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
            String guessed = URLConnection.guessContentTypeFromName(path);
            return guessed != null ? guessed : "application/octet-stream";
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (sensorManager != null) {
            sensorManager.unregisterListener(this);
        }
        if (webView != null) {
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
        if (requestCode == LOCATION_REQUEST && webView != null) {
            webView.reload();
        }
    }
}
