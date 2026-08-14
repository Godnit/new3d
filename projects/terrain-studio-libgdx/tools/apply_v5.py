from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
engine_path = ROOT / 'app/src/main/java/com/godnit/terrainstudio/gdx/MiniBlenderGameV4.java'
activity_path = ROOT / 'app/src/main/java/com/godnit/terrainstudio/gdx/BlenderActivityV4.java'
build_path = ROOT / 'app/build.gradle'
manifest_path = ROOT / 'app/src/main/AndroidManifest.xml'


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

s = must_replace(s,
'''import com.badlogic.gdx.graphics.g3d.ModelInstance;\n''',
'''import com.badlogic.gdx.graphics.g3d.ModelInstance;\nimport com.badlogic.gdx.graphics.g3d.model.Node;\nimport com.badlogic.gdx.graphics.g3d.model.NodePart;\n''', 'node imports')
s = must_replace(s,
'''import com.badlogic.gdx.math.Matrix4;\n''',
'''import com.badlogic.gdx.math.Matrix4;\nimport com.badlogic.gdx.math.Plane;\n''', 'plane import')
s = must_replace(s,
'''    public enum Tool { MOVE, ROTATE, SCALE }''',
'''    public enum Tool { MOVE, ROTATE, SCALE, SCULPT, PAINT }''', 'tool enum')

s = must_replace(s,
'''    private UiListener ui;\n''',
'''    private UiListener ui;\n    private final Color paintColor = new Color(0.24f, 0.55f, 0.92f, 1f);\n    private final Vector3 axisRotationLast = new Vector3();\n    private final Plane rotationPlane = new Plane(new Vector3(0, 1, 0), 0f);\n    private Axis sculptAxis = Axis.NONE;\n    private float sculptSign = 1f;\n''', 'v5 state')

s = must_sub(s,
    r'''    private void buildGrid\(\) \{.*?\n    \}\n\n    private void buildGizmos''',
'''    private void buildGrid() {\n        long a = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;\n        ModelBuilder mb = new ModelBuilder();\n        mb.begin();\n        Material minor = mat(0.20f, 0.22f, 0.24f);\n        Material major = mat(0.31f, 0.33f, 0.36f);\n        Material xAxis = mat(0.62f, 0.13f, 0.11f);\n        Material zAxis = mat(0.12f, 0.28f, 0.64f);\n        int extent = 50;\n        for (int i = -extent; i <= extent; i++) {\n            Material mx = i == 0 ? zAxis : (i % 10 == 0 ? major : minor);\n            Material mz = i == 0 ? xAxis : (i % 10 == 0 ? major : minor);\n            float w = (i == 0 ? 0.055f : (i % 10 == 0 ? 0.032f : 0.014f));\n            MeshPartBuilder p1 = mb.part("gx" + i, GL20.GL_TRIANGLES, a, mx);\n            p1.setVertexTransform(new Matrix4().setToTranslation(0, -0.045f, i));\n            p1.box(extent * 2f, 0.018f, w);\n            MeshPartBuilder p2 = mb.part("gz" + i, GL20.GL_TRIANGLES, a, mz);\n            p2.setVertexTransform(new Matrix4().setToTranslation(i, -0.045f, 0));\n            p2.box(w, 0.018f, extent * 2f);\n        }\n        gridModel = mb.end();\n        gridInstance = new ModelInstance(gridModel);\n    }\n\n    private void buildGizmos''', 'blender grid')

s = must_replace(s,
'''        float len = 2.2f;''',
'''        float len = 2.85f;''', 'gizmo length')
s = must_replace(s,
'''        float r = 2.05f;\n        int segs = 18;\n        float start = -70f, end = 95f;''',
'''        float r = 2.55f;\n        int segs = 22;\n        float start = -58f, end = 104f;''', 'rotation arcs')

s = must_replace(s,
'''        if (hasSelection()) {\n            refreshGizmo();\n            Gdx.gl.glClear(GL20.GL_DEPTH_BUFFER_BIT);\n            gizmoBatch.begin(camera);\n            gizmoBatch.render(gizmoInstance);\n            gizmoBatch.end();\n        }''',
'''        if (hasSelection() && tool != Tool.PAINT && tool != Tool.SCULPT) {\n            refreshGizmo();\n            Gdx.gl.glDisable(GL20.GL_DEPTH_TEST);\n            Gdx.gl.glDisable(GL20.GL_CULL_FACE);\n            gizmoBatch.begin(camera);\n            gizmoBatch.render(gizmoInstance);\n            gizmoBatch.end();\n            Gdx.gl.glEnable(GL20.GL_CULL_FACE);\n            Gdx.gl.glEnable(GL20.GL_DEPTH_TEST);\n        }''', 'gizmo overlay')

s = must_replace(s,
'''        camera.position.set(pivot.x + px, pivot.y + py, pivot.z + pz);\n        camera.up.set(Vector3.Y);''',
'''        camera.position.set(pivot.x + px, pivot.y + py, pivot.z + pz);\n        float selectedScale = hasSelection() ? maxScale(objects.get(selected).data) : 1f;\n        camera.near = Math.max(0.03f, distance * 0.00035f);\n        camera.far = Math.max(800f, Math.max(distance * 120f, selectedScale * 80f));\n        camera.up.set(Vector3.Y);''', 'dynamic camera range')

s = must_replace(s,
'''    public void setTool(Tool t) { tool=t; dragAxis=Axis.NONE; status(toolName()); }\n    public Tool getTool(){ return tool; }''',
'''    public void setTool(Tool t) { tool=t; dragAxis=Axis.NONE; transforming=false; status(toolName()); }\n    public Tool getTool(){ return tool; }\n    public void setPaintColor(final Color c){ post(() -> paintColor.set(c)); }\n    public int getObjectCount(){ return objects.size; }\n    public String getObjectLabel(int index){ if(index<0||index>=objects.size)return ""; return (index+1)+" • "+typeName(objects.get(index).data.type); }\n    public void selectObject(final int index){ post(() -> { if(index<0||index>=objects.size)return; selected=index; updatePivotFromSelection(); emitSelection(); status("تم تحديد "+typeName(objects.get(index).data.type)); }); }''', 'public v5 api')

s = must_replace(s,
'''    public void focusSelected(){ post(() -> { if(!hasSelection()) return; updatePivotFromSelection(); distance=MathUtils.clamp(maxScale(objects.get(selected).data)*8f+8f,9f,28f); }); }''',
'''    public void focusSelected(){ post(() -> { if(!hasSelection()) return; updatePivotFromSelection(); distance=MathUtils.clamp(maxScale(objects.get(selected).data)*8f+8f,2f,50000000f); }); }''', 'focus huge objects')

s = must_replace(s,
'''    private SceneObj makeObj(ObjData d){ ModelInstance i=new ModelInstance(models[MathUtils.clamp(d.type,0,models.length-1)]); SceneObj o=new SceneObj(d,i); apply(o); return o; }''',
'''    private SceneObj makeObj(ObjData d){\n        ModelInstance i=new ModelInstance(models[MathUtils.clamp(d.type,0,models.length-1)]);\n        cloneMaterials(i);\n        SceneObj o=new SceneObj(d,i);\n        if(d.painted) applyTint(o);\n        apply(o);\n        return o;\n    }\n    private void cloneMaterials(ModelInstance instance){ for(Node n:instance.nodes) cloneNodeMaterials(n); }\n    private void cloneNodeMaterials(Node n){ for(NodePart p:n.parts)p.material=new Material(p.material); for(Node c:n.getChildren())cloneNodeMaterials(c); }\n    private void applyTint(SceneObj o){ for(Node n:o.instance.nodes) tintNode(n,o.data.cr,o.data.cg,o.data.cb); }\n    private void tintNode(Node n,float r,float g,float b){ for(NodePart p:n.parts)p.material.set(ColorAttribute.createDiffuse(new Color(r,g,b,1f))); for(Node c:n.getChildren())tintNode(c,r,g,b); }\n    private void paintObject(int index){ if(index<0||index>=objects.size)return; pushUndo(); SceneObj o=objects.get(index); o.data.painted=true; o.data.cr=paintColor.r; o.data.cg=paintColor.g; o.data.cb=paintColor.b; applyTint(o); selected=index; updatePivotFromSelection(); emitSelection(); status("تم طلاء "+typeName(o.data.type)); }''', 'per object paint')

s = must_replace(s,
'''    private void beginTransform(Axis a,float x,float y){dragAxis=a;transforming=true;orbiting=false;lastX=x;lastY=y;pushUndo();}''',
'''    private void beginTransform(Axis a,float x,float y){\n        dragAxis=a; transforming=true; orbiting=false; lastX=x; lastY=y; pushUndo();\n        if(tool==Tool.ROTATE && a!=Axis.FREE) initAxisRotation(a,x,y);\n    }\n\n    private void initAxisRotation(Axis a,float sx,float sy){\n        if(!hasSelection())return; ObjData d=objects.get(selected).data; Vector3 normal=axisVec(a,tmp3a).nor();\n        rotationPlane.set(normal, tmp3b.set(d.x,d.y,d.z));\n        Ray ray=camera.getPickRay(sx,sy); Vector3 p=new Vector3();\n        if(Intersector.intersectRayPlane(ray,rotationPlane,p)){axisRotationLast.set(p.x-d.x,p.y-d.y,p.z-d.z).nor();}\n        else axisRotationLast.setZero();\n    }\n\n    private float axisRotationDelta(Axis a,float sx,float sy){\n        if(!hasSelection()||axisRotationLast.isZero())return 0f; ObjData d=objects.get(selected).data;\n        Vector3 normal=axisVec(a,tmp3a).nor(); rotationPlane.set(normal,tmp3b.set(d.x,d.y,d.z));\n        Ray ray=camera.getPickRay(sx,sy); Vector3 p=new Vector3(); if(!Intersector.intersectRayPlane(ray,rotationPlane,p))return 0f;\n        Vector3 cur=p.sub(d.x,d.y,d.z); if(cur.len2()<0.000001f)return 0f; cur.nor();\n        float sin=normal.dot(tmp3c.set(axisRotationLast).crs(cur)); float cos=MathUtils.clamp(axisRotationLast.dot(cur),-1f,1f);\n        float ang=MathUtils.atan2(sin,cos)*MathUtils.radiansToDegrees; axisRotationLast.set(cur); return ang;\n    }''', 'rotation world plane')

s = must_replace(s,
'''            else if(tool==Tool.SCALE){float f=(float)Math.exp((dx-dy)*.0065f);d.sx=clampScale(d.sx*f);d.sy=clampScale(d.sy*f);d.sz=clampScale(d.sz*f);}\n            else {d.ry+=dx*.34f;d.rx-=dy*.34f;}''',
'''            else if(tool==Tool.SCALE){float f=(float)Math.exp((dx-dy)*.0075f);d.sx=clampScale(d.sx*f);d.sy=clampScale(d.sy*f);d.sz=clampScale(d.sz*f);}\n            else if(tool==Tool.ROTATE){d.ry-=dx*.34f;d.rx+=dy*.34f;}''', 'free transform directions')

s = must_replace(s,
'''            float pix=axisProjectedPixels(dragAxis,d); if(pix<12)pix=80; float along=axisScreenPixelDelta(dragAxis,dx,dy,d); float f=MathUtils.clamp(1f+along/pix,.72f,1.35f); if(dragAxis==Axis.X)d.sx=clampScale(d.sx*f);else if(dragAxis==Axis.Y)d.sy=clampScale(d.sy*f);else d.sz=clampScale(d.sz*f);\n        } else {\n            float along=dx*rotationTangent.x+dy*rotationTangent.y; float sign=(dragAxis==Axis.X||dragAxis==Axis.Z)?-1f:1f; float ang=along*.55f*sign; if(dragAxis==Axis.X)d.rx+=ang;else if(dragAxis==Axis.Y)d.ry+=ang;else d.rz+=ang;''',
'''            float along=axisScreenPixelDelta(dragAxis,dx,dy,d); float f=(float)Math.exp(along*.0085f); if(dragAxis==Axis.X)d.sx=clampScale(d.sx*f);else if(dragAxis==Axis.Y)d.sy=clampScale(d.sy*f);else d.sz=clampScale(d.sz*f);\n        } else if(tool==Tool.ROTATE) {\n            float ang=axisRotationDelta(dragAxis,x,y); if(dragAxis==Axis.X)d.rx+=ang;else if(dragAxis==Axis.Y)d.ry+=ang;else d.rz+=ang;''', 'axis scale and rotate')

s = must_replace(s,
'''    private float clampScale(float v){return MathUtils.clamp(v,.08f,12f);}''',
'''    private float clampScale(float v){return MathUtils.clamp(v,.0001f,1000000f);}''', 'huge scale')

insert_helpers = '''\n    private Axis dominantFaceAxis(ObjData d, Vector3 worldHit){\n        Vector3 dims=baseDims(d.type,tmp3a); float hx=Math.max(.0001f,Math.abs(dims.x*d.sx)*.5f),hy=Math.max(.0001f,Math.abs(dims.y*d.sy)*.5f),hz=Math.max(.0001f,Math.abs(dims.z*d.sz)*.5f);\n        float nx=(worldHit.x-d.x)/hx,ny=(worldHit.y-d.y)/hy,nz=(worldHit.z-d.z)/hz;\n        float ax=Math.abs(nx),ay=Math.abs(ny),az=Math.abs(nz); if(ax>=ay&&ax>=az){sculptSign=Math.signum(nx==0?1:nx);return Axis.X;} if(ay>=az){sculptSign=Math.signum(ny==0?1:ny);return Axis.Y;} sculptSign=Math.signum(nz==0?1:nz);return Axis.Z;\n    }\n    private boolean hitObjectPoint(int index,float sx,float sy,Vector3 out){\n        if(index<0||index>=objects.size)return false; ObjData d=objects.get(index).data; Vector3 dims=baseDims(d.type,tmp3a);\n        float hx=Math.abs(dims.x*d.sx)*.5f,hy=Math.abs(dims.y*d.sy)*.5f,hz=Math.abs(dims.z*d.sz)*.5f; tmpBounds.set(tmp3b.set(d.x-hx,d.y-hy,d.z-hz),tmp3c.set(d.x+hx,d.y+hy,d.z+hz));\n        return Intersector.intersectRayBounds(camera.getPickRay(sx,sy),tmpBounds,out);\n    }\n    private void beginSculpt(int index,float x,float y){\n        selected=index; updatePivotFromSelection(); emitSelection(); Vector3 hp=new Vector3(); if(!hitObjectPoint(index,x,y,hp))return; sculptAxis=dominantFaceAxis(objects.get(index).data,hp);\n        transforming=true; orbiting=false; lastX=x;lastY=y;pushUndo(); status("نحت الوجه • اسحب للخارج أو الداخل");\n    }\n    private void sculptDrag(float x,float y){\n        if(!hasSelection()||sculptAxis==Axis.NONE)return; float dx=x-lastX,dy=y-lastY; ObjData d=objects.get(selected).data; float along=axisScreenPixelDelta(sculptAxis,dx,dy,d)*sculptSign; float f=(float)Math.exp(along*.006f);\n        Vector3 dims=baseDims(d.type,tmp3a); float old,newV,shift;\n        if(sculptAxis==Axis.X){old=d.sx;newV=clampScale(old*f);shift=(newV-old)*dims.x*.5f*sculptSign;d.sx=newV;d.x+=shift;}\n        else if(sculptAxis==Axis.Y){old=d.sy;newV=clampScale(old*f);shift=(newV-old)*dims.y*.5f*sculptSign;d.sy=newV;d.y+=shift;}\n        else {old=d.sz;newV=clampScale(old*f);shift=(newV-old)*dims.z*.5f*sculptSign;d.sz=newV;d.z+=shift;}\n        apply(objects.get(selected)); pivot.set(d.x,d.y,d.z); emitSelection(); lastX=x;lastY=y;\n    }\n'''
s = must_replace(s, '\n    private class EditorInput extends InputAdapter {', insert_helpers + '\n    private class EditorInput extends InputAdapter {', 'sculpt helpers')

s = must_sub(s,
    r'''    private class EditorInput extends InputAdapter \{.*?\n    \}\n\n    private void status''',
'''    private class EditorInput extends InputAdapter {\n        @Override public boolean touchDown(int x,int y,int pointer,int button){\n            if(Gdx.input.isTouched(1)){\n                if(hasSelection()){ twoFingerActive=true; transforming=false; orbiting=false; return true; }\n                initTwoFinger(); return true;\n            }\n            if(ignoreFirstSingleAfterPinch){lastX=x;lastY=y;ignoreFirstSingleAfterPinch=false;return true;}\n            lastX=x;lastY=y; transforming=false; orbiting=false; sculptAxis=Axis.NONE;\n\n            if(hasSelection() && tool!=Tool.PAINT && tool!=Tool.SCULPT){ Axis h=hitAxis(x,y); if(h!=Axis.NONE){beginTransform(h,x,y);return true;} }\n            int obj=pickObject(x,y);\n            if(obj>=0){\n                selected=obj; updatePivotFromSelection(); emitSelection();\n                if(tool==Tool.PAINT){paintObject(obj);return true;}\n                if(tool==Tool.SCULPT){beginSculpt(obj,x,y);return true;}\n                beginTransform(Axis.FREE,x,y); return true;\n            }\n\n            selected=-1; emitSelection(); pivot.set(0,0.8f,0); orbiting=true; transforming=false; status("تم إلغاء التحديد • الكاميرا حرة"); return true;\n        }\n        @Override public boolean touchDragged(int x,int y,int pointer){\n            if(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1)){\n                if(hasSelection()) return true;\n                if(!twoFingerActive)initTwoFinger(); else handleTwoFinger(); return true;\n            }\n            if(twoFingerActive)return true;\n            if(tool==Tool.SCULPT && transforming){sculptDrag(x,y);return true;}\n            if(transforming){transformDrag(x,y);return true;}\n            if(orbiting && !hasSelection()){float dx=x-lastX,dy=y-lastY;yaw-=dx*.24f;pitch=MathUtils.clamp(pitch+dy*.20f,5f,85f);lastX=x;lastY=y;return true;}\n            return true;\n        }\n        @Override public boolean touchUp(int x,int y,int pointer,int button){\n            if(twoFingerActive && !(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1))){twoFingerActive=false;ignoreFirstSingleAfterPinch=true;}\n            if(!Gdx.input.isTouched(0)&&!Gdx.input.isTouched(1)){transforming=false;orbiting=false;dragAxis=Axis.NONE;sculptAxis=Axis.NONE;twoFingerActive=false;}\n            return true;\n        }\n        private void initTwoFinger(){twoFingerActive=true;transforming=false;orbiting=false;float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);lastMidX=(x0+x1)*.5f;lastMidY=(y0+y1)*.5f;lastPinch=Vector2.dst(x0,y0,x1,y1);}\n        private void handleTwoFinger(){\n            if(hasSelection())return; float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);float mx=(x0+x1)*.5f,my=(y0+y1)*.5f,p=Vector2.dst(x0,y0,x1,y1);\n            float dx=mx-lastMidX,dy=my-lastMidY;yaw-=dx*.20f;pitch=MathUtils.clamp(pitch+dy*.17f,5f,85f);float factor=(float)Math.exp(-(p-lastPinch)*.0045f);distance=MathUtils.clamp(distance*factor,.35f,50000000f);lastMidX=mx;lastMidY=my;lastPinch=p;\n        }\n    }\n\n    private void status''', 'selection camera behavior')

s = must_replace(s,
'''    private String toolName(){return tool==Tool.MOVE?"تحريك • اسحب المجسم بحرية أو اسحب محورًا":tool==Tool.ROTATE?"تدوير • اسحب المجسم أو القوس الملون":"حجم • اسحب المجسم لكل المحاور أو محورًا واحدًا";}''',
'''    private String toolName(){ if(tool==Tool.MOVE)return "تحريك • حر أو على محور"; if(tool==Tool.ROTATE)return "تدوير • حر أو على قوس"; if(tool==Tool.SCALE)return "حجم • شامل أو محور واحد"; if(tool==Tool.SCULPT)return "نحت • اسحب وجه المجسم"; return "طلاء • اختر لونًا والمس المجسم"; }''', 'tool labels')

s = must_replace(s,
'''    public static class ObjData { public int type; public float x,y,z,rx,ry,rz,sx=1,sy=1,sz=1; public ObjData(){} ObjData(ObjData o){type=o.type;x=o.x;y=o.y;z=o.z;rx=o.rx;ry=o.ry;rz=o.rz;sx=o.sx;sy=o.sy;sz=o.sz;} }''',
'''    public static class ObjData { public int type; public float x,y,z,rx,ry,rz,sx=1,sy=1,sz=1; public boolean painted=false; public float cr=.68f,cg=.70f,cb=.73f; public ObjData(){} ObjData(ObjData o){type=o.type;x=o.x;y=o.y;z=o.z;rx=o.rx;ry=o.ry;rz=o.rz;sx=o.sx;sy=o.sy;sz=o.sz;painted=o.painted;cr=o.cr;cg=o.cg;cb=o.cb;} }''', 'save paint')

engine_path.write_text(s, encoding='utf-8')

# ---------- Android UI ----------
a = activity_path.read_text(encoding='utf-8')
a = must_replace(a,
'''        bar.addView(topButton("◎",v->game.focusSelected()));''',
'''        bar.addView(topButton("◎",v->game.focusSelected()));\n        bar.addView(topButton("☰",v->showOutliner(bar)));''', 'outliner button')

a = must_replace(a,
'''        Button duplicate=toolButton("⧉\\nنسخ");''',
'''        Button sculpt=toolButton("◇\\nنحت");\n        sculpt.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.SCULPT);activate(sculpt);});\n        rail.addView(sculpt,toolLp());\n\n        Button paint=toolButton("●\\nطلاء");\n        paint.setOnClickListener(v->{game.setTool(MiniBlenderGameV4.Tool.PAINT);activate(paint);showPaintMenu(paint);});\n        rail.addView(paint,toolLp());\n\n        Button duplicate=toolButton("⧉\\nنسخ");''', 'sculpt paint buttons')

a = must_replace(a,
'''        TextView hint=text("اضغط مجسمًا = تحديد مباشر   •   اسحب المجسم = تعديل حر   •   اسحب المحور الملون = تعديل دقيق   •   مساحة فارغة أو إصبعان = تدوير الكاميرا   •   قرّب/بعّد بإصبعين",9,0xFFD4DCE2);''',
'''        TextView hint=text("مجسم محدد = الكاميرا ثابتة   •   اضغط الفراغ لإلغاء التحديد   •   اسحب المجسم بحرية أو المحور بدقة   •   بعد إلغاء التحديد: اسحب/استخدم إصبعين للكاميرا",9,0xFFD4DCE2);''', 'bottom hint')

extra_ui = '''\n    private void showPaintMenu(View anchor){\n        LinearLayout row=new LinearLayout(this); row.setPadding(dp(6),dp(6),dp(6),dp(6)); row.setBackground(bg(0xF51E2831,dp(10)));\n        int[] colors={0xFF4E8A3A,0xFF2D6AA3,0xFFB33C36,0xFFE0B45D,0xFF8C6A48,0xFF8C8F94,0xFFE8E8E8,0xFF22262A};\n        float[][] rgb={{.31f,.54f,.23f},{.18f,.42f,.64f},{.70f,.24f,.21f},{.88f,.71f,.36f},{.55f,.42f,.28f},{.55f,.56f,.58f},{.91f,.91f,.91f},{.13f,.15f,.16f}};\n        final PopupWindow[] holder=new PopupWindow[1];\n        for(int i=0;i<colors.length;i++){ final float r=rgb[i][0],g=rgb[i][1],b=rgb[i][2]; Button sw=new Button(this); sw.setMinWidth(0);sw.setMinHeight(0);sw.setBackground(bg(colors[i],dp(6))); LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(34),dp(34));lp.setMargins(dp(2),0,dp(2),0);row.addView(sw,lp);sw.setOnClickListener(v->{game.setPaintColor(new com.badlogic.gdx.graphics.Color(r,g,b,1));if(holder[0]!=null)holder[0].dismiss();}); }\n        PopupWindow pop=new PopupWindow(row,FrameLayout.LayoutParams.WRAP_CONTENT,dp(48),true);holder[0]=pop;pop.setOutsideTouchable(true);pop.setBackgroundDrawable(bg(0x001E2831,dp(8)));pop.setElevation(dp(8));pop.showAsDropDown(anchor,dp(4),-dp(54));\n    }\n\n    private void showOutliner(View anchor){\n        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(5),dp(5),dp(5),dp(5));box.setBackground(bg(0xF51E2831,dp(10)));\n        TextView h=text("المشهد / Outliner",11,0xFF9ED9F0);h.setTypeface(Typeface.DEFAULT_BOLD);h.setGravity(Gravity.CENTER);box.addView(h,new LinearLayout.LayoutParams(dp(175),dp(30)));\n        final PopupWindow[] holder=new PopupWindow[1]; int count=game.getObjectCount(); if(count==0){TextView e=text("المشهد فارغ",10,0xFFC7D1D8);e.setGravity(Gravity.CENTER);box.addView(e,new LinearLayout.LayoutParams(dp(175),dp(38)));}\n        for(int i=0;i<count;i++){final int idx=i;Button b=new Button(this);b.setText(game.getObjectLabel(i));b.setAllCaps(false);b.setTextColor(Color.WHITE);b.setTextSize(10);b.setGravity(Gravity.CENTER_VERTICAL|Gravity.RIGHT);b.setTextDirection(View.TEXT_DIRECTION_RTL);b.setBackground(bg(BTN,dp(6)));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(175),dp(35));lp.setMargins(0,dp(1),0,dp(1));box.addView(b,lp);b.setOnClickListener(v->{game.selectObject(idx);if(holder[0]!=null)holder[0].dismiss();});}\n        PopupWindow pop=new PopupWindow(box,dp(185),FrameLayout.LayoutParams.WRAP_CONTENT,true);holder[0]=pop;pop.setOutsideTouchable(true);pop.setBackgroundDrawable(bg(0x001E2831,dp(8)));pop.setElevation(dp(8));pop.showAsDropDown(anchor,-dp(180),0);\n    }\n'''
a = must_replace(a, '\n    private void buildBottomHint(FrameLayout root){', extra_ui + '\n    private void buildBottomHint(FrameLayout root){', 'extra ui')
activity_path.write_text(a, encoding='utf-8')

# version metadata
b = build_path.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s+\d+', 'versionCode 5', b)
b = re.sub(r"versionName\s+'[^']+'", "versionName '0.5-blender-controls'", b)
build_path.write_text(b, encoding='utf-8')

m = manifest_path.read_text(encoding='utf-8').replace('Terrain Studio Mini 3D', 'Terrain Studio Mini 3D')
manifest_path.write_text(m, encoding='utf-8')

print('V5 patch applied successfully')
