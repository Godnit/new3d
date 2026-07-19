package com.mastermedia.quranoffline;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;

import org.json.JSONArray;
import org.json.JSONObject;

public final class PrayerScheduler {
    private static final String PREFS = "prayer_alerts";
    private static final String KEY_JSON = "schedule";
    private static final String KEY_ENABLED = "enabled";
    private static final long DAY_MS = 24L * 60L * 60L * 1000L;

    private PrayerScheduler() {}

    public static void setEnabled(Context context, boolean enabled) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean(KEY_ENABLED, enabled).apply();
        if (!enabled) cancelAll(context); else reschedule(context);
    }

    public static boolean isEnabled(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(KEY_ENABLED, false);
    }

    public static void schedule(Context context, String json) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(KEY_JSON, json).apply();
        if (!isEnabled(context)) return;
        cancelAll(context);
        try {
            JSONArray array = new JSONArray(json);
            for (int i = 0; i < array.length(); i++) {
                JSONObject item = array.getJSONObject(i);
                scheduleSingle(context, item.optString("key", "prayer"), item.optString("name", "الصلاة"), item.optLong("timestamp"), i);
            }
        } catch (Exception ignored) {}
    }

    public static void reschedule(Context context) {
        if (!isEnabled(context)) return;
        String json = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY_JSON, "[]");
        schedule(context, json);
    }

    public static void scheduleSingle(Context context, String key, String name, long timestamp, int requestCode) {
        if (!isEnabled(context)) return;
        long now = System.currentTimeMillis();
        while (timestamp <= now + 5000L) timestamp += DAY_MS;
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return;
        Intent intent = new Intent(context, PrayerAlarmReceiver.class)
                .setAction("com.mastermedia.quranoffline.PRAYER_" + key)
                .setData(Uri.parse("rafiq://prayer/" + key + "/" + requestCode))
                .putExtra("key", key)
                .putExtra("name", name)
                .putExtra("timestamp", timestamp)
                .putExtra("requestCode", requestCode);
        PendingIntent pending = PendingIntent.getBroadcast(context, 7200 + requestCode, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !manager.canScheduleExactAlarms()) {
                manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, timestamp, pending);
            } else {
                manager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, timestamp, pending);
            }
        } catch (SecurityException denied) {
            manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, timestamp, pending);
        }
    }

    public static void cancelAll(Context context) {
        AlarmManager manager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (manager == null) return;
        String[] keys = {"fajr", "dhuhr", "asr", "maghrib", "isha"};
        for (int i = 0; i < keys.length; i++) {
            Intent intent = new Intent(context, PrayerAlarmReceiver.class)
                    .setAction("com.mastermedia.quranoffline.PRAYER_" + keys[i])
                    .setData(Uri.parse("rafiq://prayer/" + keys[i] + "/" + i));
            PendingIntent pending = PendingIntent.getBroadcast(context, 7200 + i, intent, PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
            if (pending != null) manager.cancel(pending);
        }
    }
}
