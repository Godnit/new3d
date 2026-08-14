package com.godnit.terrainstudio.gdx;

import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;

import com.badlogic.gdx.backends.android.AndroidApplication;
import com.badlogic.gdx.backends.android.AndroidApplicationConfiguration;

public class MainActivity extends AndroidApplication {
    private static final int PANEL = 0xE51B2935;
    private static final int PANEL_SOFT = 0xD91B2935;
    private static final int BUTTON = 0xEE30485B;
    private static final int BUTTON_ACTIVE = 0xFF0B8F87;
    private static final int TEXT_MUTED = 0xFFB8C8D5;

    private TerrainStudioGame game;
    private TextView statusText;
    private TextView toolText;
    private TextView selectionText;
    private View sidePanel;
    private View bottomBar;
    private View topBar;
    private Button inspectorToggle;
    private Button chromeToggle;
    private Button activeToolButton;
    private boolean chromeHidden = false;

    private final Runnable hideStatusRunnable = new Runnable() {
        @Override public void run() {
            if (statusText != null) statusText.setVisibility(View.INVISIBLE);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                        View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);

        AndroidApplicationConfiguration cfg = new AndroidApplicationConfiguration();
        cfg.useGL30 = false;
        cfg.useImmersiveMode = true;
        cfg.useAccelerometer = false;
        cfg.useCompass = false;
        cfg.useGyroscope = false;
        cfg.disableAudio = true;
        cfg.numSamples = 0;
        cfg.depth = 16;

        game = new TerrainStudioGame();
        game.setStatusListener(text -> runOnUiThread(() -> showStatus(text)));
        game.setSelectionListener(text -> runOnUiThread(() -> {
            if (selectionText != null) selectionText.setText(text);
        }));

        View gameView = initializeForView(game, cfg);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(90, 155, 205));
        root.addView(gameView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        buildTopBar(root);
        buildBottomBar(root);
        buildSidePanel(root);
        buildStatus(root);
        setContentView(root);
    }

    private void buildTopBar(FrameLayout root) {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(7), dp(3), dp(5), dp(3));
        bar.setBackground(panel(0xE81A2733, 0));
        topBar = bar;

        TextView title = text("Terrain Studio X", 15, Color.WHITE);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
        bar.addView(title, new LinearLayout.LayoutParams(0, dp(38), 1f));

        bar.addView(action("تراجع", v -> game.undo()));
        bar.addView(action("حفظ", v -> game.save()));
        bar.addView(action("فتح", v -> game.load()));
        bar.addView(action("جديد", v -> game.newMap()));

        inspectorToggle = action("خصائص", v -> toggleInspector());
        bar.addView(inspectorToggle);

        chromeToggle = action("عرض", v -> toggleChrome());
        bar.addView(chromeToggle);

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, dp(42));
        lp.gravity = Gravity.TOP;
        root.addView(bar, lp);
    }

    private void buildBottomBar(FrameLayout root) {
        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        scroll.setFillViewport(false);
        scroll.setBackground(panel(PANEL_SOFT, 0));
        bottomBar = scroll;

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(4), dp(4), dp(4), dp(4));
        scroll.addView(row);

        Button cameraButton = tool(row, "كاميرا", TerrainStudioGame.Tool.CAMERA);
        tool(row, "تحديد", TerrainStudioGame.Tool.SELECT);
        tool(row, "رفع", TerrainStudioGame.Tool.RAISE);
        tool(row, "خفض", TerrainStudioGame.Tool.LOWER);
        tool(row, "تنعيم", TerrainStudioGame.Tool.SMOOTH);
        tool(row, "تسطيح", TerrainStudioGame.Tool.FLATTEN);
        tool(row, "خشونة", TerrainStudioGame.Tool.NOISE);
        tool(row, "طلاء", TerrainStudioGame.Tool.PAINT);
        toolbarAction(row, "مجسمات", v -> {
            showInspector();
            if (toolText != null) toolText.setText("اختر مجسمًا من المكتبة");
        });
        tool(row, "حذف", TerrainStudioGame.Tool.DELETE);

        setActiveTool(cameraButton, "كاميرا", TerrainStudioGame.Tool.CAMERA, false);

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, dp(50));
        lp.gravity = Gravity.BOTTOM;
        root.addView(scroll, lp);
    }

    private void buildSidePanel(FrameLayout root) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setVerticalScrollBarEnabled(false);
        scroll.setBackground(panel(PANEL, dp(12)));
        sidePanel = scroll;

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(9), dp(7), dp(9), dp(9));
        scroll.addView(box, new ScrollView.LayoutParams(
                ScrollView.LayoutParams.MATCH_PARENT,
                ScrollView.LayoutParams.WRAP_CONTENT));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        TextView panelTitle = text("لوحة الأدوات", 14, Color.WHITE);
        panelTitle.setTypeface(Typeface.DEFAULT_BOLD);
        header.addView(panelTitle, new LinearLayout.LayoutParams(0, dp(32), 1f));
        Button close = button("×");
        close.setTextSize(18);
        close.setOnClickListener(v -> sidePanel.setVisibility(View.INVISIBLE));
        header.addView(close, new LinearLayout.LayoutParams(dp(32), dp(30)));
        box.addView(header);

        toolText = text("الأداة: كاميرا", 12, TEXT_MUTED);
        box.addView(toolText, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(26)));

        addSection(box, "الفرشاة");
        box.addView(text("حجم الفرشاة", 11, 0xFFE7EEF4));
        SeekBar radius = new SeekBar(this);
        radius.setMax(100);
        radius.setProgress(35);
        radius.setOnSeekBarChangeListener(new Seek() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                game.setBrushRadius(0.8f + progress * 0.057f);
            }
        });
        box.addView(radius, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(32)));

        box.addView(text("قوة الفرشاة", 11, 0xFFE7EEF4));
        SeekBar strength = new SeekBar(this);
        strength.setMax(100);
        strength.setProgress(40);
        strength.setOnSeekBarChangeListener(new Seek() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                game.setBrushStrength(0.05f + progress * 0.0095f);
            }
        });
        box.addView(strength, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(32)));

        box.addView(text("لون الأرض", 11, 0xFFE7EEF4));
        HorizontalScrollView colorScroll = new HorizontalScrollView(this);
        colorScroll.setHorizontalScrollBarEnabled(false);
        LinearLayout swatches = new LinearLayout(this);
        swatches.setOrientation(LinearLayout.HORIZONTAL);
        swatches.setGravity(Gravity.CENTER_VERTICAL);
        color(swatches, 0xFF4F8738, 0.31f, 0.53f, 0.22f);
        color(swatches, 0xFF315F2F, 0.19f, 0.37f, 0.18f);
        color(swatches, 0xFF8C693E, 0.55f, 0.41f, 0.24f);
        color(swatches, 0xFFD0AD64, 0.82f, 0.68f, 0.39f);
        color(swatches, 0xFF777C80, 0.47f, 0.49f, 0.50f);
        color(swatches, 0xFFE6ECEF, 0.90f, 0.93f, 0.94f);
        colorScroll.addView(swatches);
        box.addView(colorScroll, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(42)));

        addSection(box, "مكتبة المجسمات");
        LinearLayout assets1 = compactRow();
        asset(assets1, "شجرة", TerrainStudioGame.Tool.TREE);
        asset(assets1, "صخرة", TerrainStudioGame.Tool.ROCK);
        asset(assets1, "شجيرة", TerrainStudioGame.Tool.BUSH);
        box.addView(assets1);

        LinearLayout assets2 = compactRow();
        asset(assets2, "صندوق", TerrainStudioGame.Tool.CRATE);
        asset(assets2, "عمود", TerrainStudioGame.Tool.PILLAR);
        Button selectAsset = miniButton("تحديد");
        selectAsset.setOnClickListener(v -> {
            setActiveTool(null, "تحديد", TerrainStudioGame.Tool.SELECT, true);
            sidePanel.setVisibility(View.INVISIBLE);
        });
        assets2.addView(selectAsset, miniParams());
        box.addView(assets2);

        addSection(box, "العنصر المحدد");
        selectionText = text("لا يوجد مجسم محدد", 11, 0xFFF0F5F8);
        selectionText.setGravity(Gravity.CENTER);
        selectionText.setBackground(panel(0x66344858, dp(8)));
        selectionText.setPadding(dp(5), dp(4), dp(5), dp(4));
        box.addView(selectionText, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(42)));

        LinearLayout move = compactRow();
        mini(move, "يسار", v -> game.nudgeSelected(-0.8f, 0f));
        mini(move, "أمام", v -> game.nudgeSelected(0f, 0.8f));
        mini(move, "خلف", v -> game.nudgeSelected(0f, -0.8f));
        mini(move, "يمين", v -> game.nudgeSelected(0.8f, 0f));
        box.addView(move);

        LinearLayout transform = compactRow();
        mini(transform, "أعلى", v -> game.raiseSelected(0.35f));
        mini(transform, "أسفل", v -> game.raiseSelected(-0.35f));
        mini(transform, "-15°", v -> game.rotateSelected(-15f));
        mini(transform, "+15°", v -> game.rotateSelected(15f));
        box.addView(transform);

        LinearLayout scale = compactRow();
        mini(scale, "حجم -", v -> game.scaleSelected(0.88f));
        mini(scale, "حجم +", v -> game.scaleSelected(1.14f));
        mini(scale, "تركيز", v -> game.focusSelected());
        mini(scale, "إعادة", v -> game.resetSelectedTransform());
        box.addView(scale);

        LinearLayout objectOps = compactRow();
        mini(objectOps, "نسخ", v -> game.duplicateSelected());
        mini(objectOps, "حذف", v -> game.deleteSelected());
        mini(objectOps, "إلغاء", v -> game.clearSelection());
        box.addView(objectOps);

        addSection(box, "المشهد");
        Switch shadow = new Switch(this);
        shadow.setText("ظلال حقيقية");
        shadow.setTextColor(Color.WHITE);
        shadow.setTextSize(11);
        shadow.setChecked(true);
        shadow.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);
        shadow.setOnCheckedChangeListener((buttonView, isChecked) -> game.setShadowsEnabled(isChecked));
        box.addView(shadow, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));

        Button resetCamera = wideButton("إعادة الكاميرا");
        resetCamera.setOnClickListener(v -> game.resetView());
        box.addView(resetCamera, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(34)));

        TextView help = text("إصبع واحد: الأداة الحالية\nإصبعان: تحريك وتقريب\nفي وضع التحديد: اسحب المجسم فوق الأرض", 10, TEXT_MUTED);
        help.setGravity(Gravity.CENTER);
        help.setPadding(dp(3), dp(5), dp(3), dp(2));
        box.addView(help, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(54)));

        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        int panelWidth = Math.max(210, Math.min(dp(190), Math.round(screenWidth * 0.28f)));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                panelWidth, FrameLayout.LayoutParams.MATCH_PARENT);
        lp.gravity = Gravity.END | Gravity.TOP;
        lp.topMargin = dp(46);
        lp.bottomMargin = dp(54);
        lp.rightMargin = dp(5);
        root.addView(scroll, lp);
        scroll.setVisibility(View.INVISIBLE);
    }

    private void buildStatus(FrameLayout root) {
        statusText = text("", 11, Color.WHITE);
        statusText.setGravity(Gravity.CENTER);
        statusText.setBackground(panel(0xA6000000, dp(10)));
        statusText.setVisibility(View.INVISIBLE);

        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        int width = Math.min(dp(210), Math.round(screenWidth * 0.38f));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(width, dp(27));
        lp.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        lp.topMargin = dp(47);
        root.addView(statusText, lp);
    }

    private void showStatus(String text) {
        if (statusText == null) return;
        statusText.removeCallbacks(hideStatusRunnable);
        statusText.setText(text);
        statusText.setVisibility(View.VISIBLE);
        statusText.postDelayed(hideStatusRunnable, 1450);
    }

    private void toggleInspector() {
        if (sidePanel == null) return;
        sidePanel.setVisibility(sidePanel.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
    }

    private void showInspector() {
        if (sidePanel != null) sidePanel.setVisibility(View.VISIBLE);
    }

    private void toggleChrome() {
        chromeHidden = !chromeHidden;
        if (bottomBar != null) bottomBar.setVisibility(chromeHidden ? View.INVISIBLE : View.VISIBLE);
        if (chromeHidden && sidePanel != null) sidePanel.setVisibility(View.INVISIBLE);
        if (chromeToggle != null) chromeToggle.setText(chromeHidden ? "تحرير" : "عرض");
        showStatus(chromeHidden ? "وضع العرض: الأدوات مخفية" : "وضع التحرير");
    }

    private Button tool(LinearLayout row, String label, TerrainStudioGame.Tool mode) {
        Button b = button(label);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(toolbarCellWidth(), dp(40));
        lp.setMargins(dp(2), 0, dp(2), 0);
        row.addView(b, lp);
        b.setOnClickListener(v -> setActiveTool(b, label, mode, true));
        return b;
    }

    private void toolbarAction(LinearLayout row, String label, View.OnClickListener click) {
        Button b = button(label);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(toolbarCellWidth(), dp(40));
        lp.setMargins(dp(2), 0, dp(2), 0);
        row.addView(b, lp);
        b.setOnClickListener(click);
    }

    private void setActiveTool(Button source, String label, TerrainStudioGame.Tool mode, boolean notifyGame) {
        if (activeToolButton != null) activeToolButton.setBackground(panel(BUTTON, dp(8)));
        activeToolButton = source;
        if (source != null) source.setBackground(panel(BUTTON_ACTIVE, dp(8)));
        if (toolText != null) toolText.setText("الأداة: " + label);
        if (notifyGame) game.setTool(mode);
    }

    private void asset(LinearLayout row, String label, TerrainStudioGame.Tool mode) {
        Button b = miniButton(label);
        row.addView(b, miniParams());
        b.setOnClickListener(v -> {
            setActiveTool(null, label, mode, true);
            sidePanel.setVisibility(View.INVISIBLE);
        });
    }

    private void mini(LinearLayout row, String label, View.OnClickListener click) {
        Button b = miniButton(label);
        b.setOnClickListener(click);
        row.addView(b, miniParams());
    }

    private LinearLayout compactRow() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER);
        row.setPadding(0, dp(2), 0, dp(2));
        return row;
    }

    private LinearLayout.LayoutParams miniParams() {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(34), 1f);
        lp.setMargins(dp(1), 0, dp(1), 0);
        return lp;
    }

    private Button miniButton(String label) {
        Button b = button(label);
        b.setTextSize(10);
        b.setPadding(dp(1), 0, dp(1), 0);
        b.setBackground(panel(0xEE354E61, dp(7)));
        return b;
    }

    private Button wideButton(String label) {
        Button b = button(label);
        b.setTextSize(11);
        b.setBackground(panel(0xEE354E61, dp(8)));
        return b;
    }

    private Button action(String label, View.OnClickListener click) {
        Button b = button(label);
        b.setTextSize(10.5f);
        b.setOnClickListener(click);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(topActionWidth(), dp(34));
        lp.setMargins(dp(1), 0, dp(1), 0);
        b.setLayoutParams(lp);
        return b;
    }

    private Button button(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextColor(Color.WHITE);
        b.setTextSize(11);
        b.setGravity(Gravity.CENTER);
        b.setTextDirection(View.TEXT_DIRECTION_RTL);
        b.setPadding(dp(2), 0, dp(2), 0);
        b.setMinHeight(0);
        b.setMinWidth(0);
        b.setBackground(panel(BUTTON, dp(8)));
        return b;
    }

    private void color(LinearLayout row, int androidColor, float r, float g, float bVal) {
        Button b = new Button(this);
        b.setMinWidth(0);
        b.setMinHeight(0);
        GradientDrawable bg = panel(androidColor, dp(7));
        bg.setStroke(dp(1), 0xFFD3DEE7);
        b.setBackground(bg);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(31), dp(31));
        lp.setMargins(dp(2), dp(2), dp(2), dp(2));
        row.addView(b, lp);
        b.setOnClickListener(v -> game.setPaintColor(new com.badlogic.gdx.graphics.Color(r, g, bVal, 1f)));
    }

    private void addSection(LinearLayout box, String label) {
        TextView t = text(label, 12, 0xFF9EE7E1);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setPadding(0, dp(7), 0, dp(3));
        box.addView(t, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(30)));
    }

    private TextView text(String value, float size, int color) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(size);
        t.setTextColor(color);
        t.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);
        t.setTextDirection(View.TEXT_DIRECTION_RTL);
        return t;
    }

    private GradientDrawable panel(int color, int radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(radius);
        return d;
    }

    private int toolbarCellWidth() {
        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        return Math.min(dp(66), Math.max(dp(52), screenWidth / 9));
    }

    private int topActionWidth() {
        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        return Math.min(dp(56), Math.max(dp(42), screenWidth / 10));
    }

    private int dp(int n) {
        return Math.round(n * getResources().getDisplayMetrics().density);
    }

    private abstract static class Seek implements SeekBar.OnSeekBarChangeListener {
        @Override public void onStartTrackingTouch(SeekBar seekBar) {}
        @Override public void onStopTrackingTouch(SeekBar seekBar) {}
    }
}
