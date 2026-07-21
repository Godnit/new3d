package com.mastermedia.quranoffline;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.net.Uri;

public class PrayerAlarmReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "prayer_times_v46";
    private static final long DAY_MS = 24L * 60L * 60L * 1000L;

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!PrayerScheduler.isEnabled(context)) return;
        String name = intent.getStringExtra("name");
        String key = intent.getStringExtra("key");
        int requestCode = intent.getIntExtra("requestCode", 0);
        long timestamp = intent.getLongExtra("timestamp", System.currentTimeMillis());
        if (name == null || name.trim().isEmpty()) name = "الصلاة";
        if (key == null) key = "prayer";

        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        Uri sound = Uri.parse("android.resource://" + context.getPackageName() + "/" + R.raw.adhan_short);
        AudioAttributes audio = new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build();
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "مواقيت الصلاة", NotificationManager.IMPORTANCE_HIGH);
        channel.setDescription("تنبيه عند دخول وقت الصلاة");
        channel.enableVibration(true);
        channel.setSound(sound, audio);
        manager.createNotificationChannel(channel);

        Intent open = new Intent(context, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent content = PendingIntent.getActivity(context, 8100 + requestCode, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification notification = new Notification.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle("حان وقت صلاة " + name)
                .setContentText("حي على الصلاة")
                .setContentIntent(content)
                .setAutoCancel(true)
                .setCategory(Notification.CATEGORY_ALARM)
                .setPriority(Notification.PRIORITY_HIGH)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .build();
        manager.notify(6100 + requestCode, notification);
        PrayerScheduler.scheduleSingle(context, key, name, timestamp + DAY_MS, requestCode);
    }
}
