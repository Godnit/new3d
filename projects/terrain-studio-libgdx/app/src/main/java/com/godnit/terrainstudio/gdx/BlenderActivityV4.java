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
import android.widget.LinearLayout;
import android.widget.PopupWindow;
import android.widget.TextView;

import com.badlogic.gdx.backends.android.AndroidApplication;
import com.badlogic.gdx.backends.android.AndroidApplicationConfiguration;

public class BlenderActivityV4 extends AndroidApplication {
    private static final int PANEL = 0xE81C232A;
    private static final int BTN = 0xEE303A44;
    private static final int ACTIVE = 0xFF176A87;
    private MiniBlenderGameV4 game;
    private TextView status;
    private TextView selection;
    private Button activeTool;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION);

        AndroidApplicationConfiguration cfg = new AndroidApplicationConfiguration();
        cfg.useGL30 = false;
        cfg.useImmersiveMode = true;
        cfg.useAccelerometer = false;
        cfg.useCompass = false;
        cfg.useGyroscope = false;
        cfg.disableAudio = true;
        cfg.depth = 16;
        cfg.numSamples = 0;

        game = new MiniBlenderGameV4();
        game.setUiListener(new MiniBlenderGameV4.UiListener() {
            @Override public void onStatus(String text) { runOnUiThread(() -> showStatus(text)); }
            @Override public void onSelection(String text) { runOnUiThread(() -> { if(selection!=null) selection.setText(text); }); }
        });

        View gl = initializeForView(game, cfg);
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(27,31,35));
        root.addView(gl, new FrameLayout.LayoutParams(-1,-1));
        buildTop(root);
        buildLeftTools(root);
        buildBottomHint(root);
        buildStatus(root);
        setContentView(root);
    }

    private void buildTop(FrameLayout root) {
        LinearLayout bar = new LinearLayout(this);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(8),dp(2),dp(5),dp(2));
        bar.setBackground(bg(PANEL,0));

        TextView title = text("Mini 3D",14,Color.WHITE);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setGravity(Gravity.CENTER_VERTICAL|Gravity.LEFT);
        bar.addView(title,new LinearLayout.LayoutParams(dp(82),dp(36)));

        selection = text("لا يوجد مجسم محدد",10,0xFFC7D1D8);
        selection.setGravity(Gravity.CENTER);
        bar.addView(selection,new LinearLayout.LayoutParams(0,dp(36),1f));

        bar.addView(topButton("↶",v->game.undo()));
        bar.addView(topButton("حفظ",v->game.save()));
        bar.addView(topButton("فتح",v->game.load()));
        bar.addView(topButton("جديد",v->game.newScene()));
        bar.addView(topButton("◎",v->game.focusSelected()));

        FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(-1,dp(40));
        lp.gravity=Gravity.TOP;
        root.addView(bar,lp);
    }

    private void buildLeftTools(FrameLayout root) {
        LinearLayout rail=new LinearLayout(this);
        rail.setOrientation(LinearLayout.VERTICAL);
        rail.setGravity(Gravity.TOP|Gravity.CENTER_HORIZONTAL);
        rail.setPadding(dp(3),dp(4),dp(3),dp(4));
        rail.setBackground(bg(0xDA1C232A,dp(9)));

        Button add=toolButton("＋\nإضافة");
        add.setOnClickListener(v->showAddMenu(add));
        rail.addView(add,toolLp());

        Button move=toolButton("⇆\nتحريك");
        move.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.MOVE);activate(move);});
        rail.addView(move,toolLp());

        Button rotate=toolButton("⟳\nتدوير");
        rotate.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.ROTATE);activate(rotate);});
        rail.addView(rotate,toolLp());

        Button scale=toolButton("⤢\nحجم");
        scale.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.SCALE);activate(scale);});
        rail.addView(scale,toolLp());

        Button duplicate=toolButton("⧉\nنسخ");
        duplicate.setOnClickListener(v->game.duplicateSelected());
        rail.addView(duplicate,toolLp());

        Button delete=toolButton("⌫\nحذف");
        delete.setOnClickListener(v->game.deleteSelected());
        rail.addView(delete,toolLp());

        activate(move);
        FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(dp(58),FrameLayout.LayoutParams.WRAP_CONTENT);
        lp.gravity=Gravity.LEFT|Gravity.CENTER_VERTICAL;
        lp.leftMargin=dp(5);
        root.addView(rail,lp);
    }

    private void showAddMenu(View anchor) {
        LinearLayout box=new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(5),dp(5),dp(5),dp(5));
        box.setBackground(bg(0xF51E2831,dp(10)));

        TextView head=text("إضافة مجسم",12,0xFF93D8F4);
        head.setTypeface(Typeface.DEFAULT_BOLD);
        head.setGravity(Gravity.CENTER);
        box.addView(head,new LinearLayout.LayoutParams(dp(158),dp(30)));

        final PopupWindow[] holder=new PopupWindow[1];
        addItem(box,"▭  أرض",MiniBlenderGameV4.GROUND,holder);
        addItem(box,"■  مكعب",MiniBlenderGameV4.CUBE,holder);
        addItem(box,"●  كرة",MiniBlenderGameV4.SPHERE,holder);
        addItem(box,"▥  أسطوانة",MiniBlenderGameV4.CYLINDER,holder);
        addItem(box,"▲  مخروط",MiniBlenderGameV4.CONE,holder);
        addItem(box,"◆  هرم",MiniBlenderGameV4.PYRAMID,holder);
        addItem(box,"♠  شجرة",MiniBlenderGameV4.TREE,holder);
        addItem(box,"⬟  صخرة",MiniBlenderGameV4.ROCK,holder);
        addItem(box,"♣  شجيرة",MiniBlenderGameV4.BUSH,holder);

        PopupWindow pop=new PopupWindow(box,dp(168),FrameLayout.LayoutParams.WRAP_CONTENT,true);
        holder[0]=pop;
        pop.setOutsideTouchable(true);
        pop.setBackgroundDrawable(bg(0x001E2831,dp(10)));
        pop.setElevation(dp(8));
        pop.showAsDropDown(anchor,dp(4),-dp(62));
    }

    private void addItem(LinearLayout box,String label,int type,PopupWindow[] holder){
        Button b=new Button(this);
        b.setText(label); b.setAllCaps(false); b.setTextColor(Color.WHITE); b.setTextSize(11); b.setGravity(Gravity.CENTER_VERTICAL|Gravity.RIGHT);
        b.setTextDirection(View.TEXT_DIRECTION_RTL); b.setPadding(dp(9),0,dp(9),0); b.setMinHeight(0); b.setMinWidth(0); b.setBackground(bg(BTN,dp(6)));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(36));lp.setMargins(0,dp(1),0,dp(1));box.addView(b,lp);
        b.setOnClickListener(v->{game.addObject(type);if(holder[0]!=null)holder[0].dismiss();});
    }

    private void buildBottomHint(FrameLayout root){
        TextView hint=text("اضغط مجسمًا = تحديد مباشر   •   اسحب المجسم = تعديل حر   •   اسحب المحور الملون = تعديل دقيق   •   مساحة فارغة أو إصبعان = تدوير الكاميرا   •   قرّب/بعّد بإصبعين",9,0xFFD4DCE2);
        hint.setGravity(Gravity.CENTER);
        hint.setBackground(bg(0xB51C232A,0));
        FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(-1,dp(25));lp.gravity=Gravity.BOTTOM;root.addView(hint,lp);
    }

    private void buildStatus(FrameLayout root){
        status=text("",10,Color.WHITE);status.setGravity(Gravity.CENTER);status.setVisibility(View.INVISIBLE);status.setBackground(bg(0xC9000000,dp(9)));
        FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(dp(300),dp(28));lp.gravity=Gravity.TOP|Gravity.CENTER_HORIZONTAL;lp.topMargin=dp(44);root.addView(status,lp);
    }

    private void showStatus(String s){if(status==null)return;status.setText(s);status.setVisibility(View.VISIBLE);status.removeCallbacks(hideStatus);status.postDelayed(hideStatus,1350);}
    private final Runnable hideStatus=()->{if(status!=null)status.setVisibility(View.INVISIBLE);};

    private Button toolButton(String label){Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextColor(Color.WHITE);b.setTextSize(10);b.setGravity(Gravity.CENTER);b.setPadding(0,0,0,0);b.setMinWidth(0);b.setMinHeight(0);b.setBackground(bg(BTN,dp(8)));return b;}
    private LinearLayout.LayoutParams toolLp(){LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(50),dp(48));lp.setMargins(0,dp(2),0,dp(2));return lp;}
    private void activate(Button b){if(activeTool!=null)activeTool.setBackground(bg(BTN,dp(8)));activeTool=b;if(b!=null)b.setBackground(bg(ACTIVE,dp(8)));}

    private Button topButton(String label,View.OnClickListener click){Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextColor(Color.WHITE);b.setTextSize(10);b.setGravity(Gravity.CENTER);b.setPadding(dp(2),0,dp(2),0);b.setMinWidth(0);b.setMinHeight(0);b.setBackground(bg(BTN,dp(7)));b.setOnClickListener(click);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(54),dp(32));lp.setMargins(dp(1),0,dp(1),0);b.setLayoutParams(lp);return b;}
    private TextView text(String s,float size,int color){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);t.setTextDirection(View.TEXT_DIRECTION_RTL);t.setGravity(Gravity.CENTER_VERTICAL|Gravity.RIGHT);return t;}
    private GradientDrawable bg(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(radius);return d;}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}
