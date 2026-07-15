package com.ayman.offlineai;

import android.content.res.AssetFileDescriptor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.ImageButton;
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
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {

    private static final String LANGUAGE_MODEL_ASSET = "models/qwen-0.5b.task";
    private static final String VISION_MODEL_ASSET = "models/efficientnet-lite0.tflite";
    private static final String LANGUAGE_MODEL_FILE = "qwen-0.5b.task";
    private static final long MIN_VALID_MODEL_BYTES = 500_000_000L;

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

    private LlmInference llmInference;
    private ImageClassifier imageClassifier;
    private File activeModelFile;
    private Bitmap selectedBitmap;
    private String selectedImageLabels = "";
    private volatile boolean busy = false;
    private volatile boolean visionAvailable = false;

    private final ActivityResultLauncher<String[]> imagePicker = registerForActivityResult(
            new ActivityResultContracts.OpenDocument(), this::onImageSelected);

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

        addAssistantMessage("أهلًا بك 👋 أنا نبراس، مساعد يعمل داخل هاتفك دون إنترنت. يتم تجهيز النموذج المدمج تلقائيًا في أول تشغيل فقط.");
        prepareEmbeddedModels();
    }

    private void prepareEmbeddedModels() {
        busy = true;
        setControlsEnabled(false);
        setPreparationProgress(0, "جارٍ تجهيز الذكاء المحلي لأول مرة...");
        statusText.setText("يتم التجهيز");
        modelInfoText.setText("لا تغلق التطبيق أثناء نسخ النموذج");

        executor.execute(() -> {
            try {
                File modelFile = ensureLanguageModelExtracted();
                activeModelFile = modelFile;
                initializeVisionModelSafely();
                initializeLanguageModel(modelFile);

                runOnUiThread(() -> {
                    busy = false;
                    setControlsEnabled(true);
                    modelProgress.setVisibility(View.GONE);
                    progressText.setVisibility(View.GONE);
                    statusText.setText("● جاهز دون إنترنت");
                    modelInfoText.setText("Qwen 2.5 محلي • " + humanSize(modelFile.length())
                            + (visionAvailable ? " • رؤية أساسية" : ""));
                    addSystemMessage("تم تجهيز التطبيق بنجاح. من الآن سيعمل مباشرة دون اختيار أي ملفات.");
                });
            } catch (Exception e) {
                runOnUiThread(() -> showError("تعذر تجهيز الذكاء المحلي: " + safeMessage(e)));
            }
        });
    }

    private File ensureLanguageModelExtracted() throws Exception {
        File modelDir = new File(getFilesDir(), "models");
        if (!modelDir.exists() && !modelDir.mkdirs()) {
            throw new IllegalStateException("تعذر إنشاء مساحة النموذج داخل الهاتف");
        }

        File target = new File(modelDir, LANGUAGE_MODEL_FILE);
        if (target.exists() && target.length() >= MIN_VALID_MODEL_BYTES) {
            runOnUiThread(() -> setPreparationProgress(88, "تم العثور على النموذج المدمج..."));
            return target;
        }

        File temporary = new File(modelDir, LANGUAGE_MODEL_FILE + ".part");
        if (temporary.exists() && !temporary.delete()) {
            throw new IllegalStateException("تعذر حذف نسخة تجهيز غير مكتملة");
        }
        if (target.exists() && !target.delete()) {
            throw new IllegalStateException("تعذر استبدال النموذج غير المكتمل");
        }

        long totalBytes = -1L;
        try (AssetFileDescriptor descriptor = getAssets().openFd(LANGUAGE_MODEL_ASSET)) {
            totalBytes = descriptor.getLength();
        } catch (Exception ignored) {
            // The copy still works even if the exact asset size cannot be read.
        }

        if (totalBytes > 0 && modelDir.getUsableSpace() < totalBytes + 160_000_000L) {
            throw new IllegalStateException("المساحة الحرة غير كافية. حرر نحو 800 ميجابايت ثم افتح التطبيق مجددًا");
        }

        long copied = 0L;
        int lastProgress = -1;
        try (InputStream input = getAssets().open(LANGUAGE_MODEL_ASSET);
             OutputStream output = new FileOutputStream(temporary)) {
            byte[] buffer = new byte[2 * 1024 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
                copied += read;
                if (totalBytes > 0) {
                    int progress = Math.min(86, (int) ((copied * 86L) / totalBytes));
                    if (progress >= lastProgress + 2) {
                        lastProgress = progress;
                        final int progressValue = progress;
                        final String copiedText = "نسخ النموذج: " + progressValue + "%";
                        runOnUiThread(() -> setPreparationProgress(progressValue, copiedText));
                    }
                }
            }
            output.flush();
        } catch (Exception e) {
            temporary.delete();
            throw e;
        }

        if (temporary.length() < MIN_VALID_MODEL_BYTES) {
            temporary.delete();
            throw new IllegalStateException("ملف النموذج المدمج غير مكتمل");
        }
        if (!temporary.renameTo(target)) {
            throw new IllegalStateException("تعذر تثبيت النموذج داخل التطبيق");
        }
        return target;
    }

    private void initializeLanguageModel(File modelFile) {
        runOnUiThread(() -> setPreparationProgress(92, "جارٍ تشغيل محرك المحادثة..."));
        closeLanguageModel();
        LlmInference.LlmInferenceOptions options = LlmInference.LlmInferenceOptions.builder()
                .setModelPath(modelFile.getAbsolutePath())
                .setMaxTokens(512)
                .setMaxTopK(40)
                .build();
        llmInference = LlmInference.createFromOptions(getApplicationContext(), options);
        runOnUiThread(() -> setPreparationProgress(100, "اكتمل التشغيل"));
    }

    private void initializeVisionModelSafely() {
        runOnUiThread(() -> setPreparationProgress(89, "جارٍ تشغيل نموذج رؤية الصور..."));
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
        } catch (Exception ignored) {
            visionAvailable = false;
            imageClassifier = null;
        }
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
        if (busy) return;
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
        progressText.setText(message);
    }

    private void showError(String message) {
        busy = false;
        setControlsEnabled(false);
        statusText.setText("● تعذر التشغيل");
        modelInfoText.setText("تأكد من وجود مساحة كافية ثم أعد فتح التطبيق");
        progressText.setVisibility(View.VISIBLE);
        progressText.setText(message);
        addSystemMessage(message);
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
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
        return String.format(Locale.US, "%.0f %s", value, units[unit]);
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
