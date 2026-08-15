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

s = must_replace(s,
'''    private final BoundingBox tmpBounds = new BoundingBox();''',
'''    private final BoundingBox tmpBounds = new BoundingBox();
    private final BoundingBox[] modelBounds = new BoundingBox[9];
    private float rotateLastScreenAngle = 0f;''', 'v6 picking state')

s = must_replace(s,
'''        buildModels();
        buildGrid();''',
'''        buildModels();
        cacheModelBounds();
        buildGrid();''', 'cache bounds call')

s = must_sub(s,
    r'''    private void buildGrid\(\) \{.*?\n    \}\n\n    private void buildGizmos''',
'''    private void buildGrid() {
        long a = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;
        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        Material minor = mat(0.19f, 0.205f, 0.225f);
        Material major = mat(0.30f, 0.32f, 0.35f);
        Material xAxis = mat(0.72f, 0.11f, 0.10f);
        Material zAxis = mat(0.10f, 0.30f, 0.78f);

        // Blender-like two-density grid: dense around origin, coarse far away.
        int fine = 100;
        for (int i = -fine; i <= fine; i++) {
            if (i % 10 == 0) continue;
            MeshPartBuilder p1 = mb.part("fgx" + i, GL20.GL_TRIANGLES, a, minor);
            p1.setVertexTransform(new Matrix4().setToTranslation(0, -0.055f, i));
            p1.box(fine * 2f, 0.014f, 0.012f);
            MeshPartBuilder p2 = mb.part("fgz" + i, GL20.GL_TRIANGLES, a, minor);
            p2.setVertexTransform(new Matrix4().setToTranslation(i, -0.055f, 0));
            p2.box(0.012f, 0.014f, fine * 2f);
        }

        int coarse = 500;
        for (int i = -coarse; i <= coarse; i += 10) {
            if (i == 0) continue;
            MeshPartBuilder p1 = mb.part("cgx" + i, GL20.GL_TRIANGLES, a, major);
            p1.setVertexTransform(new Matrix4().setToTranslation(0, -0.06f, i));
            p1.box(coarse * 2f, 0.018f, 0.026f);
            MeshPartBuilder p2 = mb.part("cgz" + i, GL20.GL_TRIANGLES, a, major);
            p2.setVertexTransform(new Matrix4().setToTranslation(i, -0.06f, 0));
            p2.box(0.026f, 0.018f, coarse * 2f);
        }

        MeshPartBuilder x = mb.part("worldX", GL20.GL_TRIANGLES, a, xAxis);
        x.setVertexTransform(new Matrix4().setToTranslation(0, -0.065f, 0));
        x.box(2000f, 0.026f, 0.055f);
        MeshPartBuilder z = mb.part("worldZ", GL20.GL_TRIANGLES, a, zAxis);
        z.setVertexTransform(new Matrix4().setToTranslation(0, -0.065f, 0));
        z.box(0.055f, 0.026f, 2000f);
        gridModel = mb.end();
        gridInstance = new ModelInstance(gridModel);
    }

    private void buildGizmos''', 'v6 blender grid')

s = must_replace(s,
'''        camera.near = Math.max(0.03f, distance * 0.00035f);
        camera.far = Math.max(800f, Math.max(distance * 120f, selectedScale * 80f));''',
'''        camera.near = Math.max(0.025f, Math.min(1.0f, distance * 0.00018f));
        camera.far = Math.max(5000f, Math.max(distance * 500f, selectedScale * 600f));''', 'v6 camera clip range')

# Oriented/local-space object picking fixes rotated object misses.
s = must_sub(s,
    r'''    private int pickObject\(float sx,float sy\)\{.*?\n    \}\n\n    private Vector3 baseDims''',
'''    private void cacheModelBounds(){
        for(int i=0;i<models.length;i++){
            BoundingBox b=new BoundingBox();
            if(models[i]!=null) models[i].calculateBoundingBox(b);
            modelBounds[i]=b;
        }
    }

    private Ray localRayFor(SceneObj o,float sx,float sy){
        Ray world=camera.getPickRay(sx,sy);
        Matrix4 inv=new Matrix4(o.instance.transform).inv();
        Ray local=new Ray(new Vector3(world.origin),new Vector3(world.direction));
        local.mul(inv);
        return local;
    }

    private boolean localHitObject(int index,float sx,float sy,Vector3 localHit){
        if(index<0||index>=objects.size)return false;
        SceneObj o=objects.get(index);
        BoundingBox b=modelBounds[MathUtils.clamp(o.data.type,0,modelBounds.length-1)];
        if(b==null)return false;
        return Intersector.intersectRayBounds(localRayFor(o,sx,sy),b,localHit);
    }

    private int pickObject(float sx,float sy){
        int best=-1; float bestD=Float.MAX_VALUE;
        Vector3 localHit=new Vector3();
        for(int i=0;i<objects.size;i++){
            if(localHitObject(i,sx,sy,localHit)){
                ObjData d=objects.get(i).data;
                float dist=camera.position.dst2(d.x,d.y,d.z);
                if(dist<bestD){bestD=dist;best=i;}
            }
        }
        return best;
    }

    private Vector3 baseDims''', 'oriented picking')

# Larger/easier gizmo hit target.
s = s.replace('Axis best=Axis.NONE; float bestD=34f;', 'Axis best=Axis.NONE; float bestD=52f;', 1)
s = s.replace('Axis best=Axis.NONE; float bestD=31f;', 'Axis best=Axis.NONE; float bestD=48f;', 1)

# Replace rotation drag with Blender-style screen angular delta around object center.
s = must_sub(s,
    r'''    private void beginTransform\(Axis a,float x,float y\)\{.*?\n    \}\n\n    private float axisRotationDelta\(Axis a,float sx,float sy\)\{.*?\n    \}''',
'''    private void beginTransform(Axis a,float x,float y){
        dragAxis=a; transforming=true; orbiting=false; lastX=x; lastY=y; pushUndo();
        if(tool==Tool.ROTATE && a!=Axis.FREE) initScreenRotation(x,y);
    }

    private void initScreenRotation(float sx,float sy){
        if(!hasSelection())return;
        ObjData d=objects.get(selected).data;
        project(d.x,d.y,d.z,tmp2a);
        rotateLastScreenAngle=MathUtils.atan2(-(sy-tmp2a.y), sx-tmp2a.x);
    }

    private float axisRotationDelta(Axis a,float sx,float sy){
        if(!hasSelection())return 0f;
        ObjData d=objects.get(selected).data;
        project(d.x,d.y,d.z,tmp2a);
        float now=MathUtils.atan2(-(sy-tmp2a.y), sx-tmp2a.x);
        float delta=now-rotateLastScreenAngle;
        while(delta>MathUtils.PI)delta-=MathUtils.PI2;
        while(delta<-MathUtils.PI)delta+=MathUtils.PI2;
        rotateLastScreenAngle=now;
        Vector3 av=axisVec(a,tmp3a).nor();
        float facing=av.dot(camera.direction);
        float sign=facing<0f?1f:-1f;
        if(Math.abs(facing)<0.04f)sign=1f;
        return delta*MathUtils.radiansToDegrees*sign;
    }''', 'screen angle rotation')

s = must_replace(s,
'''            else if(tool==Tool.ROTATE){d.ry-=dx*.34f;d.rx+=dy*.34f;}''',
'''            else if(tool==Tool.ROTATE){d.ry+=dx*.32f;d.rx+=dy*.32f;}''', 'free rotate direction')

# Better sculpt: detect actual local face of rotated object, then push/pull that face.
s = must_sub(s,
    r'''    private Axis dominantFaceAxis\(ObjData d, Vector3 worldHit\)\{.*?\n    \}\n    private boolean hitObjectPoint\(int index,float sx,float sy,Vector3 out\)\{.*?\n    \}\n    private void beginSculpt\(int index,float x,float y\)\{.*?\n    \}\n    private void sculptDrag\(float x,float y\)\{.*?\n    \}''',
'''    private Axis localFaceAxis(int index,Vector3 p){
        SceneObj o=objects.get(index);
        BoundingBox b=modelBounds[MathUtils.clamp(o.data.type,0,modelBounds.length-1)];
        float dx0=Math.abs(p.x-b.min.x),dx1=Math.abs(b.max.x-p.x);
        float dy0=Math.abs(p.y-b.min.y),dy1=Math.abs(b.max.y-p.y);
        float dz0=Math.abs(p.z-b.min.z),dz1=Math.abs(b.max.z-p.z);
        float best=dx0; Axis axis=Axis.X; sculptSign=-1f;
        if(dx1<best){best=dx1;axis=Axis.X;sculptSign=1f;}
        if(dy0<best){best=dy0;axis=Axis.Y;sculptSign=-1f;}
        if(dy1<best){best=dy1;axis=Axis.Y;sculptSign=1f;}
        if(dz0<best){best=dz0;axis=Axis.Z;sculptSign=-1f;}
        if(dz1<best){axis=Axis.Z;sculptSign=1f;}
        return axis;
    }

    private void beginSculpt(int index,float x,float y){
        selected=index; updatePivotFromSelection(); emitSelection();
        Vector3 localHit=new Vector3();
        if(!localHitObject(index,x,y,localHit)){transforming=false;return;}
        sculptAxis=localFaceAxis(index,localHit);
        transforming=true; orbiting=false; lastX=x; lastY=y; pushUndo();
    }

    private Vector3 localAxisWorld(ObjData d,Axis a,Vector3 out){
        out.set(a==Axis.X?1:0,a==Axis.Y?1:0,a==Axis.Z?1:0);
        Matrix4 r=new Matrix4().idt().rotate(Vector3.X,d.rx).rotate(Vector3.Y,d.ry).rotate(Vector3.Z,d.rz);
        return out.rot(r).nor();
    }

    private float baseAxisSize(int type,Axis a){
        Vector3 dims=baseDims(type,tmp3a);
        return a==Axis.X?Math.abs(dims.x):(a==Axis.Y?Math.abs(dims.y):Math.abs(dims.z));
    }

    private void sculptDrag(float x,float y){
        if(!hasSelection()||sculptAxis==Axis.NONE)return;
        float dx=x-lastX,dy=y-lastY;
        ObjData d=objects.get(selected).data;
        float axisPixels=axisProjectedPixels(sculptAxis,d);
        float along=axisPixels>12f?axisScreenPixelDelta(sculptAxis,dx,dy,d)*sculptSign:-dy;
        float worldPerPixel=Math.max(.00008f,distance*.0022f);
        float sizeDelta=along*worldPerPixel;
        float base=Math.max(.0001f,baseAxisSize(d.type,sculptAxis));
        float oldScale=sculptAxis==Axis.X?d.sx:(sculptAxis==Axis.Y?d.sy:d.sz);
        float oldSize=Math.max(base*.0001f,base*oldScale);
        float newSize=Math.max(base*.0001f,oldSize+sizeDelta);
        float realDelta=newSize-oldSize;
        float ns=clampScale(newSize/base);
        if(sculptAxis==Axis.X)d.sx=ns; else if(sculptAxis==Axis.Y)d.sy=ns; else d.sz=ns;
        Vector3 dir=localAxisWorld(d,sculptAxis,tmp3b).scl(realDelta*.5f*sculptSign);
        d.x+=dir.x; d.y+=dir.y; d.z+=dir.z;
        apply(objects.get(selected)); pivot.set(d.x,d.y,d.z); emitSelection(); lastX=x;lastY=y;
    }''', 'v6 local sculpt')

# Replace touch handling. Selection is sticky; camera activates only after a clear empty-space touch.
s = must_sub(s,
    r'''    private class EditorInput extends InputAdapter \{.*?\n    \}\n\n    private void status''',
'''    private class EditorInput extends InputAdapter {
        @Override public boolean touchDown(int x,int y,int pointer,int button){
            if(Gdx.input.isTouched(1)){
                if(hasSelection()){twoFingerActive=true;transforming=false;orbiting=false;return true;}
                initTwoFinger();return true;
            }
            if(ignoreFirstSingleAfterPinch){lastX=x;lastY=y;ignoreFirstSingleAfterPinch=false;return true;}
            lastX=x;lastY=y;transforming=false;orbiting=false;sculptAxis=Axis.NONE;

            if(hasSelection() && tool!=Tool.PAINT && tool!=Tool.SCULPT){
                Axis h=hitAxis(x,y);
                if(h!=Axis.NONE){beginTransform(h,x,y);return true;}
            }

            int obj=pickObject(x,y);
            if(obj>=0){
                selected=obj;updatePivotFromSelection();emitSelection();
                if(tool==Tool.PAINT){paintObject(obj);return true;}
                if(tool==Tool.SCULPT){beginSculpt(obj,x,y);return true;}
                beginTransform(Axis.FREE,x,y);return true;
            }

            // Only a true empty-space press deselects. From that same press the camera may orbit.
            selected=-1;emitSelection();pivot.set(0,0.8f,0);orbiting=true;transforming=false;return true;
        }

        @Override public boolean touchDragged(int x,int y,int pointer){
            if(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1)){
                if(hasSelection())return true;
                if(!twoFingerActive)initTwoFinger();else handleTwoFinger();return true;
            }
            if(twoFingerActive)return true;
            if(tool==Tool.SCULPT&&transforming){sculptDrag(x,y);return true;}
            if(transforming){transformDrag(x,y);return true;}
            if(orbiting&&!hasSelection()){
                float dx=x-lastX,dy=y-lastY;
                yaw-=dx*.22f;pitch=MathUtils.clamp(pitch+dy*.18f,4f,86f);
                lastX=x;lastY=y;return true;
            }
            return true;
        }

        @Override public boolean touchUp(int x,int y,int pointer,int button){
            if(twoFingerActive&&!(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1))){twoFingerActive=false;ignoreFirstSingleAfterPinch=true;}
            if(!Gdx.input.isTouched(0)&&!Gdx.input.isTouched(1)){
                transforming=false;orbiting=false;dragAxis=Axis.NONE;sculptAxis=Axis.NONE;twoFingerActive=false;
            }
            return true;
        }

        private void initTwoFinger(){
            twoFingerActive=true;transforming=false;orbiting=false;
            float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);
            lastMidX=(x0+x1)*.5f;lastMidY=(y0+y1)*.5f;lastPinch=Vector2.dst(x0,y0,x1,y1);
        }

        private void handleTwoFinger(){
            if(hasSelection())return;
            float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);
            float mx=(x0+x1)*.5f,my=(y0+y1)*.5f,p=Vector2.dst(x0,y0,x1,y1);
            float dx=mx-lastMidX,dy=my-lastMidY;
            yaw-=dx*.18f;pitch=MathUtils.clamp(pitch+dy*.15f,4f,86f);
            float factor=(float)Math.exp(-(p-lastPinch)*.0038f);
            distance=MathUtils.clamp(distance*factor,.25f,50000000f);
            lastMidX=mx;lastMidY=my;lastPinch=p;
        }
    }

    private void status''', 'v6 touch interaction')

# Remove noisy status messages completely; selection coordinates remain in top bar.
s = must_sub(s,
    r'''    private void status\(String s\)\{if\(ui!=null\)ui\.onStatus\(s\);\}''',
'''    private void status(String s){}''', 'disable status messages')

engine_path.write_text(s,encoding='utf-8')

# UI: remove bottom instructions/status overlay, use cleaner compact controls, 24-bit depth.
a=activity_path.read_text(encoding='utf-8')
a=must_replace(a,
'''        cfg.depth = 16;''',
'''        cfg.depth = 24;''', '24 bit depth')
a=must_replace(a,
'''        buildBottomHint(root);
        buildStatus(root);
        setContentView(root);''',
'''        setContentView(root);''', 'remove hint and status overlay')
a=must_replace(a,
'''        Button move=toolButton("⇆\\nتحريك");''',
'''        Button move=toolButton("↔\\nتحريك");''', 'move icon')
a=must_replace(a,
'''        Button scale=toolButton("⤢\\nحجم");''',
'''        Button scale=toolButton("⌗\\nحجم");''', 'scale icon')
a=must_replace(a,
'''        Button sculpt=toolButton("◇\\nنحت");''',
'''        Button sculpt=toolButton("◈\\nنحت");''', 'sculpt icon')
a=must_replace(a,
'''        Button paint=toolButton("●\\nطلاء");''',
'''        Button paint=toolButton("◉\\nطلاء");''', 'paint icon')
a=must_replace(a,
'''    private LinearLayout.LayoutParams toolLp(){LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(50),dp(48));lp.setMargins(0,dp(2),0,dp(2));return lp;}''',
'''    private LinearLayout.LayoutParams toolLp(){LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(dp(48),dp(44));lp.setMargins(0,dp(2),0,dp(2));return lp;}''', 'compact tools')
activity_path.write_text(a,encoding='utf-8')

b=build_path.read_text(encoding='utf-8')
b=re.sub(r'versionCode\s+\d+','versionCode 6',b)
b=re.sub(r"versionName\s+'[^']+'","versionName '0.6-blender-interaction'",b)
build_path.write_text(b,encoding='utf-8')

print('V6 patch applied successfully')
