package com.mastermedia.quranoffline;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.res.AssetFileDescriptor;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;

import java.io.IOException;
import java.util.Locale;

public class AudioServiceV410 extends Service {
    public static final String ACTION_PLAY_SURAH = "com.mastermedia.quranoffline.PLAY_SURAH_V410";
    public static final String ACTION_TOGGLE = "com.mastermedia.quranoffline.TOGGLE_AUDIO_V410";
    public static final String ACTION_NEXT = "com.mastermedia.quranoffline.NEXT_AUDIO_V410";
    public static final String ACTION_PREVIOUS = "com.mastermedia.quranoffline.PREVIOUS_AUDIO_V410";
    public static final String ACTION_STOP = "com.mastermedia.quranoffline.STOP_AUDIO_V410";
    public static final String ACTION_QUERY = "com.mastermedia.quranoffline.QUERY_AUDIO_V410";
    public static final String BROADCAST_STATE = "com.mastermedia.quranoffline.AUDIO_STATE_V410";
    public static final String EXTRA_SURAH = "surah";
    public static final String EXTRA_NAME = "name";

    private static final String CHANNEL_ID = "quran_playback_offline_v410";
    private static final int NOTIFICATION_ID = 4110;

    private static final String[] SURAHS = new String[]{
            "الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف","الأنفال","التوبة","يونس","هود","يوسف","الرعد","إبراهيم","الحجر","النحل","الإسراء","الكهف","مريم","طه","الأنبياء","الحج","المؤمنون","النور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم","لقمان","السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر","فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق","الذاريات","الطور","النجم","القمر","الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة","الصف","الجمعة","المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج","نوح","الجن","المزمل","المدثر","القيامة","الإنسان","المرسلات","النبأ","النازعات","عبس","التكوير","الانفطار","المطففين","الانشقاق","البروج","الطارق","الأعلى","الغاشية","الفجر","البلد","الشمس","الليل","الضحى","الشرح","التين","العلق","القدر","البينة","الزلزلة","العاديات","القارعة","التكاثر","العصر","الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر","المسد","الإخلاص","الفلق","الناس"
    };

    private MediaPlayer player;
    private MediaSession mediaSession;
    private AudioManager audioManager;
    private AudioFocusRequest focusRequest;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private int currentSurah = 1;
    private int playerGeneration = 0;
    private boolean active;
    private boolean prepared;
    private boolean buffering;
    private boolean startedForeground;
    private String lastError = "";

    private final Runnable progressTicker = new Runnable() {
        @Override public void run() {
            if (!active || player == null) return;
            updatePlaybackState();
            updateNotification();
            broadcastState();
            handler.postDelayed(this, 1000L);
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        currentSurah = getSharedPreferences("audio", MODE_PRIVATE).getInt("surah", 1);
        mediaSession = new MediaSession(this, "RafiqAlHudaPlaybackV410");
        mediaSession.setCallback(new MediaSession.Callback() {
            @Override public void onPlay() { resumePlayback(); }
            @Override public void onPause() { pausePlayback(); }
            @Override public void onSkipToNext() { playSurah(currentSurah + 1); }
            @Override public void onSkipToPrevious() { playSurah(currentSurah - 1); }
            @Override public void onStop() { stopSelfSafely(""); }
            @Override public void onSeekTo(long pos) {
                if (!active || !prepared || player == null) return;
                try {
                    int safe = (int) Math.max(0, Math.min(duration(), pos));
                    player.seekTo(safe);
                    updatePlaybackState();
                    broadcastState();
                } catch (RuntimeException ignored) {}
            }
        });
        mediaSession.setActive(false);
        updatePlaybackState();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent != null ? intent.getAction() : null;
        if (ACTION_PLAY_SURAH.equals(action)) {
            playSurah(intent.getIntExtra(EXTRA_SURAH, currentSurah));
        } else if (ACTION_TOGGLE.equals(action)) {
            if (!active || player == null) playSurah(currentSurah);
            else if (isPlayingSafe()) pausePlayback();
            else resumePlayback();
        } else if (ACTION_NEXT.equals(action)) {
            playSurah(currentSurah + 1);
        } else if (ACTION_PREVIOUS.equals(action)) {
            playSurah(currentSurah - 1);
        } else if (ACTION_STOP.equals(action)) {
            stopSelfSafely("");
        } else if (ACTION_QUERY.equals(action)) {
            broadcastState();
            if (active) updateNotification(); else stopSelf(startId);
        }
        return START_NOT_STICKY;
    }

    private void playSurah(int number) {
        currentSurah = Math.max(1, Math.min(114, number));
        getSharedPreferences("audio", MODE_PRIVATE).edit().putInt("surah", currentSurah).apply();
        final int generation = ++playerGeneration;
        releasePlayer();
        active = true;
        prepared = false;
        buffering = true;
        lastError = "";
        requestAudioFocus();

        MediaPlayer created = new MediaPlayer();
        player = created;
        created.setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                .build());
        try { created.setWakeMode(getApplicationContext(), PowerManager.PARTIAL_WAKE_LOCK); }
        catch (RuntimeException ignored) {}

        created.setOnPreparedListener(mp -> {
            if (generation != playerGeneration || mp != player || !active) return;
            prepared = true;
            buffering = false;
            try {
                mp.start();
                startTicker();
                mediaSession.setActive(true);
                updatePlaybackState();
                updateNotification();
                broadcastState();
            } catch (RuntimeException error) {
                handlePlayerError("تعذر بدء التلاوة. جرّب السورة مرة أخرى.");
            }
        });
        created.setOnCompletionListener(mp -> {
            if (generation != playerGeneration || mp != player) return;
            if (currentSurah < 114) playSurah(currentSurah + 1); else stopSelfSafely("");
        });
        created.setOnErrorListener((mp, what, extra) -> {
            if (generation == playerGeneration && mp == player) {
                handlePlayerError("تعذر تشغيل ملف السورة. أُغلق المشغل بأمان.");
            }
            return true;
        });

        try (AssetFileDescriptor descriptor = getAssets().openFd(
                String.format(Locale.US, "quran-audio/%03d.ogg", currentSurah))) {
            created.setDataSource(descriptor.getFileDescriptor(), descriptor.getStartOffset(), descriptor.getLength());
            ensureForeground();
            created.prepareAsync();
            updatePlaybackState();
            broadcastState();
        } catch (IOException | RuntimeException error) {
            handlePlayerError("تعذر فتح تلاوة السورة داخل التطبيق.");
        }
    }

    private void resumePlayback() {
        if (!active || player == null) {
            playSurah(currentSurah);
            return;
        }
        requestAudioFocus();
        if (buffering || !prepared) {
            updatePlaybackState();
            updateNotification();
            broadcastState();
            return;
        }
        try {
            player.start();
            startTicker();
            mediaSession.setActive(true);
        } catch (RuntimeException error) {
            handlePlayerError("تعذر استئناف التلاوة.");
            return;
        }
        updatePlaybackState();
        updateNotification();
        broadcastState();
    }

    private void pausePlayback() {
        if (!active || player == null || !prepared) return;
        try { if (isPlayingSafe()) player.pause(); }
        catch (RuntimeException ignored) {}
        stopTicker();
        updatePlaybackState();
        updateNotification();
        broadcastState();
    }

    private void startTicker() {
        handler.removeCallbacks(progressTicker);
        handler.post(progressTicker);
    }

    private void stopTicker() {
        handler.removeCallbacks(progressTicker);
    }

    private void requestAudioFocus() {
        if (audioManager == null) return;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            if (focusRequest == null) {
                focusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
                        .setAudioAttributes(new AudioAttributes.Builder()
                                .setUsage(AudioAttributes.USAGE_MEDIA)
                                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
                        .setOnAudioFocusChangeListener(change -> {
                            if (change == AudioManager.AUDIOFOCUS_LOSS ||
                                    change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) pausePlayback();
                        }).build();
            }
            audioManager.requestAudioFocus(focusRequest);
        } else {
            audioManager.requestAudioFocus(change -> {
                if (change <= AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) pausePlayback();
            }, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN);
        }
    }

    private void abandonAudioFocus() {
        if (audioManager == null) return;
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && focusRequest != null) {
                audioManager.abandonAudioFocusRequest(focusRequest);
            }
        } catch (RuntimeException ignored) {}
    }

    private boolean isPlayingSafe() {
        try { return active && prepared && player != null && player.isPlaying(); }
        catch (RuntimeException ignored) { return false; }
    }

    private int currentPosition() {
        try { return active && prepared && player != null ? Math.max(0, player.getCurrentPosition()) : 0; }
        catch (RuntimeException ignored) { return 0; }
    }

    private int duration() {
        try { return active && prepared && player != null ? Math.max(0, player.getDuration()) : 0; }
        catch (RuntimeException ignored) { return 0; }
    }

    private void updatePlaybackState() {
        if (mediaSession == null) return;
        boolean playing = isPlayingSafe();
        int state;
        if (!active) state = PlaybackState.STATE_STOPPED;
        else if (buffering) state = PlaybackState.STATE_BUFFERING;
        else state = playing ? PlaybackState.STATE_PLAYING : PlaybackState.STATE_PAUSED;
        long actions = PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PAUSE |
                PlaybackState.ACTION_PLAY_PAUSE | PlaybackState.ACTION_SKIP_TO_NEXT |
                PlaybackState.ACTION_SKIP_TO_PREVIOUS | PlaybackState.ACTION_STOP |
                PlaybackState.ACTION_SEEK_TO;
        try {
            mediaSession.setPlaybackState(new PlaybackState.Builder()
                    .setActions(actions)
                    .setState(state, currentPosition(), playing ? 1f : 0f)
                    .build());
            mediaSession.setMetadata(new android.media.MediaMetadata.Builder()
                    .putString(android.media.MediaMetadata.METADATA_KEY_TITLE, "سورة " + surahName())
                    .putString(android.media.MediaMetadata.METADATA_KEY_ARTIST, "ياسر الدوسري")
                    .putString(android.media.MediaMetadata.METADATA_KEY_ALBUM, "القرآن الكريم — دون إنترنت")
                    .putLong(android.media.MediaMetadata.METADATA_KEY_DURATION, duration())
                    .build());
        } catch (RuntimeException ignored) {}
    }

    private PendingIntent serviceAction(String action, int requestCode) {
        Intent intent = new Intent(this, AudioServiceV410.class).setAction(action);
        return PendingIntent.getService(this, requestCode, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private Notification buildNotification() {
        boolean playing = isPlayingSafe();
        Intent open = new Intent(this, MainActivityV410.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent content = PendingIntent.getActivity(this, 4100, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Action previous = new Notification.Action.Builder(
                android.R.drawable.ic_media_previous, "السابق", serviceAction(ACTION_PREVIOUS, 4101)).build();
        Notification.Action toggle = new Notification.Action.Builder(
                playing ? android.R.drawable.ic_media_pause : android.R.drawable.ic_media_play,
                playing ? "إيقاف مؤقت" : "تشغيل", serviceAction(ACTION_TOGGLE, 4102)).build();
        Notification.Action next = new Notification.Action.Builder(
                android.R.drawable.ic_media_next, "التالي", serviceAction(ACTION_NEXT, 4103)).build();
        Notification.Action stop = new Notification.Action.Builder(
                android.R.drawable.ic_menu_close_clear_cancel, "إغلاق", serviceAction(ACTION_STOP, 4104)).build();
        Notification.Builder builder = new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle("سورة " + surahName())
                .setContentText(buffering ? "جارٍ تجهيز التلاوة — ياسر الدوسري" : "ياسر الدوسري — يعمل دون إنترنت")
                .setContentIntent(content)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setOnlyAlertOnce(true)
                .setOngoing(playing || buffering)
                .setShowWhen(false)
                .addAction(previous).addAction(toggle).addAction(next).addAction(stop)
                .setStyle(new Notification.MediaStyle()
                        .setMediaSession(mediaSession.getSessionToken())
                        .setShowActionsInCompactView(0, 1, 2));
        int total = duration();
        if (total > 0) builder.setProgress(total, currentPosition(), buffering);
        return builder.build();
    }

    private void ensureForeground() {
        if (!active) return;
        Notification notification = buildNotification();
        if (!startedForeground) {
            startForeground(NOTIFICATION_ID, notification);
            startedForeground = true;
        } else {
            NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            if (manager != null) manager.notify(NOTIFICATION_ID, notification);
        }
    }

    private void updateNotification() {
        if (!active) return;
        ensureForeground();
    }

    private void broadcastState() {
        Intent state = new Intent(BROADCAST_STATE).setPackage(getPackageName());
        state.putExtra("active", active);
        state.putExtra("playing", isPlayingSafe());
        state.putExtra("buffering", active && buffering);
        state.putExtra("surah", currentSurah);
        state.putExtra("name", surahName());
        state.putExtra("position", currentPosition());
        state.putExtra("duration", duration());
        state.putExtra("error", lastError == null ? "" : lastError);
        sendBroadcast(state);
    }

    private String surahName() {
        return SURAHS[Math.max(0, Math.min(SURAHS.length - 1, currentSurah - 1))];
    }

    private void createChannel() {
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (manager == null) return;
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "تلاوة القرآن", NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("مشغل القرآن كاملًا بصوت ياسر الدوسري دون إنترنت");
        channel.setSound(null, null);
        manager.createNotificationChannel(channel);
    }

    private void releasePlayer() {
        stopTicker();
        MediaPlayer old = player;
        player = null;
        prepared = false;
        buffering = false;
        if (old != null) {
            try { old.setOnPreparedListener(null); } catch (RuntimeException ignored) {}
            try { old.setOnCompletionListener(null); } catch (RuntimeException ignored) {}
            try { old.setOnErrorListener(null); } catch (RuntimeException ignored) {}
            try { old.stop(); } catch (RuntimeException ignored) {}
            try { old.reset(); } catch (RuntimeException ignored) {}
            try { old.release(); } catch (RuntimeException ignored) {}
        }
    }

    private void handlePlayerError(String message) {
        lastError = message == null ? "تعذر تشغيل التلاوة." : message;
        active = false;
        ++playerGeneration;
        releasePlayer();
        updatePlaybackState();
        broadcastState();
        if (mediaSession != null) mediaSession.setActive(false);
        if (startedForeground) stopForeground(STOP_FOREGROUND_REMOVE);
        startedForeground = false;
        abandonAudioFocus();
        stopSelf();
    }

    private void stopSelfSafely(String error) {
        lastError = error == null ? "" : error;
        active = false;
        ++playerGeneration;
        releasePlayer();
        updatePlaybackState();
        broadcastState();
        if (mediaSession != null) mediaSession.setActive(false);
        if (startedForeground) stopForeground(STOP_FOREGROUND_REMOVE);
        startedForeground = false;
        abandonAudioFocus();
        stopSelf();
    }

    @Override public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        active = false;
        ++playerGeneration;
        releasePlayer();
        abandonAudioFocus();
        if (mediaSession != null) {
            try { mediaSession.release(); } catch (RuntimeException ignored) {}
            mediaSession = null;
        }
        super.onDestroy();
    }
}
