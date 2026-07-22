#!/usr/bin/env python3
from pathlib import Path

import prepare_v412


def replace_exact(path: Path, old: str, new: str, expected_min: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count < expected_min:
        raise RuntimeError(f"Expected at least {expected_min} occurrence(s) in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")
    print(f"patched {path}: {count} occurrence(s)")


def main() -> None:
    prepare_v412.main()
    root = Path(__file__).resolve().parents[1]
    java = root / "app/src/main/java/com/mastermedia/quranoffline"
    assets = root / "app/src/main/assets"
    audio = java / "AudioServiceV410.java"
    activity = java / "MainActivityV410.java"
    reader = assets / "app-v11.js"

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
        public void deleteSurahAudio(int number) {
            if (number < 1 || number > 114 || AudioDownloadServiceV414.isBuiltIn(number)) return;
            Intent intent = new Intent(MainActivityV410.this, AudioDownloadServiceV414.class)
                    .setAction(AudioDownloadServiceV414.ACTION_DELETE)
                    .putExtra(AudioDownloadServiceV414.EXTRA_SURAH, number);
            runOnUiThread(() -> {
                try { startService(intent); } catch (RuntimeException ignored) {}
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
