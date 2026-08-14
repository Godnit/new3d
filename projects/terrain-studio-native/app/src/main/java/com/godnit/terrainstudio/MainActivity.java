package com.godnit.terrainstudio;

import android.app.Activity;
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
import android.widget.TextView;

public class MainActivity extends Activity implements TerrainGLView.StatusListener {
    private TerrainGLView glView;
    private TextView statusText;
    private TextView toolText;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN |
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(91, 158, 207));
        setContentView(root);

        glView = new TerrainGLView(this);
        glView.setStatusListener(this);
        root.addView(glView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));

        buildTopBar(root);
        buildBottomTools(root);
        buildSidePanel(root);
        buildStatus(root);
    }

    private void buildTopBar(FrameLayout root) {
        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.setPadding(dp(12), dp(6), dp(8), dp(6));
        top.setBackground(makePanel(0xDD18222E, 0));

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, dp(58));
        lp.gravity = Gravity.TOP;
        root.addView(top, lp);

        TextView title = new TextView(this);
        title.setText("Terrain Studio");
        title.setTextColor(Color.WHITE);
        title.setTextSize(18);
        title.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams titleLp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f);
        top.addView(title, titleLp);

        top.addView(makeActionButton("تراجع", v -> glView.undo()));
        top.addView(makeActionButton("حفظ", v -> glView.saveMap()));
        top.addView(makeActionButton("فتح", v -> glView.loadMap()));
        top.addView(makeActionButton("جديد", v -> glView.newMap()));
    }

    private void buildBottomTools(FrameLayout root) {
        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        scroll.setFillViewport(true);
        scroll.setBackground(makePanel(0xE51B2734, 0));

        LinearLayout tools = new LinearLayout(this);
        tools.setOrientation(LinearLayout.HORIZONTAL);
        tools.setGravity(Gravity.CENTER);
        tools.setPadding(dp(6), dp(7), dp(6), dp(7));
        scroll.addView(tools, new HorizontalScrollView.LayoutParams(
                HorizontalScrollView.LayoutParams.WRAP_CONTENT,
                HorizontalScrollView.LayoutParams.MATCH_PARENT));

        addTool(tools, "كاميرا", TerrainGLView.MODE_CAMERA);
        addTool(tools, "رفع", TerrainGLView.MODE_RAISE);
        addTool(tools, "خفض", TerrainGLView.MODE_LOWER);
        addTool(tools, "تنعيم", TerrainGLView.MODE_SMOOTH);
        addTool(tools, "طلاء", TerrainGLView.MODE_PAINT);
        addTool(tools, "شجر", TerrainGLView.MODE_TREE);
        addTool(tools, "صخر", TerrainGLView.MODE_ROCK);
        addTool(tools, "حذف", TerrainGLView.MODE_ERASE);

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, dp(68));
        lp.gravity = Gravity.BOTTOM;
        root.addView(scroll, lp);
    }

    private void addTool(LinearLayout parent, String label, int mode) {
        Button b = makeButton(label);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(92), dp(52));
        lp.setMargins(dp(3), 0, dp(3), 0);
        b.setLayoutParams(lp);
        b.setOnClickListener(v -> {
            glView.setToolMode(mode);
            toolText.setText("الأداة: " + label);
        });
        parent.addView(b);
    }

    private void buildSidePanel(FrameLayout root) {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(12), dp(10), dp(12), dp(10));
        panel.setGravity(Gravity.TOP);
        panel.setBackground(makePanel(0xE9222D3A, dp(12)));

        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(dp(210), dp(330));
        lp.gravity = Gravity.END | Gravity.CENTER_VERTICAL;
        lp.rightMargin = dp(10);
        root.addView(panel, lp);

        toolText = label("الأداة: كاميرا", 16, Color.WHITE);
        panel.addView(toolText, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));

        panel.addView(label("حجم الفرشاة", 14, 0xFFE7EEF5));
        SeekBar radius = new SeekBar(this);
        radius.setMax(100);
        radius.setProgress(40);
        radius.setOnSeekBarChangeListener(new SimpleSeek() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                glView.setBrushRadius(0.8f + (progress / 100f) * 5.2f);
            }
        });
        panel.addView(radius, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));

        panel.addView(label("قوة الفرشاة", 14, 0xFFE7EEF5));
        SeekBar strength = new SeekBar(this);
        strength.setMax(100);
        strength.setProgress(40);
        strength.setOnSeekBarChangeListener(new SimpleSeek() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                glView.setBrushStrength(0.05f + (progress / 100f) * 0.95f);
            }
        });
        panel.addView(strength, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(38)));

        panel.addView(label("لون الأرض", 14, 0xFFE7EEF5));
        LinearLayout colors = new LinearLayout(this);
        colors.setOrientation(LinearLayout.HORIZONTAL);
        colors.setGravity(Gravity.CENTER);
        addColor(colors, 0xFF4F823B);
        addColor(colors, 0xFF8A6A43);
        addColor(colors, 0xFFD4B36A);
        addColor(colors, 0xFF777A78);
        panel.addView(colors, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(46)));

        TextView help = label("إصبع واحد: تعديل أو دوران\nإصبعان: تقريب وإبعاد", 13, 0xFFB9C9D8);
        help.setGravity(Gravity.CENTER);
        panel.addView(help, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, dp(64)));
    }

    private void addColor(LinearLayout parent, int color) {
        Button b = new Button(this);
        b.setText("");
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(color);
        bg.setCornerRadius(dp(9));
        bg.setStroke(dp(2), 0xFFCBD5DF);
        b.setBackground(bg);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(38), dp(38));
        lp.setMargins(dp(3), dp(3), dp(3), dp(3));
        parent.addView(b, lp);
        b.setOnClickListener(v -> glView.setPaintColor(color));
    }

    private void buildStatus(FrameLayout root) {
        statusText = label("جاهز", 14, Color.WHITE);
        statusText.setGravity(Gravity.CENTER);
        statusText.setBackground(makePanel(0xB9000000, dp(14)));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(dp(330), dp(38));
        lp.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        lp.topMargin = dp(66);
        root.addView(statusText, lp);
    }

    private Button makeActionButton(String text, View.OnClickListener listener) {
        Button b = makeButton(text);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(86), dp(46));
        lp.setMargins(dp(3), 0, dp(3), 0);
        b.setLayoutParams(lp);
        b.setOnClickListener(listener);
        return b;
    }

    private Button makeButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextSize(14);
        b.setTextColor(Color.WHITE);
        b.setAllCaps(false);
        b.setGravity(Gravity.CENTER);
        b.setPadding(dp(4), 0, dp(4), 0);
        b.setTextDirection(View.TEXT_DIRECTION_RTL);
        b.setBackground(makePanel(0xFF33485B, dp(9)));
        return b;
    }

    private TextView label(String text, float size, int color) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextSize(size);
        t.setTextColor(color);
        t.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);
        t.setTextDirection(View.TEXT_DIRECTION_RTL);
        return t;
    }

    private GradientDrawable makePanel(int color, int radiusPx) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(radiusPx);
        return d;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override
    public void onStatus(String text) {
        runOnUiThread(() -> statusText.setText(text));
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (glView != null) glView.onResume();
    }

    @Override
    protected void onPause() {
        if (glView != null) glView.onPause();
        super.onPause();
    }

    private abstract static class SimpleSeek implements SeekBar.OnSeekBarChangeListener {
        @Override public void onStartTrackingTouch(SeekBar seekBar) {}
        @Override public void onStopTrackingTouch(SeekBar seekBar) {}
    }
}
