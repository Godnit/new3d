package com.ayman.offlineai;

import android.app.DownloadManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.google.android.material.button.MaterialButton;
import com.google.android.material.progressindicator.LinearProgressIndicator;
import com.google.android.material.textfield.TextInputEditText;
import com.google.mediapipe.framework.image.BitmapImageBuilder;
import com.google.mediapipe.framework.image.MPImage;
import com.google.mediapipe.tasks.components.containers.Category;
import com.google.mediapipe.tasks.core.BaseOptions;
import com.google.mediapipe.tasks.genai.llminference.LlmInference;
import com.google.mediapipe.tasks.vision.core.RunningMode;
import com.google.mediapipe.tasks.vision.imageclassifier.ImageClassifier;
import com.google.mediapipe.tasks.vision.imageclassifier.ImageClassifierResult;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {

    private static final String MODEL_URL =
            "https://huggingface.co/litert-community/Qwen2.5-0.5B-Instruct/resolve/main/"
                    + "Qwen2.5-0.5B-Instruct_multi-prefill-seq_q8_ekv1280.task?download=true";
    private static final String MODEL_FILE_NAME = "qwen-0.5b.task";
    private static final String VISION_MODEL_ASSET = "models/efficientnet-lite0.tflite";
    private static final long MODEL_SIZE_BYTES = 546_660_344L;
    private static final String MODEL_SHA256 =
            "e608953f169aeb1bd7b9155fec2559825e08453fc209b84eda3a781ed0452fd2";
    private static final String PREFS = "nebras_model_state";
    private static final String KEY_DOWNLOAD_ID = "download_id";
    private static final String KEY_TRUSTED_PATH = "trusted_path";
    private static final String KEY_TRUSTED_SIZE = "trusted_size";

    private TextView statusText;
    private TextView modelInfoText;
    private TextView progressText;
    private TextView imageLabelsText;
    private TextInputEditText promptInput;
    private MaterialButton sendButton;
    private MaterialButton selectImageButton;
    private LinearProgressIndicator modelProgress;
    private ImageView selectedImageView;
    private View selectedImageCard;
    private LinearLayout chatContainer;
    private ScrollView chatScroll;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final List<String> conversation = new ArrayList<>();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());

    private LlmInference llmInference;
    private ImageClassifier imageClassifier;
    private Bitmap selectedBitmap;
    private String selectedImageLabels = "";
    private volatile boolean busy = false;
    private volatile boolean visionAvailable = false;
    private volatile boolean destroyed = false;

    private DownloadManager downloadManager;
    private SharedPreferences preferences;
    private long activeDownloadId = -1L;

    private final ActivityResultLauncher<String[]> imagePicker = registerForActivityResult(
            new ActivityResultContracts.OpenDocument(), this::onImageSelected);

    private final Runnable downloadWatcher = new Runnable() {
        @Override
        public void run() {
            if (destroyed || activeDownloadId < 0) return;
            observeDownload(activeDownloadId);
        }
    };

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusText = findViewById(R.id.statusText);
        modelInfoText = findViewById(R.id.modelInfoText);
        progressText = findViewById(R.id.progressText);
        imageLabelsText = findViewById(R.id.imageLabelsText);
        promptInput = findViewById(R.id.promptInput);
        sendButton = findViewById(R.id.sendButton);
        selectImageButton = findViewById(R.id.selectImageButton);
        modelProgress = findViewById(R.id.modelProgress);
        selectedImageView = findViewById(R.id.selectedImageView);
        selectedImageCard = findViewById(R.id.selectedImageCard);
        chatContainer = findViewById(R.id.chatContainer);
        chatScroll = findViewById(R.id.chatScroll);

        downloadManager = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
        preferences = getSharedPreferences(PREFS, MODE_PRIVATE);

        selectImageButton.setOnClickListener(v -> imagePicker.launch(new String[]{"image/*"}));
        findViewById(R.id.newChatButton).setOnClickListener(v -> clearChat());
        findViewById(R.id.removeImageButton).setOnClickListener(v -> clearSelectedImage());
        sendButton.setOnClickListener(v -> sendPrompt());
        promptInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                sendPrompt();
                return true;
            }
            return false;
        });

        addAssistantMessage("أهلًا بك 👋 أنا نبراس. أعمل داخل هاتفك دون إنترنت بعد تجهيز النموذج مرة واحدة فقط.");
        prepareLocalAI();
    }

    private void prepareLocalAI() {
        busy = true;
        setControlsEnabled(false);
        progressText.setOnClickListener(null);
        setPreparationProgress(0, "جارٍ فحص النموذج المحلي...");
        statusText.setText("● يتم التجهيز");
        modelInfoText.setText("لن تحتاج إلى اختيار أي ملف");

        executor.execute(() -> {
            initializeVisionModelSafely();
            File existing = findReusableModel();
            if (existing != null) {
                initializeLanguageModel(existing);
                showReady(existing, "تم العثور على النموذج الموجود في الهاتف");
            } else {
                runOnUiThread(this::startOrResumeDownload);
            }
        });
    }

    private File findReusableModel() {
        File oldInternal = new File(new File(getFilesDir(), "models"), MODEL_FILE_NAME);
        if (isValidModel(oldInternal)) return oldInternal;

        File downloaded = getDownloadedModelFile();
        if (isValidModel(downloaded)) return downloaded;
        return null;
    }

    private boolean isValidModel(File file) {
        if (file == null || !file.isFile() || file.length() != MODEL_SIZE_BYTES) return false;

        String trustedPath = preferences.getString(KEY_TRUSTED_PATH, "");
        long trustedSize = preferences.getLong(KEY_TRUSTED_SIZE, -1L);
        if (file.getAbsolutePath().equals(trustedPath) && trustedSize == file.length()) return true;

        runOnUiThread(() -> setPreparationProgress(94, "جارٍ التأكد من سلامة النموذج..."));
        try {
            String hash = sha256(file);
            if (MODEL_SHA256.equalsIgnoreCase(hash)) {
                markModelTrusted(file);
                return true;
            }
        } catch (Exception ignored) {
        }

        if (!file.delete()) file.deleteOnExit();
        return false;
    }

    private void markModelTrusted(File file) {
        preferences.edit()
                .putString(KEY_TRUSTED_PATH, file.getAbsolutePath())
                .putLong(KEY_TRUSTED_SIZE, file.length())
                .apply();
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new FileInputStream(file)) {
            byte[] buffer = new byte[2 * 1024 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) digest.update(buffer, 0, read);
        }
        byte[] bytes = digest.digest();
        StringBuilder value = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) value.append(String.format(Locale.US, "%02x", b & 0xff));
        return value.toString();
    }

    private void startOrResumeDownload() {
        if (destroyed) return;
        busy = true;
        setControlsEnabled(false);

        long storedId = preferences.getLong(KEY_DOWNLOAD_ID, -1L);
        if (storedId >= 0 && downloadExists(storedId)) {
            activeDownloadId = storedId;
            statusText.setText("● يستكمل تنزيل النموذج");
            modelInfoText.setText("يمكنك إغلاق التطبيق وسيواصل أندرويد التنزيل");
            mainHandler.removeCallbacks(downloadWatcher);
            mainHandler.post(downloadWatcher);
            return;
        }

        File target = getDownloadedModelFile();
        if (target.exists() && !target.delete()) {
            showDownloadFailure("تعذر استبدال ملف تنزيل قديم");
            return;
        }
        File parent = target.getParentFile();
        if (parent != null && !parent.exists()) parent.mkdirs();

        if (target.getUsableSpace() < MODEL_SIZE_BYTES + 120_000_000L) {
            showDownloadFailure("المساحة الحرة غير كافية. حرر نحو 700 ميجابايت ثم اضغط هنا للمحاولة");
            return;
        }

        try {
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(MODEL_URL));
            request.setTitle("نبراس AI - تنزيل النموذج المحلي");
            request.setDescription("يتم تنزيل النموذج مرة واحدة ثم يعمل التطبيق دون إنترنت");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setAllowedOverMetered(true);
            request.setAllowedOverRoaming(true);
            request.setDestinationInExternalFilesDir(this, Environment.DIRECTORY_DOWNLOADS, MODEL_FILE_NAME);

            activeDownloadId = downloadManager.enqueue(request);
            preferences.edit().putLong(KEY_DOWNLOAD_ID, activeDownloadId).apply();
            statusText.setText("● بدأ تنزيل النموذج");
            modelInfoText.setText("التنزيل قابل للاستكمال عند انقطاع الإنترنت");
            setPreparationProgress(0, "بدء تنزيل 522 ميجابايت...");
            mainHandler.removeCallbacks(downloadWatcher);
            mainHandler.post(downloadWatcher);
        } catch (Exception e) {
            showDownloadFailure("تعذر بدء التنزيل: " + safeMessage(e));
        }
    }

    private boolean downloadExists(long downloadId) {
        DownloadManager.Query query = new DownloadManager.Query().setFilterById(downloadId);
        try (Cursor cursor = downloadManager.query(query)) {
            return cursor != null && cursor.moveToFirst();
        } catch (Exception ignored) {
            return false;
        }
    }

    private void observeDownload(long downloadId) {
        DownloadManager.Query query = new DownloadManager.Query().setFilterById(downloadId);
        try (Cursor cursor = downloadManager.query(query)) {
            if (cursor == null || !cursor.moveToFirst()) {
                clearStoredDownload();
                showDownloadFailure("توقف التنزيل. اضغط هنا لإعادته");
                return;
            }

            int status = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));
            long downloaded = cursor.getLong(cursor.getColumnIndexOrThrow(
                    DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR));
            long total = cursor.getLong(cursor.getColumnIndexOrThrow(
                    DownloadManager.COLUMN_TOTAL_SIZE_BYTES));
            if (total <= 0) total = MODEL_SIZE_BYTES;

            int percent = Math.max(0, Math.min(100, (int) ((downloaded * 100L) / total)));
            String amount = humanSize(downloaded) + " من " + humanSize(total);

            if (status == DownloadManager.STATUS_SUCCESSFUL) {
                mainHandler.removeCallbacks(downloadWatcher);
                preferences.edit().remove(KEY_DOWNLOAD_ID).apply();
                activeDownloadId = -1L;
                verifyDownloadedModel();
                return;
            }

            if (status == DownloadManager.STATUS_FAILED) {
                int reason = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON));
                clearStoredDownload();
                showDownloadFailure("فشل التنزيل (" + reason + "). اضغط هنا لإعادة المحاولة");
                return;
            }

            if (status == DownloadManager.STATUS_PAUSED) {
                statusText.setText("● التنزيل متوقف مؤقتًا");
                modelInfoText.setText("سيُستكمل تلقائيًا عند تحسن الاتصال");
                setPreparationProgress(percent, amount);
            } else if (status == DownloadManager.STATUS_PENDING) {
                statusText.setText("● بانتظار بدء التنزيل");
                modelInfoText.setText("أندرويد يجهز اتصال التنزيل");
                setPreparationProgress(percent, amount);
            } else {
                statusText.setText("● ينزّل النموذج " + percent + "%");
                modelInfoText.setText("يمكن إغلاق التطبيق وسيواصل أندرويد التنزيل");
                setPreparationProgress(percent, amount);
            }

            mainHandler.postDelayed(downloadWatcher, 1500L);
        } catch (Exception e) {
            mainHandler.postDelayed(downloadWatcher, 2500L);
        }
    }

    private void verifyDownloadedModel() {
        busy = true;
        setControlsEnabled(false);
        setPreparationProgress(100, "اكتمل التنزيل، جارٍ فحص الملف...");
        statusText.setText("● يتحقق من النموذج");

        executor.execute(() -> {
            File file = getDownloadedModelFile();
            if (isValidModel(file)) {
                initializeLanguageModel(file);
                showReady(file, "اكتمل تنزيل النموذج وحفظه داخل الهاتف");
            } else {
                runOnUiThread(() -> {
                    preferences.edit().remove(KEY_TRUSTED_PATH).remove(KEY_TRUSTED_SIZE).apply();
                    showDownloadFailure("ملف التنزيل غير مكتمل. اضغط هنا لإعادة تنزيله");
                });
            }
        });
    }

    private void clearStoredDownload() {
        mainHandler.removeCallbacks(downloadWatcher);
        if (activeDownloadId >= 0) {
            try {
                downloadManager.remove(activeDownloadId);
            } catch (Exception ignored) {
            }
        }
        activeDownloadId = -1L;
        preferences.edit().remove(KEY_DOWNLOAD_ID).apply();
    }

    private void showDownloadFailure(String message) {
        busy = false;
        setControlsEnabled(false);
        statusText.setText("● يحتاج اتصالًا لإكمال التجهيز");
        modelInfoText.setText("بعد التنزيل سيعمل دون إنترنت دائمًا");
        modelProgress.setVisibility(View.VISIBLE);
        progressText.setVisibility(View.VISIBLE);
        progressText.setText(message);
        progressText.setTextColor(getResources().getColor(R.color.teal_light));
        progressText.setOnClickListener(v -> startOrResumeDownload());
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private File getDownloadedModelFile() {
        File downloads = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
        if (downloads == null) downloads = getFilesDir();
        return new File(downloads, MODEL_FILE_NAME);
    }

    private void initializeLanguageModel(File modelFile) {
        runOnUiThread(() -> setPreparationProgress(97, "جارٍ تشغيل محرك المحادثة..."));
        closeLanguageModel();
        LlmInference.LlmInferenceOptions options = LlmInference.LlmInferenceOptions.builder()
                .setModelPath(modelFile.getAbsolutePath())
                .setMaxTokens(512)
                .setMaxTopK(40)
                .build();
        llmInference = LlmInference.createFromOptions(getApplicationContext(), options);
    }

    private void initializeVisionModelSafely() {
        try {
            BaseOptions baseOptions = BaseOptions.builder()
                    .setModelAssetPath(VISION_MODEL_ASSET)
                    .build();
            ImageClassifier.ImageClassifierOptions options = ImageClassifier.ImageClassifierOptions.builder()
                    .setBaseOptions(baseOptions)
                    .setRunningMode(RunningMode.IMAGE)
                    .setMaxResults(5)
                    .setScoreThreshold(0.02f)
                    .build();
            imageClassifier = ImageClassifier.createFromOptions(getApplicationContext(), options);
            visionAvailable = true;
        } catch (Throwable ignored) {
            visionAvailable = false;
            imageClassifier = null;
        }
    }

    private void showReady(File modelFile, String message) {
        runOnUiThread(() -> {
            if (destroyed) return;
            busy = false;
            setControlsEnabled(true);
            modelProgress.setVisibility(View.GONE);
            progressText.setVisibility(View.GONE);
            progressText.setOnClickListener(null);
            statusText.setText("● جاهز دون إنترنت");
            modelInfoText.setText("Qwen 2.5 محلي • " + humanSize(modelFile.length())
                    + (visionAvailable ? " • رؤية أساسية" : ""));
            addSystemMessage(message + ". لن تحتاج إلى تنزيله مرة أخرى.");
        });
    }

    private void onImageSelected(Uri uri) {
        if (uri == null || busy) return;
        busy = true;
        setControlsEnabled(false);
        statusText.setText("● يحلل الصورة محليًا");

        executor.execute(() -> {
            try (InputStream input = getContentResolver().openInputStream(uri)) {
                Bitmap bitmap = BitmapFactory.decodeStream(input);
                if (bitmap == null) throw new IllegalStateException("الصورة غير صالحة");
                Bitmap scaled = scaleBitmap(bitmap, 768);
                String labels = classifyImage(scaled);
                runOnUiThread(() -> {
                    selectedBitmap = scaled;
                    selectedImageLabels = labels;
                    selectedImageView.setImageBitmap(scaled);
                    imageLabelsText.setText(labels);
                    selectedImageCard.setVisibility(View.VISIBLE);
                    busy = false;
                    setControlsEnabled(true);
                    statusText.setText("● الصورة جاهزة للسؤال");
                    modelInfoText.setText("اكتب سؤالك عن الصورة ثم اضغط إرسال");
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    busy = false;
                    setControlsEnabled(true);
                    Toast.makeText(this, "تعذر تحليل الصورة: " + safeMessage(e), Toast.LENGTH_LONG).show();
                    statusText.setText("● جاهز دون إنترنت");
                });
            }
        });
    }

    private String classifyImage(Bitmap bitmap) {
        if (!visionAvailable || imageClassifier == null) {
            return "تم إرفاق الصورة، لكن نموذج الرؤية غير متاح على هذا الجهاز";
        }

        MPImage mpImage = new BitmapImageBuilder(bitmap).build();
        try {
            ImageClassifierResult result = imageClassifier.classify(mpImage);
            if (result.classificationResult().classifications().isEmpty()) {
                return "لم يتعرف نموذج الرؤية على محتوى واضح";
            }

            List<Category> categories = result.classificationResult().classifications().get(0).categories();
            StringBuilder labels = new StringBuilder("رؤية محلية: ");
            int included = 0;
            for (Category category : categories) {
                if (included >= 5) break;
                String name = category.displayName();
                if (name == null || name.trim().isEmpty()) name = category.categoryName();
                if (name == null || name.trim().isEmpty()) continue;
                if (included > 0) labels.append("، ");
                labels.append(name.trim())
                        .append(" ")
                        .append(Math.round(category.score() * 100f))
                        .append("%");
                included++;
            }
            return included == 0 ? "لم يتعرف نموذج الرؤية على محتوى واضح" : labels.toString();
        } finally {
            mpImage.close();
        }
    }

    private void sendPrompt() {
        if (busy) return;
        if (llmInference == null) {
            Toast.makeText(this, "لا يزال النموذج قيد التجهيز", Toast.LENGTH_LONG).show();
            return;
        }

        String userText = promptInput.getText() == null ? "" : promptInput.getText().toString().trim();
        if (userText.isEmpty() && selectedBitmap != null) {
            userText = "صف لي هذه الصورة وما الذي يظهر فيها.";
        }
        if (userText.isEmpty()) return;

        promptInput.setText("");
        addUserMessage(userText);

        String enrichedText = userText;
        if (selectedBitmap != null) {
            enrichedText += "\n\nنتائج نموذج الرؤية المحلي للصورة: " + selectedImageLabels
                    + "\nاعتمد على هذه النتائج فقط، ولا تخترع تفاصيل بصرية غير موجودة. اشرح للمستخدم بالعربية بوضوح.";
        }
        conversation.add("<|im_start|>user\n" + enrichedText + "<|im_end|>\n");

        busy = true;
        setControlsEnabled(false);
        statusText.setText("● يفكر داخل الهاتف...");
        modelInfoText.setText("قد يستغرق الرد بعض الوقت على الأجهزة القديمة");
        TextView assistantBubble = addAssistantMessage("يفكر...");

        executor.execute(() -> {
            try {
                String answer = llmInference.generateResponse(buildConversationPrompt());
                if (answer == null || answer.trim().isEmpty()) answer = "لم يُرجع النموذج إجابة.";
                String finalAnswer = cleanModelAnswer(answer);
                conversation.add("<|im_start|>assistant\n" + finalAnswer + "<|im_end|>\n");
                trimConversation();

                runOnUiThread(() -> {
                    assistantBubble.setText(finalAnswer);
                    clearSelectedImage();
                    busy = false;
                    setControlsEnabled(true);
                    statusText.setText("● جاهز دون إنترنت");
                    modelInfoText.setText("Qwen 2.5 محلي • بياناتك لا تغادر الهاتف");
                    scrollToBottom();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    assistantBubble.setText("تعذر إنشاء الرد: " + safeMessage(e));
                    busy = false;
                    setControlsEnabled(true);
                    statusText.setText("● جاهز بعد خطأ");
                    modelInfoText.setText("أعد المحاولة برسالة أقصر");
                });
            }
        });
    }

    private String buildConversationPrompt() {
        StringBuilder prompt = new StringBuilder();
        prompt.append("<|im_start|>system\n")
                .append("أنت نبراس، مساعد عربي مفيد يعمل بالكامل داخل هاتف المستخدم دون إنترنت. ")
                .append("أجب بالعربية الواضحة، وكن صادقًا بشأن حدود معرفتك. ")
                .append("لا تقل إنك اتصلت بالإنترنت، ولا تدّع رؤية تفاصيل لم يقدمها نموذج الرؤية المحلي.")
                .append("<|im_end|>\n");
        for (String turn : conversation) prompt.append(turn);
        prompt.append("<|im_start|>assistant\n");
        return prompt.toString();
    }

    private String cleanModelAnswer(String answer) {
        String cleaned = answer.trim();
        int endToken = cleaned.indexOf("<|im_end|>");
        if (endToken >= 0) cleaned = cleaned.substring(0, endToken).trim();
        if (cleaned.startsWith("assistant\n")) cleaned = cleaned.substring(10).trim();
        return cleaned.isEmpty() ? "لم يُرجع النموذج إجابة واضحة." : cleaned;
    }

    private void trimConversation() {
        while (conversation.size() > 8) conversation.remove(0);
    }

    private void clearChat() {
        if (busy || llmInference == null) return;
        conversation.clear();
        chatContainer.removeAllViews();
        clearSelectedImage();
        addAssistantMessage("بدأنا محادثة جديدة. اسألني ما تريد وسأجيب محليًا دون إنترنت.");
        statusText.setText("● جاهز دون إنترنت");
    }

    private void clearSelectedImage() {
        selectedBitmap = null;
        selectedImageLabels = "";
        selectedImageView.setImageDrawable(null);
        selectedImageCard.setVisibility(View.GONE);
    }

    private TextView addUserMessage(String text) {
        return addBubble(text, true, false);
    }

    private TextView addAssistantMessage(String text) {
        return addBubble(text, false, false);
    }

    private void addSystemMessage(String text) {
        addBubble(text, false, true);
    }

    private TextView addBubble(String text, boolean user, boolean system) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(system ? 13 : 16);
        view.setTextColor(user ? Color.WHITE : Color.rgb(16, 32, 51));
        view.setPadding(dp(16), dp(12), dp(16), dp(12));
        view.setTextIsSelectable(true);
        view.setGravity(Gravity.START);
        view.setTextDirection(View.TEXT_DIRECTION_FIRST_STRONG);
        view.setLineSpacing(0f, 1.12f);
        view.setMaxWidth((int) (getResources().getDisplayMetrics().widthPixels * 0.84f));

        GradientDrawable background = new GradientDrawable();
        background.setCornerRadius(dp(system ? 16 : 21));
        if (system) {
            background.setColor(Color.rgb(232, 242, 255));
            background.setStroke(dp(1), Color.rgb(199, 218, 242));
        } else if (user) {
            background.setColor(Color.rgb(15, 174, 158));
        } else {
            background.setColor(Color.WHITE);
            background.setStroke(dp(1), Color.rgb(220, 229, 238));
        }
        view.setBackground(background);
        view.setElevation(dp(system ? 0 : 1));

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                system ? LinearLayout.LayoutParams.MATCH_PARENT : LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        params.gravity = system ? Gravity.CENTER : (user ? Gravity.END : Gravity.START);
        params.setMargins(user ? dp(42) : 0, dp(6), user ? 0 : dp(42), dp(6));
        view.setLayoutParams(params);
        chatContainer.addView(view);
        scrollToBottom();
        return view;
    }

    private void scrollToBottom() {
        chatScroll.post(() -> chatScroll.fullScroll(View.FOCUS_DOWN));
    }

    private void setControlsEnabled(boolean enabled) {
        sendButton.setEnabled(enabled);
        selectImageButton.setEnabled(enabled && visionAvailable);
        promptInput.setEnabled(enabled);
    }

    private void setPreparationProgress(int progress, String message) {
        modelProgress.setVisibility(View.VISIBLE);
        progressText.setVisibility(View.VISIBLE);
        modelProgress.setProgress(progress);
        progressText.setTextColor(getResources().getColor(R.color.header_text_muted));
        progressText.setText(message);
    }

    private void closeLanguageModel() {
        if (llmInference != null) {
            try {
                llmInference.close();
            } catch (Exception ignored) {
            }
            llmInference = null;
        }
    }

    private Bitmap scaleBitmap(Bitmap source, int maxSide) {
        int width = source.getWidth();
        int height = source.getHeight();
        int largest = Math.max(width, height);
        if (largest <= maxSide) return source;
        float ratio = maxSide / (float) largest;
        return Bitmap.createScaledBitmap(source,
                Math.max(1, Math.round(width * ratio)),
                Math.max(1, Math.round(height * ratio)), true);
    }

    private String humanSize(long bytes) {
        if (bytes < 1024) return bytes + " بايت";
        double value = bytes;
        String[] units = {"ك.ب", "م.ب", "ج.ب"};
        int unit = -1;
        while (value >= 1024 && unit < units.length - 1) {
            value /= 1024;
            unit++;
        }
        return String.format(Locale.US, value >= 100 ? "%.0f %s" : "%.1f %s", value, units[unit]);
    }

    private String safeMessage(Exception e) {
        String message = e.getMessage();
        return message == null || message.trim().isEmpty() ? e.getClass().getSimpleName() : message;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onDestroy() {
        destroyed = true;
        mainHandler.removeCallbacks(downloadWatcher);
        closeLanguageModel();
        if (imageClassifier != null) {
            try {
                imageClassifier.close();
            } catch (Exception ignored) {
            }
            imageClassifier = null;
        }
        executor.shutdownNow();
        super.onDestroy();
    }
}
