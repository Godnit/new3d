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
    audio = java / "AudioServiceV410.java"
    activity = java / "MainActivityV410.java"

    # Keep the stable service and preferences, but update all visible reciter labels.
    replace_exact(audio, "ياسر الدوسري", "عادل ريان", expected_min=3)

    # Faster delivery with moderate native smoothing. JavaScript performs only the final visual easing.
    replace_exact(activity,
                  "private static final long COMPASS_DISPATCH_INTERVAL_MS = 75L;",
                  "private static final long COMPASS_DISPATCH_INTERVAL_MS = 35L;")
    replace_exact(activity, "final float alpha = 0.16f;", "final float alpha = 0.28f;")
    replace_exact(activity,
                  "delta = Math.max(-42f, Math.min(42f, delta));",
                  "delta = Math.max(-120f, Math.min(120f, delta));")
    replace_exact(activity,
                  "filteredHeading = (filteredHeading + delta * 0.32f + 360f) % 360f;",
                  "filteredHeading = (filteredHeading + delta * 0.72f + 360f) % 360f;")
    replace_exact(activity, "SensorManager.SENSOR_DELAY_UI", "SensorManager.SENSOR_DELAY_GAME", expected_min=3)

    # Some phones expose a rotation-vector sensor but do not deliver useful north updates.
    # Register geomagnetic and accelerometer/magnetometer fallbacks at the same time.
    replace_exact(activity,
                  "    private Sensor rotationVector;\n    private Sensor accelerometer;",
                  "    private Sensor rotationVector;\n    private Sensor geomagneticRotationVector;\n    private Sensor accelerometer;")
    replace_exact(activity,
                  "            rotationVector = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);\n            accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);",
                  "            rotationVector = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR);\n            geomagneticRotationVector = sensorManager.getDefaultSensor(Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR);\n            accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);")

    old_resume = '''        updateFromLastKnownLocation();
        if (sensorManager != null) {
            if (rotationVector != null) {
                sensorManager.registerListener(this, rotationVector, SensorManager.SENSOR_DELAY_GAME);
            } else {
                if (accelerometer != null) sensorManager.registerListener(
                        this, accelerometer, SensorManager.SENSOR_DELAY_GAME);
                if (magnetometer != null) sensorManager.registerListener(
                        this, magnetometer, SensorManager.SENSOR_DELAY_GAME);
            }
        }'''
    new_resume = '''        requestFreshLocation();
        registerCompassSensors();'''
    replace_exact(activity, old_resume, new_resume)

    insert_before_pause = '''    private void registerCompassSensors() {
        if (sensorManager == null) return;
        sensorManager.unregisterListener(this);
        if (rotationVector != null) sensorManager.registerListener(
                this, rotationVector, SensorManager.SENSOR_DELAY_GAME);
        if (geomagneticRotationVector != null) sensorManager.registerListener(
                this, geomagneticRotationVector, SensorManager.SENSOR_DELAY_GAME);
        if (accelerometer != null) sensorManager.registerListener(
                this, accelerometer, SensorManager.SENSOR_DELAY_GAME);
        if (magnetometer != null) sensorManager.registerListener(
                this, magnetometer, SensorManager.SENSOR_DELAY_GAME);
    }

    private void requestFreshLocation() {
        updateFromLastKnownLocation();
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) return;
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
            android.os.CancellationSignal cancellation = new android.os.CancellationSignal();
            manager.getCurrentLocation(provider, cancellation, getMainExecutor(), location -> {
                if (location == null) return;
                updateDeclination((float) location.getLatitude(), (float) location.getLongitude(),
                        (float) location.getAltitude(), true);
            });
        } catch (RuntimeException ignored) {}
    }

'''
    replace_exact(activity,
                  "    @Override\n    protected void onPause() {",
                  insert_before_pause + "    @Override\n    protected void onPause() {")

    # Use both rotation-vector variants. Fallback accelerometer/magnetometer events remain active.
    replace_exact(activity,
                  "        if (event.sensor.getType() == Sensor.TYPE_ROTATION_VECTOR) {",
                  "        if (event.sensor.getType() == Sensor.TYPE_ROTATION_VECTOR ||\n                event.sensor.getType() == Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR) {")
    replace_exact(activity,
                  "                sensor.getType() == Sensor.TYPE_ROTATION_VECTOR)) compassAccuracy = accuracy;",
                  "                sensor.getType() == Sensor.TYPE_ROTATION_VECTOR ||\n                sensor.getType() == Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR)) compassAccuracy = accuracy;")

    # Send pitch too, so the UI can warn when the phone is held too upright for a compass reading.
    replace_exact(activity,
                  "        float trueHeading = (magneticHeading + magneticDeclination + 360f) % 360f;\n        float heading = smoothHeading(trueHeading);",
                  "        float trueHeading = (magneticHeading + magneticDeclination + 360f) % 360f;\n        float pitchDegrees = (float) Math.toDegrees(orientation[1]);\n        float heading = smoothHeading(trueHeading);")
    replace_exact(activity,
                  '''                "window.onNativeHeading&&window.onNativeHeading(" +
                        String.format(Locale.US, "%.2f", finalHeading) + "," + finalAccuracy + ")", null));''',
                  '''                "window.onNativeHeading&&window.onNativeHeading(" +
                        String.format(Locale.US, "%.2f", finalHeading) + "," + finalAccuracy + "," +
                        String.format(Locale.US, "%.2f", pitchDegrees) + ")", null));''')

    # Native refresh button: fresh location + restart all sensor fallbacks.
    bridge_anchor = '''        @JavascriptInterface
        public void updateCompassLocation(double latitude, double longitude, double altitude) {
            if (!Double.isFinite(latitude) || !Double.isFinite(longitude) ||
                    latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return;
            updateDeclination((float) latitude, (float) longitude, (float) altitude, true);
        }
'''
    bridge_replacement = bridge_anchor + '''
        @JavascriptInterface
        public void requestCompassRefresh() {
            runOnUiThread(() -> {
                filteredHeading = Float.NaN;
                hasGravity = false;
                hasGeomagnetic = false;
                requestFreshLocation();
                registerCompassSensors();
            });
        }
'''
    replace_exact(activity, bridge_anchor, bridge_replacement)

    # Permission completion must request a fresh fix, not only an arbitrarily old cached location.
    replace_exact(activity,
                  "            updateFromLastKnownLocation();\n            if (webView != null) webView.reload();",
                  "            requestFreshLocation();\n            if (webView != null) webView.reload();")


if __name__ == "__main__":
    main()
