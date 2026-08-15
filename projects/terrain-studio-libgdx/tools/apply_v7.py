from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
engine_path = ROOT / 'app/src/main/java/com/godnit/terrainstudio/gdx/MiniBlenderGameV4.java'
activity_path = ROOT / 'app/src/main/java/com/godnit/terrainstudio/gdx/BlenderActivityV4.java'
build_path = ROOT / 'app/build.gradle'


def must_replace(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'missing patch target: {label}')
    return text.replace(old, new, 1)


def must_sub(text, pattern, repl, label):
    out, n = re.subn(pattern, repl, text, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError(f'patch regex failed: {label} ({n})')
    return out

s = engine_path.read_text(encoding='utf-8')

# Additional interaction state.
s = must_replace(s,
'''    private float rotateLastScreenAngle = 0f;''',
'''    private float rotateLastScreenAngle = 0f;
    private boolean pendingEmptyDrag = false;
    private float pendingDownX = 0f, pendingDownY = 0f;
    private static final float DRAG_START_PX = 12f;''', 'v7 gesture state')

# More persistent Blender-style grid.
s = must_sub(s,
    r'''    private void buildGrid\(\) \{.*?\n    \}\n\n    private void buildGizmos''',
'''    private void buildGrid() {
        long a = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;
        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        Material minor = mat(0.18f, 0.195f, 0.215f);
        Material major = mat(0.30f, 0.32f, 0.35f);
        Material xAxis = mat(0.78f, 0.10f, 0.09f);
        Material zAxis = mat(0.08f, 0.28f, 0.82f);

        // Fine grid near the origin.
        int fine = 160;
        for (int i = -fine; i <= fine; i++) {
            if (i == 0 || i % 10 == 0) continue;
            MeshPartBuilder p1 = mb.part("fgx" + i, GL20.GL_TRIANGLES, a, minor);
            p1.setVertexTransform(new Matrix4().setToTranslation(0, -0.08f, i));
            p1.box(fine * 2f, 0.012f, 0.012f);
            MeshPartBuilder p2 = mb.part("fgz" + i, GL20.GL_TRIANGLES, a, minor);
            p2.setVertexTransform(new Matrix4().setToTranslation(i, -0.08f, 0));
            p2.box(0.012f, 0.012f, fine * 2f);
        }

        // Major grid extends very far, like Blender.
        int far = 5000;
        for (int i = -far; i <= far; i += 50) {
            if (i == 0) continue;
            MeshPartBuilder p1 = mb.part("mgx" + i, GL20.GL_TRIANGLES, a, major);
            p1.setVertexTransform(new Matrix4().setToTranslation(0, -0.085f, i));
            p1.box(far * 2f, 0.016f, 0.040f);
            MeshPartBuilder p2 = mb.part("mgz" + i, GL20.GL_TRIANGLES, a, major);
            p2.setVertexTransform(new Matrix4().setToTranslation(i, -0.085f, 0));
            p2.box(0.040f, 0.016f, far * 2f);
        }

        MeshPartBuilder x = mb.part("worldX", GL20.GL_TRIANGLES, a, xAxis);
        x.setVertexTransform(new Matrix4().setToTranslation(0, -0.09f, 0));
        x.box(12000f, 0.025f, 0.060f);
        MeshPartBuilder z = mb.part("worldZ", GL20.GL_TRIANGLES, a, zAxis);
        z.setVertexTransform(new Matrix4().setToTranslation(0, -0.09f, 0));
        z.box(0.060f, 0.025f, 12000f);
        gridModel = mb.end();
        gridInstance = new ModelInstance(gridModel);
    }

    private void buildGizmos''', 'v7 grid')

# Keep grid within clipping range even with huge zoom.
s = must_replace(s,
'''        camera.far = Math.max(5000f, Math.max(distance * 500f, selectedScale * 600f));''',
'''        camera.far = Math.max(20000f, Math.max(distance * 800f, selectedScale * 800f));''', 'v7 far clip')

# Easier gizmo hit targets.
s = s.replace('Axis best=Axis.NONE; float bestD=52f;', 'Axis best=Axis.NONE; float bestD=64f;', 1)
s = s.replace('Axis best=Axis.NONE; float bestD=48f;', 'Axis best=Axis.NONE; float bestD=60f;', 1)

# Flip axis rotation sign from V6: screen angular direction follows the visible arc naturally.
s = must_replace(s,
'''        float facing=av.dot(camera.direction);
        float sign=facing<0f?1f:-1f;
        if(Math.abs(facing)<0.04f)sign=1f;
        return delta*MathUtils.radiansToDegrees*sign;''',
'''        float facing=av.dot(camera.direction);
        float sign=facing<0f?-1f:1f;
        if(Math.abs(facing)<0.04f) sign = 1f;
        return delta*MathUtils.radiansToDegrees*sign;''', 'v7 rotation sign')

# Free transform: stronger and simpler; no dependence on clicking the model once selection exists.
s = must_replace(s,
'''            if(tool==Tool.MOVE){ Vector3 right=new Vector3(camera.direction).crs(Vector3.Y).nor(); Vector3 up=new Vector3(right).crs(camera.direction).nor(); float k=distance*.0027f; d.x+=right.x*dx*k+up.x*(-dy)*k;d.y+=right.y*dx*k+up.y*(-dy)*k;d.z+=right.z*dx*k+up.z*(-dy)*k; }
            else if(tool==Tool.SCALE){float f=(float)Math.exp((dx-dy)*.0075f);d.sx=clampScale(d.sx*f);d.sy=clampScale(d.sy*f);d.sz=clampScale(d.sz*f);}
            else if(tool==Tool.ROTATE){d.ry+=dx*.32f;d.rx+=dy*.32f;}''',
'''            if(tool==Tool.MOVE){
                Vector3 right=new Vector3(camera.direction).crs(Vector3.Y).nor();
                Vector3 up=new Vector3(right).crs(camera.direction).nor();
                float k=Math.max(.00005f,distance*.0033f);
                d.x+=right.x*dx*k+up.x*(-dy)*k;
                d.y+=right.y*dx*k+up.y*(-dy)*k;
                d.z+=right.z*dx*k+up.z*(-dy)*k;
            }
            else if(tool==Tool.SCALE){
                float f=(float)Math.exp((dx-dy)*.0090f);
                d.sx=clampScale(d.sx*f); d.sy=clampScale(d.sy*f); d.sz=clampScale(d.sz*f);
            }
            else if(tool==Tool.ROTATE){
                d.ry-=dx*.36f;
                d.rx+=dy*.36f;
            }''', 'v7 free transforms')

# More responsive axis scaling.
s = must_replace(s,
'''            float along=axisScreenPixelDelta(dragAxis,dx,dy,d); float f=(float)Math.exp(along*.0085f);''',
'''            float along=axisScreenPixelDelta(dragAxis,dx,dy,d); float f=(float)Math.exp(along*.0120f);''', 'v7 axis scale')

# Better sculpt sensitivity, still safe on all primitives.
s = must_replace(s,
'''        float worldPerPixel=Math.max(.00008f,distance*.0022f);''',
'''        float worldPerPixel=Math.max(.00012f,distance*.0036f);''', 'v7 sculpt strength')

# Replace touch handler with pending-empty-drag logic. A tap on empty deselects; dragging empty transforms selected.
s = must_sub(s,
    r'''    private class EditorInput extends InputAdapter \{.*?\n    \}\n\n    private void status''',
'''    private class EditorInput extends InputAdapter {
        @Override public boolean touchDown(int x,int y,int pointer,int button){
            if(Gdx.input.isTouched(1)){
                if(hasSelection()){ twoFingerActive=true; transforming=false; orbiting=false; pendingEmptyDrag=false; return true; }
                initTwoFinger(); return true;
            }
            if(ignoreFirstSingleAfterPinch){ lastX=x; lastY=y; ignoreFirstSingleAfterPinch=false; return true; }

            lastX=x; lastY=y; transforming=false; orbiting=false; pendingEmptyDrag=false; sculptAxis=Axis.NONE;

            // Gizmo always has first priority when an object is selected.
            if(hasSelection() && tool!=Tool.PAINT && tool!=Tool.SCULPT){
                Axis h=hitAxis(x,y);
                if(h!=Axis.NONE){ beginTransform(h,x,y); return true; }
            }

            int obj=pickObject(x,y);
            if(obj>=0){
                selected=obj; updatePivotFromSelection(); emitSelection();
                if(tool==Tool.PAINT){ paintObject(obj); return true; }
                if(tool==Tool.SCULPT){ beginSculpt(obj,x,y); return true; }
                beginTransform(Axis.FREE,x,y); return true;
            }

            // Selected object + empty workspace: wait to see if this is a drag or a tap.
            if(hasSelection() && tool!=Tool.PAINT && tool!=Tool.SCULPT){
                pendingEmptyDrag=true;
                pendingDownX=x; pendingDownY=y;
                return true;
            }

            // No selection: camera may orbit immediately.
            selected=-1; emitSelection(); pivot.set(0,0.8f,0); orbiting=true; return true;
        }

        @Override public boolean touchDragged(int x,int y,int pointer){
            if(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1)){
                if(hasSelection()) return true;
                if(!twoFingerActive) initTwoFinger(); else handleTwoFinger();
                return true;
            }
            if(twoFingerActive) return true;

            if(pendingEmptyDrag && hasSelection()){
                float dd=Vector2.dst(pendingDownX,pendingDownY,x,y);
                if(dd>=DRAG_START_PX){
                    pendingEmptyDrag=false;
                    beginTransform(Axis.FREE,pendingDownX,pendingDownY);
                    transformDrag(x,y);
                    return true;
                }
                return true;
            }

            if(tool==Tool.SCULPT && transforming){ sculptDrag(x,y); return true; }
            if(transforming){ transformDrag(x,y); return true; }
            if(orbiting && !hasSelection()){
                float dx=x-lastX,dy=y-lastY;
                yaw-=dx*.22f; pitch=MathUtils.clamp(pitch+dy*.18f,4f,86f);
                lastX=x; lastY=y; return true;
            }
            return true;
        }

        @Override public boolean touchUp(int x,int y,int pointer,int button){
            if(pendingEmptyDrag && hasSelection()){
                // Empty-space TAP (not drag) deselects, exactly like requested.
                pendingEmptyDrag=false;
                selected=-1; emitSelection(); pivot.set(0,0.8f,0);
                transforming=false; orbiting=false; dragAxis=Axis.NONE;
                return true;
            }

            if(twoFingerActive && !(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1))){ twoFingerActive=false; ignoreFirstSingleAfterPinch=true; }
            if(!Gdx.input.isTouched(0)&&!Gdx.input.isTouched(1)){
                transforming=false; orbiting=false; dragAxis=Axis.NONE; sculptAxis=Axis.NONE; twoFingerActive=false; pendingEmptyDrag=false;
            }
            return true;
        }

        private void initTwoFinger(){
            twoFingerActive=true; transforming=false; orbiting=false; pendingEmptyDrag=false;
            float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);
            lastMidX=(x0+x1)*.5f; lastMidY=(y0+y1)*.5f; lastPinch=Vector2.dst(x0,y0,x1,y1);
        }
        private void handleTwoFinger(){
            if(hasSelection()) return;
            float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);
            float mx=(x0+x1)*.5f,my=(y0+y1)*.5f,p=Vector2.dst(x0,y0,x1,y1);
            float dx=mx-lastMidX,dy=my-lastMidY;
            yaw-=dx*.20f; pitch=MathUtils.clamp(pitch+dy*.17f,4f,86f);
            float factor=(float)Math.exp(-(p-lastPinch)*.0045f);
            distance=MathUtils.clamp(distance*factor,.25f,50000000f);
            lastMidX=mx; lastMidY=my; lastPinch=p;
        }
    }

    private void status''', 'v7 stable touch handler')

engine_path.write_text(s, encoding='utf-8')

# ---------- Android UI: make the left tool rail scrollable ----------
a = activity_path.read_text(encoding='utf-8')
if 'import android.widget.ScrollView;' not in a:
    a = must_replace(a, 'import android.widget.PopupWindow;\n', 'import android.widget.PopupWindow;\nimport android.widget.ScrollView;\n', 'scroll import')

a = must_sub(a,
    r'''    private void buildLeftTools\(FrameLayout root\) \{.*?\n    \}\n\n    private void showAddMenu''',
'''    private void buildLeftTools(FrameLayout root) {
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(false);
        scroll.setVerticalScrollBarEnabled(false);
        scroll.setOverScrollMode(View.OVER_SCROLL_NEVER);
        scroll.setBackground(bg(0xDA1C232A,dp(9)));

        LinearLayout rail=new LinearLayout(this);
        rail.setOrientation(LinearLayout.VERTICAL);
        rail.setGravity(Gravity.TOP|Gravity.CENTER_HORIZONTAL);
        rail.setPadding(dp(3),dp(4),dp(3),dp(8));

        Button add=toolButton("＋\\nإضافة"); add.setOnClickListener(v->showAddMenu(add)); rail.addView(add,toolLp());
        Button move=toolButton("↔\\nتحريك"); move.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.MOVE);activate(move);}); rail.addView(move,toolLp());
        Button rotate=toolButton("⟳\\nتدوير"); rotate.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.ROTATE);activate(rotate);}); rail.addView(rotate,toolLp());
        Button scale=toolButton("⤢\\nحجم"); scale.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.SCALE);activate(scale);}); rail.addView(scale,toolLp());
        Button sculpt=toolButton("◈\\nنحت"); sculpt.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.SCULPT);activate(sculpt);}); rail.addView(sculpt,toolLp());
        Button paint=toolButton("●\\nطلاء"); paint.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.PAINT);activate(paint);showPaintMenu(paint);}); rail.addView(paint,toolLp());
        Button duplicate=toolButton("⧉\\nنسخ"); duplicate.setOnClickListener(v->game.duplicateSelected()); rail.addView(duplicate,toolLp());
        Button delete=toolButton("⌫\\nحذف"); delete.setOnClickListener(v->game.deleteSelected()); rail.addView(delete,toolLp());

        activate(move);
        scroll.addView(rail,new ScrollView.LayoutParams(dp(54),ScrollView.LayoutParams.WRAP_CONTENT));
        FrameLayout.LayoutParams lp=new FrameLayout.LayoutParams(dp(62),FrameLayout.LayoutParams.MATCH_PARENT);
        lp.gravity=Gravity.LEFT|Gravity.TOP;
        lp.topMargin=dp(42); lp.bottomMargin=dp(4); lp.leftMargin=dp(4);
        root.addView(scroll,lp);
    }

    private void showAddMenu''', 'scrollable left rail')

a = must_replace(a,
'''    private LinearLayout.LayoutParams toolLp(){LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(50),dp(48));lp.setMargins(0,dp(2),0,dp(2));return lp;}''',
'''    private LinearLayout.LayoutParams toolLp(){LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(48),dp(44));lp.setMargins(0,dp(2),0,dp(2));return lp;}''', 'compact tools')

activity_path.write_text(a, encoding='utf-8')

# Version bump.
b = build_path.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s+\d+', 'versionCode 7', b)
b = re.sub(r"versionName\s+'[^']+'", "versionName '0.7-stable-controls'", b)
build_path.write_text(b, encoding='utf-8')

print('V7 stable interaction patch applied successfully')
