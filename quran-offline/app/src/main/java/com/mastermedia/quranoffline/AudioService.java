package com.mastermedia.quranoffline;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.Build;
import android.os.IBinder;

import java.io.IOException;
import java.util.Locale;

public class AudioService extends Service {
    public static final String ACTION_PLAY_SURAH = "com.mastermedia.quranoffline.PLAY_SURAH";
    public static final String ACTION_TOGGLE = "com.mastermedia.quranoffline.TOGGLE_AUDIO";
    public static final String ACTION_NEXT = "com.mastermedia.quranoffline.NEXT_AUDIO";
    public static final String ACTION_PREVIOUS = "com.mastermedia.quranoffline.PREVIOUS_AUDIO";
    public static final String ACTION_STOP = "com.mastermedia.quranoffline.STOP_AUDIO";
    public static final String ACTION_QUERY = "com.mastermedia.quranoffline.QUERY_AUDIO";
    public static final String BROADCAST_STATE = "com.mastermedia.quranoffline.AUDIO_STATE";
    public static final String EXTRA_SURAH = "surah";
    public static final String EXTRA_NAME = "name";

    private static final String CHANNEL_ID = "quran_playback";
    private static final int NOTIFICATION_ID = 4106;

    private static final String[] SURAHS = new String[]{
            "الفاتحة","البقرة","آل عمران","النساء","المائدة","الأنعام","الأعراف","الأنفال","التوبة","يونس","هود","يوسف","الرعد","إبراهيم","الحجر","النحل","الإسراء","الكهف","مريم","طه","الأنبياء","الحج","المؤمنون","النور","الفرقان","الشعراء","النمل","القصص","العنكبوت","الروم","لقمان","السجدة","الأحزاب","سبأ","فاطر","يس","الصافات","ص","الزمر","غافر","فصلت","الشورى","الزخرف","الدخان","الجاثية","الأحقاف","محمد","الفتح","الحجرات","ق","الذاريات","الطور","النجم","القمر","الرحمن","الواقعة","الحديد","المجادلة","الحشر","الممتحنة","الصف","الجمعة","المنافقون","التغابن","الطلاق","التحريم","الملك","القلم","الحاقة","المعارج","نوح","الجن","المزمل","المدثر","القيامة","الإنسان","المرسلات","النبأ","النازعات","عبس","التكوير","الانفطار","المطففين","الانشقاق","البروج","الطارق","الأعلى","الغاشية","الفجر","البلد","الشمس","الليل","الضحى","الشرح","التين","العلق","القدر","البينة","الزلزلة","العاديات","القارعة","التكاثر","العصر","الهمزة","الفيل","قريش","الماعون","الكوثر","الكافرون","النصر","المسد","الإخلاص","الفلق","الناس"
    };

    private MediaPlayer player;
    private MediaSession mediaSession;
    private AudioManager audioManager;
    private AudioFocusRequest focusRequest;
    private int currentSurah = 1;
    private boolean buffering;
    private boolean startedForeground;

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
        audioManager = (AudioManager) getSystemService(Context.AUDIO_SERVICE);
        currentSurah = getSharedPreferences("audio", MODE_PRIVATE).getInt("surah", 1);
        mediaSession = new MediaSession(this, "RafiqAlHudaPlayback");
        mediaSession.setCallback(new MediaSession.Callback() {
            @Override public void onPlay() { resumePlayback(); }
            @Override public void onPause() { pausePlayback(); }
            @Override public void onSkipToNext() { playSurah(currentSurah + 1); }
            @Override public void onSkipToPrevious() { playSurah(currentSurah - 1); }
            @Override public void onStop() { stopSelfSafely(); }
        });
        mediaSession.setActive(true);
        updatePlaybackState();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent != null ? intent.getAction() : null;
        if (ACTION_PLAY_SURAH.equals(action)) {
            playSurah(intent.getIntExtra(EXTRA_SURAH, currentSurah));
        } else if (ACTION_TOGGLE.equals(action)) {
            if (player != null && player.isPlaying()) pausePlayback(); else resumePlayback();
        } else if (ACTION_NEXT.equals(action)) {
            playSurah(currentSurah + 1);
        } else if (ACTION_PREVIOUS.equals(action)) {
            playSurah(currentSurah - 1);
        } else if (ACTION_STOP.equals(action)) {
            stopSelfSafely();
        } else if (ACTION_QUERY.equals(action)) {
            broadcastState();
            updateNotification();
        }
        return START_NOT_STICKY;
    }

    private void playSurah(int number) {
        currentSurah = Math.max(1, Math.min(114, number));
        getSharedPreferences("audio", MODE_PRIVATE).edit().putInt("surah", currentSurah).apply();
        releasePlayer();
        requestAudioFocus();
        buffering = true;
        player = new MediaPlayer();
        player.setAudioAttributes(new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                .build());
        player.setOnPreparedListener(mp -> {
            buffering = false;
            mp.start();
            updatePlaybackState();
            updateNotification();
            broadcastState();
        });
        player.setOnCompletionListener(mp -> {
            if (currentSurah < 114) playSurah(currentSurah + 1); else stopSelfSafely();
        });
        player.setOnErrorListener((mp, what, extra) -> {
            buffering = false;
            updatePlaybackState();
            updateNotification();
            broadcastState();
            return true;
        });
        try {
            String url = String.format(Locale.US, "https://server11.mp3quran.net/yasser/%03d.mp3", currentSurah);
            player.setDataSource(url);
            player.prepareAsync();
            ensureForeground();
            updatePlaybackState();
            updateNotification();
            broadcastState();
        } catch (IOException error) {
            buffering = false;
            releasePlayer();
            updatePlaybackState();
            broadcastState();
        }
    }

    private void resumePlayback() {
        if (player == null) {
            playSurah(currentSurah);
            return;
        }
        requestAudioFocus();
        if (!buffering) player.start();
        updatePlaybackState();
        updateNotification();
        broadcastState();
    }

    private void pausePlayback() {
        if (player != null && player.isPlaying()) player.pause();
        updatePlaybackState();
        updateNotification();
        broadcastState();
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
                            if (change == AudioManager.AUDIOFOCUS_LOSS || change == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) pausePlayback();
                        }).build();
            }
            audioManager.requestAudioFocus(focusRequest);
        } else {
            audioManager.requestAudioFocus(change -> {
                if (change <= AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) pausePlayback();
            }, AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN);
        }
    }

    private void updatePlaybackState() {
        boolean playing = player != null && player.isPlaying();
        int state = buffering ? PlaybackState.STATE_BUFFERING : (playing ? PlaybackState.STATE_PLAYING : PlaybackState.STATE_PAUSED);
        long actions = PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PAUSE | PlaybackState.ACTION_PLAY_PAUSE |
                PlaybackState.ACTION_SKIP_TO_NEXT | PlaybackState.ACTION_SKIP_TO_PREVIOUS | PlaybackState.ACTION_STOP;
        mediaSession.setPlaybackState(new PlaybackState.Builder().setActions(actions).setState(state, 0, 1f).build());
        mediaSession.setMetadata(new android.media.MediaMetadata.Builder()
                .putString(android.media.MediaMetadata.METADATA_KEY_TITLE, "سورة " + surahName())
                .putString(android.media.MediaMetadata.METADATA_KEY_ARTIST, "ياسر الدوسري")
                .putString(android.media.MediaMetadata.METADATA_KEY_ALBUM, "القرآن الكريم")
                .build());
    }

    private PendingIntent serviceAction(String action, int requestCode) {
        Intent intent = new Intent(this, AudioService.class).setAction(action);
        return PendingIntent.getService(this, requestCode, intent, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private Notification buildNotification() {
        boolean playing = player != null && player.isPlaying();
        Intent open = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent content = PendingIntent.getActivity(this, 4000, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Action previous = new Notification.Action.Builder(android.R.drawable.ic_media_previous, "السابق", serviceAction(ACTION_PREVIOUS, 4001)).build();
        Notification.Action toggle = new Notification.Action.Builder(playing ? android.R.drawable.ic_media_pause : android.R.drawable.ic_media_play, playing ? "إيقاف مؤقت" : "تشغيل", serviceAction(ACTION_TOGGLE, 4002)).build();
        Notification.Action next = new Notification.Action.Builder(android.R.drawable.ic_media_next, "التالي", serviceAction(ACTION_NEXT, 4003)).build();
        Notification.Action stop = new Notification.Action.Builder(android.R.drawable.ic_menu_close_clear_cancel, "إغلاق", serviceAction(ACTION_STOP, 4004)).build();
        return new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle("سورة " + surahName())
                .setContentText(buffering ? "جارٍ تجهيز التلاوة — ياسر الدوسري" : "ياسر الدوسري")
                .setContentIntent(content)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setOnlyAlertOnce(true)
                .setOngoing(playing || buffering)
                .setShowWhen(false)
                .addAction(previous).addAction(toggle).addAction(next).addAction(stop)
                .setStyle(new Notification.MediaStyle().setMediaSession(mediaSession.getSessionToken()).setShowActionsInCompactView(0, 1, 2))
                .build();
    }

    private void ensureForeground() {
        Notification notification = buildNotification();
        if (!startedForeground) {
            startForeground(NOTIFICATION_ID, notification);
            startedForeground = true;
        } else {
            ((NotificationManager) getSystemService(NOTIFICATION_SERVICE)).notify(NOTIFICATION_ID, notification);
        }
    }

    private void updateNotification() {
        if (player == null && !startedForeground) return;
        ensureForeground();
    }

    private void broadcastState() {
        Intent state = new Intent(BROADCAST_STATE).setPackage(getPackageName());
        state.putExtra("playing", player != null && player.isPlaying());
        state.putExtra("buffering", buffering);
        state.putExtra("surah", currentSurah);
        state.putExtra("name", surahName());
        sendBroadcast(state);
    }

    private String surahName() { return SURAHS[Math.max(0, Math.min(SURAHS.length - 1, currentSurah - 1))]; }

    private void createChannel() {
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "تلاوة القرآن", NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("مشغل تلاوة ياسر الدوسري");
        channel.setSound(null, null);
        manager.createNotificationChannel(channel);
    }

    private void releasePlayer() {
        if (player != null) {
            try { player.stop(); } catch (Exception ignored) {}
            player.reset();
            player.release();
            player = null;
        }
        buffering = false;
    }

    private void stopSelfSafely() {
        releasePlayer();
        updatePlaybackState();
        broadcastState();
        if (mediaSession != null) mediaSession.setActive(false);
        stopForeground(STOP_FOREGROUND_REMOVE);
        startedForeground = false;
        stopSelf();
    }

    @Override public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        releasePlayer();
        if (mediaSession != null) { mediaSession.release(); mediaSession = null; }
        super.onDestroy();
    }
}
