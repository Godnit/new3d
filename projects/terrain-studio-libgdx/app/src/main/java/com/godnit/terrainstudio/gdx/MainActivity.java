package com.godnit.terrainstudio.gdx;

import android.graphics.Color;
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
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;

import com.badlogic.gdx.backends.android.AndroidApplication;
import com.badlogic.gdx.backends.android.AndroidApplicationConfiguration;

public class MainActivity extends AndroidApplication {
    private TerrainStudioGame game;
    private TextView statusText;
    private TextView toolText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);

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
        game.setStatusListener(text -> runOnUiThread(() -> {
            if (statusText != null) statusText.setText(text);
        }));

        View gameView = initializeForView(game, cfg);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(90, 155, 205));
        root.addView(gameView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));

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
        bar.setPadding(dp(12), dp(5), dp(8), dp(5));
        bar.setBackground(panel(0xE51A2530, 0));

        TextView title = text("Terrain Studio X", 18, Color.WHITE);
        title.setGravity(Gravity.CENTER_VERTICAL | Gravity.LEFT);
        bar.addView(title, new LinearLayout.LayoutParams(0, dp(52), 1f));

        bar.addView(action("↶ تراجع", v -> game.undo()));
        bar.addView(action("حفظ", v -> game.save()));
        bar.addView(action("فتح", v -> game.load()));
        bar.addView(action("جديد", v -> game.newMap()));

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, dp(58));
        lp.gravity = Gravity.TOP;
        root.addView(bar, lp);
    }

    private void buildBottomBar(FrameLayout root) {
        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        scroll.setFillViewport(false);
        scroll.setBackground(panel(0xEA192632, 0));

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(6), dp(6), dp(6), dp(6));
        scroll.addView(row);

        tool(row, "كاميرا", TerrainStudioGame.Tool.CAMERA);
        tool(row, "رفع", TerrainStudioGame.Tool.RAISE);
        tool(row, "خفض", TerrainStudioGame.Tool.LOWER);
        tool(row, "تنعيم", TerrainStudioGame.Tool.SMOOTH);
        tool(row, "تسطيح", TerrainStudioGame.Tool.FLATTEN);
        tool(row, "طلاء", TerrainStudioGame.Tool.PAINT);
        tool(row, "شجرة", TerrainStudioGame.Tool.TREE);
        tool(row, "صخرة", TerrainStudioGame.Tool.ROCK);
        tool(row, "حذف", TerrainStudioGame.Tool.DELETE);

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, dp(68));
        lp.gravity = Gravity.BOTTOM;
        root.addView(scroll, lp);
    }

    private void buildSidePanel(FrameLayout root) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(12), dp(10), dp(12), dp(10));
        box.setBackground(panel(0xE922303C, dp(14)));

        toolText = text("الأداة: كاميرا", 15, Color.WHITE);
        box.addView(toolText, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));

        box.addView(text("حجم الفرشاة", 13, 0xFFE6EEF5));
        SeekBar radius = new SeekBar(this);
        radius.setMax(100); radius.setProgress(35);
        radius.setOnSeekBarChangeListener(new Seek() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                game.setBrushRadius(0.8f + progress * 0.057f);
            }
        });
        box.addView(radius, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));

        box.addView(text("قوة الفرشاة", 13, 0xFFE6EEF5));
        SeekBar strength = new SeekBar(this);
        strength.setMax(100); strength.setProgress(40);
        strength.setOnSeekBarChangeListener(new Seek() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                game.setBrushStrength(0.05f + progress * 0.0095f);
            }
        });
        box.addView(strength, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));

        box.addView(text("لون الأرض", 13, 0xFFE6EEF5));
        LinearLayout swatches = new LinearLayout(this);
        swatches.setGravity(Gravity.CENTER);
        color(swatches, 0xFF4F8738, 0.31f, 0.53f, 0.22f);
        color(swatches, 0xFF8C693E, 0.55f, 0.41f, 0.24f);
        color(swatches, 0xFFD0AD64, 0.82f, 0.68f, 0.39f);
        color(swatches, 0xFF777C80, 0.47f, 0.49f, 0.50f);
        box.addView(swatches, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(48)));

        Switch shadow = new Switch(this);
        shadow.setText("ظلال حقيقية");
        shadow.setTextColor(Color.WHITE);
        shadow.setTextSize(13);
        shadow.setChecked(true);
        shadow.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);
        shadow.setOnCheckedChangeListener((buttonView, isChecked) -> game.setShadowsEnabled(isChecked));
        box.addView(shadow, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(44)));

        TextView help = text("إصبع واحد: الأداة الحالية\nإصبعان: تحريك + تقريب", 12, 0xFFB7C8D6);
        help.setGravity(Gravity.CENTER);
        box.addView(help, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, dp(56)));

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(dp(205), dp(330));
        lp.gravity = Gravity.END | Gravity.CENTER_VERTICAL;
        lp.rightMargin = dp(8);
        root.addView(box, lp);
    }

    private void buildStatus(FrameLayout root) {
        statusText = text("جاري تشغيل المحرر...", 13, Color.WHITE);
        statusText.setGravity(Gravity.CENTER);
        statusText.setBackground(panel(0xB5000000, dp(13)));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(dp(300), dp(36));
        lp.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        lp.topMargin = dp(65);
        root.addView(statusText, lp);
    }

    private void tool(LinearLayout row, String label, TerrainStudioGame.Tool mode) {
        Button b = button(label);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(88), dp(52));
        lp.setMargins(dp(3), 0, dp(3), 0);
        row.addView(b, lp);
        b.setOnClickListener(v -> {
            game.setTool(mode);
            if (toolText != null) toolText.setText("الأداة: " + label);
        });
    }

    private Button action(String label, View.OnClickListener click) {
        Button b = button(label);
        b.setOnClickListener(click);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(88), dp(46));
        lp.setMargins(dp(2), 0, dp(2), 0);
        b.setLayoutParams(lp);
        return b;
    }

    private Button button(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setTextColor(Color.WHITE);
        b.setTextSize(13);
        b.setGravity(Gravity.CENTER);
        b.setTextDirection(View.TEXT_DIRECTION_RTL);
        b.setPadding(dp(3), 0, dp(3), 0);
        b.setBackground(panel(0xFF334A5E, dp(9)));
        return b;
    }

    private void color(LinearLayout row, int androidColor, float r, float g, float bVal) {
        Button b = new Button(this);
        GradientDrawable bg = panel(androidColor, dp(8));
        bg.setStroke(dp(2), 0xFFD3DEE7);
        b.setBackground(bg);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(38), dp(38));
        lp.setMargins(dp(3), dp(3), dp(3), dp(3));
        row.addView(b, lp);
        b.setOnClickListener(v -> game.setPaintColor(new com.badlogic.gdx.graphics.Color(r, g, bVal, 1f)));
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

    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }

    private abstract static class Seek implements SeekBar.OnSeekBarChangeListener {
        @Override public void onStartTrackingTouch(SeekBar seekBar) {}
        @Override public void onStopTrackingTouch(SeekBar seekBar) {}
    }
}
