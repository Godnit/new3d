package com.ayman.offlineai;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
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
import com.google.android.material.textfield.TextInputEditText;
import com.google.mediapipe.framework.image.BitmapImageBuilder;
import com.google.mediapipe.framework.image.MPImage;
import com.google.mediapipe.tasks.genai.llminference.GraphOptions;
import com.google.mediapipe.tasks.genai.llminference.LlmInference;
import com.google.mediapipe.tasks.genai.llminference.LlmInferenceSession;

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

    private TextView statusText;
    private TextInputEditText promptInput;
    private MaterialButton sendButton;
    private ImageView selectedImageView;
    private LinearLayout chatContainer;
    private ScrollView chatScroll;

    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final List<String> conversation = new ArrayList<>();

    private LlmInference llmInference;
    private File activeModelFile;
    private Bitmap selectedBitmap;
    private volatile boolean busy = false;

    private final ActivityResultLauncher<String[]> modelPicker = registerForActivityResult(
            new ActivityResultContracts.OpenDocument(), this::onModelSelected);

    private final ActivityResultLauncher<String[]> imagePicker = registerForActivityResult(
            new ActivityResultContracts.OpenDocument(), this::onImageSelected);

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        statusText = findViewById(R.id.statusText);
        promptInput = findViewById(R.id.promptInput);
        sendButton = findViewById(R.id.sendButton);
        selectedImageView = findViewById(R.id.selectedImageView);
        chatContainer = findViewById(R.id.chatContainer);
        chatScroll = findViewById(R.id.chatScroll);

        findViewById(R.id.selectModelButton).setOnClickListener(v ->
                modelPicker.launch(new String[]{"application/octet-stream", "*/*"}));
        findViewById(R.id.selectImageButton).setOnClickListener(v ->
                imagePicker.launch(new String[]{"image/*"}));
        findViewById(R.id.newChatButton).setOnClickListener(v -> clearChat());
        sendButton.setOnClickListener(v -> sendPrompt());

        addSystemMessage("مرحبًا! اختر ملف نموذج بصيغة .task أولًا. بعد تحميله يمكنك المحادثة دون إنترنت. تحليل الصور يحتاج نموذجًا يدعم الرؤية مثل Gemma 3n.");

        File saved = new File(new File(getFilesDir(), "models"), "active_model.task");
        if (saved.exists() && saved.length() > 0) {
            activeModelFile = saved;
            initializeModel(saved);
        }
    }

    private void onModelSelected(Uri uri) {
        if (uri == null || busy) return;
        busy = true;
        setControlsEnabled(false);
        statusText.setText("جارٍ نسخ النموذج إلى التطبيق...");

        executor.execute(() -> {
            try {
                File dir = new File(getFilesDir(), "models");
                if (!dir.exists() && !dir.mkdirs()) {
                    throw new IllegalStateException("تعذر إنشاء مجلد النماذج");
                }
                File target = new File(dir, "active_model.task");
                try (InputStream in = getContentResolver().openInputStream(uri);
                     OutputStream out = new FileOutputStream(target)) {
                    if (in == null) throw new IllegalStateException("تعذر فتح ملف النموذج");
                    byte[] buffer = new byte[1024 * 1024];
                    int read;
                    while ((read = in.read(buffer)) != -1) {
                        out.write(buffer, 0, read);
                    }
                    out.flush();
                }
                activeModelFile = target;
                runOnUiThread(() -> {
                    busy = false;
                    initializeModel(target);
                });
            } catch (Exception e) {
                runOnUiThread(() -> showError("فشل استيراد النموذج: " + safeMessage(e)));
            }
        });
    }

    private void initializeModel(File modelFile) {
        busy = true;
        setControlsEnabled(false);
        statusText.setText("جارٍ تشغيل النموذج المحلي...");

        executor.execute(() -> {
            try {
                closeModel();
                LlmInference.LlmInferenceOptions options = LlmInference.LlmInferenceOptions.builder()
                        .setModelPath(modelFile.getAbsolutePath())
                        .setMaxTokens(1024)
                        .setMaxTopK(64)
                        .setMaxNumImages(1)
                        .build();
                llmInference = LlmInference.createFromOptions(getApplicationContext(), options);
                runOnUiThread(() -> {
                    busy = false;
                    setControlsEnabled(true);
                    statusText.setText("جاهز دون إنترنت • " + humanSize(modelFile.length()));
                    addSystemMessage("تم تشغيل النموذج بنجاح. يمكنك الآن الكتابة، أو اختيار صورة إذا كان النموذج يدعم الرؤية.");
                });
            } catch (Exception e) {
                runOnUiThread(() -> showError("تعذر تشغيل النموذج على هذا الهاتف: " + safeMessage(e)));
            }
        });
    }

    private void onImageSelected(Uri uri) {
        if (uri == null) return;
        executor.execute(() -> {
            try (InputStream in = getContentResolver().openInputStream(uri)) {
                Bitmap bitmap = BitmapFactory.decodeStream(in);
                if (bitmap == null) throw new IllegalStateException("الصورة غير صالحة");
                Bitmap scaled = scaleBitmap(bitmap, 1024);
                runOnUiThread(() -> {
                    selectedBitmap = scaled;
                    selectedImageView.setImageBitmap(scaled);
                    selectedImageView.setVisibility(View.VISIBLE);
                    statusText.setText("تمت إضافة صورة • اكتب سؤالك عنها");
                });
            } catch (Exception e) {
                runOnUiThread(() -> showError("تعذر فتح الصورة: " + safeMessage(e)));
            }
        });
    }

    private void sendPrompt() {
        if (busy) return;
        if (llmInference == null) {
            Toast.makeText(this, "اختر نموذجًا وشغّله أولًا", Toast.LENGTH_LONG).show();
            return;
        }

        String userText = promptInput.getText() == null ? "" : promptInput.getText().toString().trim();
        if (userText.isEmpty()) return;

        promptInput.setText("");
        addUserMessage(userText);
        conversation.add("المستخدم: " + userText);

        busy = true;
        setControlsEnabled(false);
        statusText.setText("يفكر محليًا...");
        TextView assistantBubble = addAssistantMessage("...");
        Bitmap imageForRequest = selectedBitmap;

        executor.execute(() -> {
            try {
                String answer = imageForRequest != null
                        ? generateWithImage(userText, imageForRequest)
                        : llmInference.generateResponse(buildConversationPrompt());
                if (answer == null || answer.trim().isEmpty()) answer = "لم يُرجع النموذج إجابة.";
                String finalAnswer = answer.trim();
                conversation.add("المساعد: " + finalAnswer);
                runOnUiThread(() -> {
                    assistantBubble.setText(finalAnswer);
                    selectedBitmap = null;
                    selectedImageView.setImageDrawable(null);
                    selectedImageView.setVisibility(View.GONE);
                    busy = false;
                    setControlsEnabled(true);
                    statusText.setText("جاهز دون إنترنت");
                    scrollToBottom();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    assistantBubble.setText("حدث خطأ أثناء التوليد: " + safeMessage(e));
                    busy = false;
                    setControlsEnabled(true);
                    statusText.setText("جاهز • حدث خطأ في آخر طلب");
                });
            }
        });
    }

    private String generateWithImage(String question, Bitmap bitmap) {
        MPImage mpImage = new BitmapImageBuilder(bitmap).build();
        GraphOptions graphOptions = GraphOptions.builder()
                .setEnableVisionModality(true)
                .build();
        LlmInferenceSession.LlmInferenceSessionOptions sessionOptions =
                LlmInferenceSession.LlmInferenceSessionOptions.builder()
                        .setTopK(40)
                        .setTemperature(0.7f)
                        .setGraphOptions(graphOptions)
                        .build();

        try (LlmInferenceSession session = LlmInferenceSession.createFromOptions(llmInference, sessionOptions)) {
            session.addQueryChunk("أجب بالعربية بوضوح. حلل الصورة ثم أجب عن السؤال التالي: " + question);
            session.addImage(mpImage);
            return session.generateResponse();
        } finally {
            mpImage.close();
        }
    }

    private String buildConversationPrompt() {
        StringBuilder prompt = new StringBuilder();
        prompt.append("أنت مساعد ذكي يعمل بالكامل داخل الهاتف دون إنترنت. أجب بالعربية بشكل صحيح وواضح. ")
                .append("لا تدّع معرفة معلومات غير موجودة، واذكر عدم اليقين عند الحاجة.\n\n");
        int start = Math.max(0, conversation.size() - 8);
        for (int i = start; i < conversation.size(); i++) {
            prompt.append(conversation.get(i)).append('\n');
        }
        prompt.append("المساعد:");
        return prompt.toString();
    }

    private void clearChat() {
        conversation.clear();
        chatContainer.removeAllViews();
        selectedBitmap = null;
        selectedImageView.setImageDrawable(null);
        selectedImageView.setVisibility(View.GONE);
        addSystemMessage("بدأت محادثة جديدة. المعالجة محلية داخل الهاتف.");
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
        view.setTextColor(Color.rgb(34, 28, 23));
        view.setPadding(dp(14), dp(11), dp(14), dp(11));
        view.setTextIsSelectable(true);
        view.setGravity(Gravity.START);

        GradientDrawable background = new GradientDrawable();
        background.setCornerRadius(dp(18));
        if (system) {
            background.setColor(Color.rgb(245, 235, 218));
            background.setStroke(dp(1), Color.rgb(205, 177, 125));
        } else if (user) {
            background.setColor(Color.rgb(225, 205, 170));
        } else {
            background.setColor(Color.WHITE);
            background.setStroke(dp(1), Color.rgb(226, 216, 205));
        }
        view.setBackground(background);

        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                system ? LinearLayout.LayoutParams.MATCH_PARENT : dp(300),
                LinearLayout.LayoutParams.WRAP_CONTENT);
        params.gravity = system ? Gravity.CENTER : (user ? Gravity.END : Gravity.START);
        params.setMargins(0, dp(5), 0, dp(5));
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
        promptInput.setEnabled(enabled);
    }

    private void showError(String message) {
        busy = false;
        setControlsEnabled(true);
        statusText.setText("غير جاهز");
        addSystemMessage(message);
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private void closeModel() {
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
        return String.format(Locale.US, "%.1f %s", value, units[unit]);
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
        closeModel();
        executor.shutdownNow();
        super.onDestroy();
    }
}
