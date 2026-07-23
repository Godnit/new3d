package com.mastermedia.quranoffline;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.os.Environment;
import android.os.IBinder;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

import javax.net.ssl.HttpsURLConnection;

public class AudioDownloadServiceV414 extends Service {
    public static final String ACTION_DOWNLOAD = "com.mastermedia.quranoffline.DOWNLOAD_SURAH_V414";
    public static final String ACTION_DELETE = "com.mastermedia.quranoffline.DELETE_SURAH_V414";
    public static final String BROADCAST_DOWNLOAD = "com.mastermedia.quranoffline.AUDIO_DOWNLOAD_STATE_V414";
    public static final String EXTRA_SURAH = "surah";

    private static final String CHANNEL_ID = "quran_audio_downloads_v414";
    private static final int NOTIFICATION_ID = 4140;
    private static final Set<Integer> BUILT_IN = new HashSet<>();

    static {
        for (int surah = 46; surah <= 114; surah++) BUILT_IN.add(surah);
    }

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Set<Integer> queued = java.util.Collections.synchronizedSet(new HashSet<>());
    private final AtomicInteger pending = new AtomicInteger();

    private static final class IntegrityException extends Exception {
        IntegrityException(String message) { super(message); }
    }

    public static boolean isBuiltIn(int surah) {
        return BUILT_IN.contains(surah);
    }

    public static File audioDirectory(Context context) {
        File base = context.getExternalFilesDir(Environment.DIRECTORY_MUSIC);
        if (base == null) base = context.getFilesDir();
        File directory = new File(base, "adel-rayan-surahs");
        if (!directory.exists()) directory.mkdirs();
        return directory;
    }

    public static File audioFile(Context context, int surah) {
        return new File(audioDirectory(context), String.format(Locale.US, "%03d.ogg", surah));
    }

    public static boolean isDownloaded(Context context, int surah) {
        File file = audioFile(context, surah);
        return file.isFile() && file.length() > 10_000L;
    }

    public static boolean isAvailable(Context context, int surah) {
        return isBuiltIn(surah) || isDownloaded(context, surah);
    }

    public static boolean deleteDownloaded(Context context, int surah) {
        if (isBuiltIn(surah)) return false;
        File file = audioFile(context, surah);
        File part = new File(file.getParentFile(), file.getName() + ".part");
        if (part.exists()) part.delete();
        return !file.exists() || file.delete();
    }

    public static String availabilityJson(Context context) {
        JSONObject root = new JSONObject();
        JSONArray items = new JSONArray();
        try {
            JSONObject manifest = readManifest(context);
            JSONArray sources = manifest.optJSONArray("surahs");
            for (int surah = 1; surah <= 114; surah++) {
                JSONObject source = sources != null && sources.length() >= surah
                        ? sources.optJSONObject(surah - 1) : null;
                JSONObject item = new JSONObject();
                item.put("surah", surah);
                item.put("builtIn", isBuiltIn(surah));
                item.put("downloaded", isDownloaded(context, surah));
                item.put("available", isAvailable(context, surah));
                item.put("bytes", source == null ? 0L : source.optLong("bytes", 0L));
                File downloaded = audioFile(context, surah);
                item.put("storedBytes", downloaded.isFile() ? downloaded.length() : 0L);
                items.put(item);
            }
            root.put("reciter", manifest.optString("reciter", "عادل ريان"));
            root.put("builtInJuzFrom", 26);
            root.put("builtInJuzTo", 30);
            root.put("items", items);
        } catch (Exception error) {
            try {
                root.put("error", "تعذر قراءة قائمة ملفات الصوت");
                root.put("items", items);
            } catch (Exception ignored) {}
        }
        return root.toString();
    }

    private static JSONObject readManifest(Context context) throws Exception {
        try (InputStream input = context.getAssets().open("audio-download-manifest.json")) {
            byte[] buffer = new byte[16_384];
            java.io.ByteArrayOutputStream output = new java.io.ByteArrayOutputStream();
            int count;
            while ((count = input.read(buffer)) >= 0) output.write(buffer, 0, count);
            return new JSONObject(output.toString(StandardCharsets.UTF_8.name()));
        }
    }

    private static JSONObject sourceFor(Context context, int surah) throws Exception {
        JSONArray items = readManifest(context).getJSONArray("surahs");
        JSONObject item = items.getJSONObject(surah - 1);
        if (item.optInt("surah") != surah) throw new IllegalStateException("Audio manifest order mismatch");
        return item;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent == null ? null : intent.getAction();
        int surah = intent == null ? 0 : intent.getIntExtra(EXTRA_SURAH, 0);
        if (surah < 1 || surah > 114) {
            stopSelf(startId);
            return START_NOT_STICKY;
        }
        if (ACTION_DELETE.equals(action)) {
            boolean deleted = deleteDownloaded(this, surah);
            broadcast(surah, deleted ? "deleted" : "error", 0, 0L, 0L,
                    deleted ? "" : "تعذر حذف ملف السورة");
            stopSelf(startId);
            return START_NOT_STICKY;
        }
        if (!ACTION_DOWNLOAD.equals(action)) {
            stopSelf(startId);
            return START_NOT_STICKY;
        }
        if (isAvailable(this, surah)) {
            File file = audioFile(this, surah);
            long size = file.isFile() ? file.length() : 0L;
            broadcast(surah, "completed", 100, size, size, "");
            stopSelf(startId);
            return START_NOT_STICKY;
        }
        if (!queued.add(surah)) {
            broadcast(surah, "queued", 0, 0L, 0L, "");
            return START_NOT_STICKY;
        }
        pending.incrementAndGet();
        startForeground(NOTIFICATION_ID, notification(surah, 0, true, "في انتظار تنزيل السورة"));
        executor.execute(() -> {
            try {
                download(surah);
            } finally {
                queued.remove(surah);
                if (pending.decrementAndGet() <= 0) {
                    stopForeground(STOP_FOREGROUND_REMOVE);
                    stopSelf();
                }
            }
        });
        return START_NOT_STICKY;
    }

    private boolean finishPart(File part, File destination, long expectedBytes, String expectedHash)
            throws Exception {
        if (!part.isFile()) return false;
        if (expectedBytes > 0 && part.length() != expectedBytes) return false;
        if (part.length() <= 10_000L) return false;
        String actualHash = sha256(part);
        if (!expectedHash.isEmpty() && !expectedHash.equalsIgnoreCase(actualHash)) {
            if (!part.delete()) part.deleteOnExit();
            throw new IntegrityException("Downloaded checksum mismatch");
        }
        if (destination.exists() && !destination.delete()) {
            throw new java.io.IOException("Cannot replace old file");
        }
        if (!part.renameTo(destination)) {
            copyFile(part, destination);
            if (!part.delete()) part.deleteOnExit();
        }
        return destination.isFile() && destination.length() > 10_000L;
    }

    private static void copyFile(File source, File destination) throws Exception {
        try (InputStream input = new BufferedInputStream(new FileInputStream(source), 128 * 1024);
             BufferedOutputStream output = new BufferedOutputStream(new FileOutputStream(destination), 128 * 1024)) {
            byte[] buffer = new byte[128 * 1024];
            int count;
            while ((count = input.read(buffer)) >= 0) output.write(buffer, 0, count);
        }
    }

    private void download(int surah) {
        File destination = audioFile(this, surah);
        File part = new File(destination.getParentFile(), destination.getName() + ".part");
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        long expectedBytes = 0L;
        try {
            JSONObject source = sourceFor(this, surah);
            String sourceUrl = source.getString("url");
            expectedBytes = source.optLong("bytes", 0L);
            String expectedHash = source.optString("sha256", "");
            if (!sourceUrl.startsWith("https://")) throw new SecurityException("Only HTTPS audio sources are allowed");

            if (finishPart(part, destination, expectedBytes, expectedHash)) {
                broadcast(surah, "completed", 100, destination.length(), destination.length(), "");
                return;
            }

            broadcast(surah, "downloading", progress(part.length(), expectedBytes), part.length(), expectedBytes, "");
            if (manager != null) manager.notify(NOTIFICATION_ID,
                    notification(surah, progress(part.length(), expectedBytes), expectedBytes <= 0, "جارٍ بدء التنزيل"));

            Exception lastError = null;
            for (int attempt = 1; attempt <= 4; attempt++) {
                HttpsURLConnection connection = null;
                try {
                    long existing = part.isFile() ? part.length() : 0L;
                    if (expectedBytes > 0 && existing > expectedBytes) {
                        part.delete();
                        existing = 0L;
                    }
                    if (finishPart(part, destination, expectedBytes, expectedHash)) {
                        broadcast(surah, "completed", 100, destination.length(), destination.length(), "");
                        return;
                    }

                    String cacheToken = expectedHash.length() >= 16 ? expectedHash.substring(0, 16) : expectedHash;
                    String requestUrl = sourceUrl + (sourceUrl.contains("?") ? "&" : "?") + "integrity=" + cacheToken;
                    connection = (HttpsURLConnection) new java.net.URL(requestUrl).openConnection();
                    connection.setConnectTimeout(25_000);
                    connection.setReadTimeout(90_000);
                    connection.setRequestProperty("User-Agent", "RafiqAlHuda/4.17 Android");
                    connection.setRequestProperty("Accept-Encoding", "identity");
                    connection.setRequestProperty("Cache-Control", "no-cache");
                    connection.setRequestProperty("Pragma", "no-cache");
                    if (existing > 0) connection.setRequestProperty("Range", "bytes=" + existing + "-");
                    connection.setInstanceFollowRedirects(true);

                    int response = connection.getResponseCode();
                    if (response == 416) {
                        if (finishPart(part, destination, expectedBytes, expectedHash)) {
                            broadcast(surah, "completed", 100, destination.length(), destination.length(), "");
                            return;
                        }
                        if (part.exists()) part.delete();
                        throw new java.io.IOException("Server rejected partial range");
                    }
                    boolean append = existing > 0 && response == HttpsURLConnection.HTTP_PARTIAL;
                    if (response == HttpsURLConnection.HTTP_OK && existing > 0) {
                        if (!part.delete()) throw new java.io.IOException("Cannot restart partial download");
                        existing = 0L;
                        append = false;
                    } else if (response != HttpsURLConnection.HTTP_OK && response != HttpsURLConnection.HTTP_PARTIAL) {
                        throw new java.io.IOException("HTTP " + response);
                    }

                    long written = existing;
                    int lastPercent = progress(written, expectedBytes);
                    try (InputStream input = new BufferedInputStream(connection.getInputStream(), 256 * 1024);
                         BufferedOutputStream output = new BufferedOutputStream(
                                 new FileOutputStream(part, append), 256 * 1024)) {
                        byte[] buffer = new byte[256 * 1024];
                        int count;
                        while ((count = input.read(buffer)) >= 0) {
                            output.write(buffer, 0, count);
                            written += count;
                            int percent = progress(written, expectedBytes);
                            if (percent != lastPercent) {
                                lastPercent = percent;
                                broadcast(surah, "downloading", percent, written, expectedBytes, "");
                                if (manager != null && (percent % 4 == 0 || percent >= 98)) {
                                    manager.notify(NOTIFICATION_ID,
                                            notification(surah, percent, expectedBytes <= 0,
                                                    "جارٍ تنزيل سورة رقم " + surah));
                                }
                            }
                        }
                    }

                    if (expectedBytes > 0 && part.length() != expectedBytes) {
                        throw new java.io.IOException("Incomplete download: " + part.length() + " != " + expectedBytes);
                    }
                    if (!finishPart(part, destination, expectedBytes, expectedHash)) {
                        throw new java.io.IOException("Downloaded file is incomplete");
                    }

                    broadcast(surah, "completed", 100, destination.length(), destination.length(), "");
                    if (manager != null) manager.notify(NOTIFICATION_ID,
                            notification(surah, 100, false, "اكتمل تنزيل السورة"));
                    return;
                } catch (IntegrityException integrity) {
                    throw integrity;
                } catch (Exception error) {
                    lastError = error;
                    if (attempt < 4) {
                        long stored = part.isFile() ? part.length() : 0L;
                        broadcast(surah, "downloading", progress(stored, expectedBytes), stored, expectedBytes, "");
                        try { Thread.sleep(1400L * attempt); }
                        catch (InterruptedException interrupted) {
                            Thread.currentThread().interrupt();
                            throw interrupted;
                        }
                    }
                } finally {
                    if (connection != null) connection.disconnect();
                }
            }
            throw lastError != null ? lastError : new java.io.IOException("Download failed");
        } catch (IntegrityException error) {
            broadcast(surah, "error", 0, 0L, expectedBytes,
                    "تعذر التحقق من الملف. اضغط تحميل مرة أخرى لتنزيل نسخة جديدة.");
        } catch (Exception error) {
            long stored = part.isFile() ? part.length() : 0L;
            broadcast(surah, "error", progress(stored, expectedBytes), stored, expectedBytes,
                    "توقف التنزيل مؤقتًا. اضغط متابعة ليكمل من حيث توقف.");
        }
    }

    private static int progress(long bytes, long total) {
        if (total <= 0) return 0;
        return (int) Math.max(0, Math.min(99, bytes * 100L / total));
    }

    private static String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new BufferedInputStream(new FileInputStream(file), 128 * 1024)) {
            byte[] buffer = new byte[128 * 1024];
            int count;
            while ((count = input.read(buffer)) >= 0) digest.update(buffer, 0, count);
        }
        return hex(digest.digest());
    }

    private static String hex(byte[] bytes) {
        StringBuilder builder = new StringBuilder(bytes.length * 2);
        for (byte value : bytes) builder.append(String.format(Locale.US, "%02x", value & 0xff));
        return builder.toString();
    }

    private void broadcast(int surah, String status, int progress, long bytes, long total, String error) {
        Intent intent = new Intent(BROADCAST_DOWNLOAD).setPackage(getPackageName());
        intent.putExtra("surah", surah);
        intent.putExtra("status", status);
        intent.putExtra("progress", progress);
        intent.putExtra("bytes", bytes);
        intent.putExtra("total", total);
        intent.putExtra("error", error == null ? "" : error);
        sendBroadcast(intent);
    }

    private Notification notification(int surah, int progress, boolean indeterminate, String text) {
        Intent open = new Intent(this, MainActivityV410.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pendingIntent = PendingIntent.getActivity(this, 4140, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder builder = new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle("تنزيل تلاوة سورة رقم " + surah)
                .setContentText(text)
                .setContentIntent(pendingIntent)
                .setOnlyAlertOnce(true)
                .setOngoing(progress < 100)
                .setShowWhen(false);
        if (progress < 100) builder.setProgress(100, progress, indeterminate);
        return builder.build();
    }

    private void createChannel() {
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (manager == null) return;
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "تنزيل تلاوات القرآن", NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("تنزيل السور للاستماع إليها دون إنترنت");
        channel.setSound(null, null);
        manager.createNotificationChannel(channel);
    }

    @Override
    public void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
