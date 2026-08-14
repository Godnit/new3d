package com.godnit.terrainstudio.gdx;

import com.badlogic.gdx.ApplicationAdapter;
import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.InputAdapter;
import com.badlogic.gdx.Preferences;
import com.badlogic.gdx.graphics.Color;
import com.badlogic.gdx.graphics.GL20;
import com.badlogic.gdx.graphics.PerspectiveCamera;
import com.badlogic.gdx.graphics.VertexAttributes;
import com.badlogic.gdx.graphics.g3d.Environment;
import com.badlogic.gdx.graphics.g3d.Material;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelBatch;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.attributes.ColorAttribute;
import com.badlogic.gdx.graphics.g3d.attributes.DepthTestAttribute;
import com.badlogic.gdx.graphics.g3d.environment.DirectionalLight;
import com.badlogic.gdx.graphics.g3d.environment.DirectionalShadowLight;
import com.badlogic.gdx.graphics.g3d.utils.DepthShaderProvider;
import com.badlogic.gdx.graphics.g3d.utils.MeshPartBuilder;
import com.badlogic.gdx.graphics.g3d.utils.ModelBuilder;
import com.badlogic.gdx.math.Intersector;
import com.badlogic.gdx.math.MathUtils;
import com.badlogic.gdx.math.Matrix4;
import com.badlogic.gdx.math.Vector2;
import com.badlogic.gdx.math.Vector3;
import com.badlogic.gdx.math.collision.BoundingBox;
import com.badlogic.gdx.math.collision.Ray;
import com.badlogic.gdx.utils.Array;
import com.badlogic.gdx.utils.Json;

public class MiniBlenderGameV4 extends ApplicationAdapter {
    public enum Tool { MOVE, ROTATE, SCALE }
    private enum Axis { NONE, X, Y, Z, FREE }

    public static final int GROUND = 0;
    public static final int CUBE = 1;
    public static final int SPHERE = 2;
    public static final int CYLINDER = 3;
    public static final int CONE = 4;
    public static final int PYRAMID = 5;
    public static final int TREE = 6;
    public static final int ROCK = 7;
    public static final int BUSH = 8;

    public interface UiListener {
        void onStatus(String text);
        void onSelection(String text);
    }

    private PerspectiveCamera camera;
    private ModelBatch sceneBatch;
    private ModelBatch shadowBatch;
    private ModelBatch gizmoBatch;
    private Environment environment;
    private DirectionalShadowLight shadowLight;
    private boolean shadows = true;

    private Model gridModel, moveGizmoModel, scaleGizmoModel, rotateGizmoModel;
    private ModelInstance gridInstance, gizmoInstance;
    private final Model[] models = new Model[9];
    private final Array<SceneObj> objects = new Array<>();
    private final Array<Snapshot> undo = new Array<>();

    private Tool tool = Tool.MOVE;
    private int selected = -1;
    private UiListener ui;

    private float yaw = 42f;
    private float pitch = 38f;
    private float distance = 24f;
    private final Vector3 pivot = new Vector3(0, 0.8f, 0);

    private Axis dragAxis = Axis.NONE;
    private boolean transforming = false;
    private boolean orbiting = false;
    private boolean twoFingerActive = false;
    private boolean ignoreFirstSingleAfterPinch = false;
    private float lastX, lastY, lastMidX, lastMidY, lastPinch;
    private final Vector2 rotationTangent = new Vector2(1, 0);

    private final Vector3 tmp3a = new Vector3();
    private final Vector3 tmp3b = new Vector3();
    private final Vector3 tmp3c = new Vector3();
    private final Vector2 tmp2a = new Vector2();
    private final Vector2 tmp2b = new Vector2();
    private final BoundingBox tmpBounds = new BoundingBox();

    @Override
    public void create() {
        Gdx.gl.glEnable(GL20.GL_DEPTH_TEST);
        Gdx.gl.glEnable(GL20.GL_CULL_FACE);
        Gdx.gl.glCullFace(GL20.GL_BACK);

        camera = new PerspectiveCamera(58f, Gdx.graphics.getWidth(), Gdx.graphics.getHeight());
        camera.near = 0.2f;
        camera.far = 180f;
        updateCamera();

        sceneBatch = new ModelBatch();
        gizmoBatch = new ModelBatch();
        environment = new Environment();
        environment.set(new ColorAttribute(ColorAttribute.AmbientLight, 0.44f, 0.46f, 0.49f, 1f));
        try {
            shadowLight = new DirectionalShadowLight(512, 512, 46f, 46f, 1f, 90f);
            shadowLight.set(0.96f, 0.89f, 0.78f, -0.55f, -1f, -0.32f);
            environment.add(shadowLight);
            environment.shadowMap = shadowLight;
            shadowBatch = new ModelBatch(new DepthShaderProvider());
        } catch (Throwable t) {
            shadows = false;
            shadowLight = null;
            environment.add(new DirectionalLight().set(0.96f, 0.89f, 0.78f, -0.55f, -1f, -0.32f));
        }

        buildModels();
        buildGrid();
        buildGizmos();
        Gdx.input.setInputProcessor(new EditorInput());
        emitSelection();
        status("مشهد فارغ • أضف مجسمًا من +");
    }

    private void buildModels() {
        long a = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;
        Material ground = mat(0.45f, 0.48f, 0.50f);
        Material white = mat(0.68f, 0.70f, 0.73f);
        Material warm = mat(0.72f, 0.48f, 0.22f);
        models[GROUND] = new ModelBuilder().createBox(8f, 0.28f, 8f, ground, a);
        models[CUBE] = new ModelBuilder().createBox(2f, 2f, 2f, white, a);
        models[SPHERE] = new ModelBuilder().createSphere(2f, 2f, 2f, 18, 12, white, a);
        models[CYLINDER] = new ModelBuilder().createCylinder(2f, 2.5f, 2f, 18, white, a);
        models[CONE] = new ModelBuilder().createCone(2.2f, 2.8f, 2.2f, 18, warm, a);
        models[PYRAMID] = new ModelBuilder().createCone(2.4f, 2.6f, 2.4f, 4, warm, a);
        models[ROCK] = new ModelBuilder().createSphere(2.2f, 1.45f, 1.85f, 10, 7, mat(0.42f, 0.43f, 0.44f), a);

        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        MeshPartBuilder trunk = mb.part("trunk", GL20.GL_TRIANGLES, a, mat(0.32f, 0.18f, 0.08f));
        trunk.setVertexTransform(new Matrix4().setToTranslation(0, 1.1f, 0));
        trunk.cylinder(0.36f, 2.2f, 0.36f, 9);
        MeshPartBuilder crown1 = mb.part("crown1", GL20.GL_TRIANGLES, a, mat(0.15f, 0.43f, 0.17f));
        crown1.setVertexTransform(new Matrix4().setToTranslation(0, 2.6f, 0));
        crown1.cone(2.2f, 3.1f, 2.2f, 12);
        MeshPartBuilder crown2 = mb.part("crown2", GL20.GL_TRIANGLES, a, mat(0.18f, 0.50f, 0.19f));
        crown2.setVertexTransform(new Matrix4().setToTranslation(0, 3.6f, 0));
        crown2.cone(1.5f, 2.2f, 1.5f, 12);
        models[TREE] = mb.end();

        mb = new ModelBuilder();
        mb.begin();
        MeshPartBuilder stem = mb.part("stem", GL20.GL_TRIANGLES, a, mat(0.29f, 0.18f, 0.08f));
        stem.setVertexTransform(new Matrix4().setToTranslation(0, 0.45f, 0));
        stem.cylinder(0.22f, 0.9f, 0.22f, 8);
        MeshPartBuilder leaf = mb.part("leaf", GL20.GL_TRIANGLES, a, mat(0.20f, 0.52f, 0.20f));
        leaf.setVertexTransform(new Matrix4().setToTranslation(0, 1.15f, 0));
        leaf.sphere(2.25f, 1.65f, 2.25f, 12, 8);
        models[BUSH] = mb.end();
    }

    private Material mat(float r, float g, float b) {
        return new Material(ColorAttribute.createDiffuse(new Color(r, g, b, 1)));
    }

    private Material gizmoMat(Color c) {
        return new Material(ColorAttribute.createDiffuse(c), new DepthTestAttribute(GL20.GL_ALWAYS, false));
    }

    private void buildGrid() {
        long a = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;
        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        Material minor = mat(0.26f, 0.28f, 0.31f);
        Material major = mat(0.38f, 0.40f, 0.43f);
        for (int i = -12; i <= 12; i++) {
            Material m = (i == 0 || i % 5 == 0) ? major : minor;
            MeshPartBuilder p1 = mb.part("gx" + i, GL20.GL_TRIANGLES, a, m);
            p1.setVertexTransform(new Matrix4().setToTranslation(0, -0.035f, i));
            p1.box(24f, 0.025f, 0.025f);
            MeshPartBuilder p2 = mb.part("gz" + i, GL20.GL_TRIANGLES, a, m);
            p2.setVertexTransform(new Matrix4().setToTranslation(i, -0.035f, 0));
            p2.box(0.025f, 0.025f, 24f);
        }
        gridModel = mb.end();
        gridInstance = new ModelInstance(gridModel);
    }

    private void buildGizmos() {
        long a = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;
        Material red = gizmoMat(new Color(1f, 0.12f, 0.10f, 1));
        Material green = gizmoMat(new Color(0.12f, 1f, 0.22f, 1));
        Material blue = gizmoMat(new Color(0.12f, 0.42f, 1f, 1));
        Material yellow = gizmoMat(new Color(1f, 0.78f, 0.12f, 1));

        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        axisParts(mb, a, red, green, blue, false);
        MeshPartBuilder center = mb.part("center", GL20.GL_TRIANGLES, a, yellow);
        center.box(0.26f, 0.26f, 0.26f);
        moveGizmoModel = mb.end();

        mb = new ModelBuilder();
        mb.begin();
        axisParts(mb, a, red, green, blue, true);
        scaleGizmoModel = mb.end();

        mb = new ModelBuilder();
        mb.begin();
        addArc(mb, a, red, Axis.X);
        addArc(mb, a, green, Axis.Y);
        addArc(mb, a, blue, Axis.Z);
        rotateGizmoModel = mb.end();
    }

    private void axisParts(ModelBuilder mb, long a, Material red, Material green, Material blue, boolean scale) {
        float len = 2.2f;
        MeshPartBuilder x = mb.part("x", GL20.GL_TRIANGLES, a, red);
        x.setVertexTransform(new Matrix4().setToTranslation(len * 0.5f, 0, 0).rotate(Vector3.Z, -90f));
        x.cylinder(0.09f, len, 0.09f, 8);
        MeshPartBuilder y = mb.part("y", GL20.GL_TRIANGLES, a, green);
        y.setVertexTransform(new Matrix4().setToTranslation(0, len * 0.5f, 0));
        y.cylinder(0.09f, len, 0.09f, 8);
        MeshPartBuilder z = mb.part("z", GL20.GL_TRIANGLES, a, blue);
        z.setVertexTransform(new Matrix4().setToTranslation(0, 0, len * 0.5f).rotate(Vector3.X, 90f));
        z.cylinder(0.09f, len, 0.09f, 8);
        if (scale) {
            MeshPartBuilder hx = mb.part("hx", GL20.GL_TRIANGLES, a, red);
            hx.setVertexTransform(new Matrix4().setToTranslation(len + 0.16f, 0, 0)); hx.box(0.34f, 0.34f, 0.34f);
            MeshPartBuilder hy = mb.part("hy", GL20.GL_TRIANGLES, a, green);
            hy.setVertexTransform(new Matrix4().setToTranslation(0, len + 0.16f, 0)); hy.box(0.34f, 0.34f, 0.34f);
            MeshPartBuilder hz = mb.part("hz", GL20.GL_TRIANGLES, a, blue);
            hz.setVertexTransform(new Matrix4().setToTranslation(0, 0, len + 0.16f)); hz.box(0.34f, 0.34f, 0.34f);
        } else {
            MeshPartBuilder tx = mb.part("tx", GL20.GL_TRIANGLES, a, red);
            tx.setVertexTransform(new Matrix4().setToTranslation(len + 0.18f, 0, 0).rotate(Vector3.Z, -90f)); tx.cone(0.34f, 0.58f, 0.34f, 8);
            MeshPartBuilder ty = mb.part("ty", GL20.GL_TRIANGLES, a, green);
            ty.setVertexTransform(new Matrix4().setToTranslation(0, len + 0.18f, 0)); ty.cone(0.34f, 0.58f, 0.34f, 8);
            MeshPartBuilder tz = mb.part("tz", GL20.GL_TRIANGLES, a, blue);
            tz.setVertexTransform(new Matrix4().setToTranslation(0, 0, len + 0.18f).rotate(Vector3.X, 90f)); tz.cone(0.34f, 0.58f, 0.34f, 8);
        }
    }

    private void addArc(ModelBuilder mb, long a, Material material, Axis axis) {
        MeshPartBuilder part = mb.part("arc" + axis, GL20.GL_TRIANGLES, a, material);
        float r = 2.05f;
        int segs = 18;
        float start = -70f, end = 95f;
        for (int i = 0; i < segs; i++) {
            float t0 = MathUtils.lerp(start, end, i / (float) segs);
            float t1 = MathUtils.lerp(start, end, (i + 1f) / segs);
            float a0 = t0 * MathUtils.degreesToRadians;
            float a1 = t1 * MathUtils.degreesToRadians;
            float c0 = MathUtils.cos(a0), s0 = MathUtils.sin(a0);
            float c1 = MathUtils.cos(a1), s1 = MathUtils.sin(a1);
            if (axis == Axis.Z) {
                float x0=r*c0,y0=r*s0,x1=r*c1,y1=r*s1;
                float dx=x1-x0,dy=y1-y0,len=(float)Math.sqrt(dx*dx+dy*dy);
                float ang=MathUtils.atan2(dy,dx)*MathUtils.radiansToDegrees;
                part.setVertexTransform(new Matrix4().setToTranslation((x0+x1)*.5f,(y0+y1)*.5f,0).rotate(Vector3.Z,ang));
                part.box(len,0.075f,0.075f);
            } else if (axis == Axis.Y) {
                float x0=r*c0,z0=r*s0,x1=r*c1,z1=r*s1;
                float dx=x1-x0,dz=z1-z0,len=(float)Math.sqrt(dx*dx+dz*dz);
                float ang=MathUtils.atan2(dz,dx)*MathUtils.radiansToDegrees;
                part.setVertexTransform(new Matrix4().setToTranslation((x0+x1)*.5f,0,(z0+z1)*.5f).rotate(Vector3.Y,-ang));
                part.box(len,0.075f,0.075f);
            } else {
                float y0=r*c0,z0=r*s0,y1=r*c1,z1=r*s1;
                float dy=y1-y0,dz=z1-z0,len=(float)Math.sqrt(dy*dy+dz*dz);
                float ang=MathUtils.atan2(dz,dy)*MathUtils.radiansToDegrees;
                part.setVertexTransform(new Matrix4().setToTranslation(0,(y0+y1)*.5f,(z0+z1)*.5f).rotate(Vector3.X,ang));
                part.box(0.075f,len,0.075f);
            }
        }
    }

    @Override
    public void render() {
        updateCamera();
        if (shadows && shadowLight != null && shadowBatch != null && objects.size > 0) {
            shadowLight.begin(pivot, camera.direction);
            shadowBatch.begin(shadowLight.getCamera());
            for (SceneObj o : objects) shadowBatch.render(o.instance);
            shadowBatch.end();
            shadowLight.end();
        }

        Gdx.gl.glViewport(0, 0, Gdx.graphics.getBackBufferWidth(), Gdx.graphics.getBackBufferHeight());
        Gdx.gl.glClearColor(0.105f, 0.12f, 0.14f, 1f);
        Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT | GL20.GL_DEPTH_BUFFER_BIT);
        sceneBatch.begin(camera);
        sceneBatch.render(gridInstance, environment);
        for (SceneObj o : objects) sceneBatch.render(o.instance, environment);
        sceneBatch.end();

        if (hasSelection()) {
            refreshGizmo();
            Gdx.gl.glClear(GL20.GL_DEPTH_BUFFER_BIT);
            gizmoBatch.begin(camera);
            gizmoBatch.render(gizmoInstance);
            gizmoBatch.end();
        }
    }

    private void updateCamera() {
        float py = MathUtils.sinDeg(pitch) * distance;
        float h = MathUtils.cosDeg(pitch) * distance;
        float px = MathUtils.sinDeg(yaw) * h;
        float pz = MathUtils.cosDeg(yaw) * h;
        camera.position.set(pivot.x + px, pivot.y + py, pivot.z + pz);
        camera.up.set(Vector3.Y);
        camera.lookAt(pivot);
        camera.update();
    }

    private void refreshGizmo() {
        SceneObj o = objects.get(selected);
        float s = MathUtils.clamp(camera.position.dst(o.data.x,o.data.y,o.data.z) * 0.075f, 0.70f, 3.8f);
        Model m = tool == Tool.ROTATE ? rotateGizmoModel : (tool == Tool.SCALE ? scaleGizmoModel : moveGizmoModel);
        if (gizmoInstance == null || gizmoInstance.model != m) gizmoInstance = new ModelInstance(m);
        gizmoInstance.transform.setToTranslation(o.data.x,o.data.y,o.data.z).scale(s,s,s);
    }

    public void setUiListener(UiListener l) { ui = l; emitSelection(); }
    public void setTool(Tool t) { tool=t; dragAxis=Axis.NONE; status(toolName()); }
    public Tool getTool(){ return tool; }

    public void addObject(int type) {
        post(() -> {
            pushUndo();
            ObjData d = new ObjData();
            d.type=type;
            d.x=pivot.x; d.z=pivot.z;
            d.y = type==GROUND ? 0f : 1.2f;
            if (type==GROUND) { d.sx=1.35f; d.sy=1f; d.sz=1.35f; }
            else { d.sx=d.sy=d.sz=1f; }
            SceneObj o = makeObj(d);
            objects.add(o); selected=objects.size-1;
            pivot.set(d.x,d.y,d.z);
            emitSelection(); status("تمت إضافة " + typeName(type));
        });
    }

    public void deleteSelected(){ post(() -> { if(!hasSelection()) return; pushUndo(); objects.removeIndex(selected); selected=-1; pivot.set(0,0.8f,0); emitSelection(); status("تم الحذف"); }); }
    public void duplicateSelected(){ post(() -> { if(!hasSelection()) return; pushUndo(); ObjData n=new ObjData(objects.get(selected).data); n.x+=1.2f; n.z+=1.2f; objects.add(makeObj(n)); selected=objects.size-1; updatePivotFromSelection(); emitSelection(); status("تم النسخ"); }); }
    public void focusSelected(){ post(() -> { if(!hasSelection()) return; updatePivotFromSelection(); distance=MathUtils.clamp(maxScale(objects.get(selected).data)*8f+8f,9f,28f); }); }
    public void newScene(){ post(() -> { pushUndo(); objects.clear(); selected=-1; pivot.set(0,0.8f,0); emitSelection(); status("مشهد فارغ جديد"); }); }
    public void undo(){ post(() -> { if(undo.size==0){status("لا يوجد تراجع");return;} Snapshot s=undo.pop(); restore(s); status("تم التراجع"); }); }
    public void save(){ post(() -> { SaveData s=new SaveData(); for(SceneObj o:objects)s.objects.add(new ObjData(o.data)); Gdx.app.getPreferences("mini-blender-v4").putString("scene",new Json().toJson(s)).flush(); status("تم الحفظ"); }); }
    public void load(){ post(() -> { String s=Gdx.app.getPreferences("mini-blender-v4").getString("scene",""); if(s.isEmpty()){status("لا يوجد حفظ");return;} try{pushUndo(); SaveData d=new Json().fromJson(SaveData.class,s); objects.clear(); if(d.objects!=null)for(ObjData od:d.objects)objects.add(makeObj(od)); selected=-1; pivot.set(0,0.8f,0); emitSelection();status("تم الفتح");}catch(Throwable t){status("تعذر الفتح");} }); }
    public void toggleShadows(boolean on){ post(() -> { shadows=on && shadowLight!=null; if(shadowLight!=null)environment.shadowMap=shadows?shadowLight:null; }); }

    private SceneObj makeObj(ObjData d){ ModelInstance i=new ModelInstance(models[MathUtils.clamp(d.type,0,models.length-1)]); SceneObj o=new SceneObj(d,i); apply(o); return o; }
    private void apply(SceneObj o){ ObjData d=o.data; o.instance.transform.idt().translate(d.x,d.y,d.z).rotate(Vector3.X,d.rx).rotate(Vector3.Y,d.ry).rotate(Vector3.Z,d.rz).scale(d.sx,d.sy,d.sz); }
    private float maxScale(ObjData d){ return Math.max(Math.abs(d.sx),Math.max(Math.abs(d.sy),Math.abs(d.sz))); }
    private void updatePivotFromSelection(){ if(hasSelection()){ObjData d=objects.get(selected).data;pivot.set(d.x,d.y,d.z);} }

    private void pushUndo(){ Snapshot s=new Snapshot(); for(SceneObj o:objects)s.objects.add(new ObjData(o.data)); undo.add(s); if(undo.size>25)undo.removeIndex(0); }
    private void restore(Snapshot s){ objects.clear(); for(ObjData d:s.objects)objects.add(makeObj(d)); selected=-1; pivot.set(0,0.8f,0); emitSelection(); }
    private void post(Runnable r){ if(Gdx.app!=null)Gdx.app.postRunnable(r); }

    private int pickObject(float sx,float sy){
        Ray ray=camera.getPickRay(sx,sy); int best=-1; float bestD=Float.MAX_VALUE;
        for(int i=0;i<objects.size;i++){
            SceneObj o=objects.get(i); ObjData d=o.data; Vector3 dims=baseDims(d.type,tmp3a);
            float hx=Math.abs(dims.x*d.sx)*.5f, hy=Math.abs(dims.y*d.sy)*.5f, hz=Math.abs(dims.z*d.sz)*.5f;
            tmpBounds.set(tmp3b.set(d.x-hx,d.y-hy,d.z-hz),tmp3c.set(d.x+hx,d.y+hy,d.z+hz));
            if(Intersector.intersectRayBoundsFast(ray,tmpBounds)){
                float dist=camera.position.dst2(d.x,d.y,d.z); if(dist<bestD){bestD=dist;best=i;}
            }
        }
        return best;
    }

    private Vector3 baseDims(int type,Vector3 out){
        switch(type){
            case GROUND:return out.set(8,.3f,8);
            case CYLINDER:return out.set(2,2.5f,2);
            case CONE:return out.set(2.2f,2.8f,2.2f);
            case PYRAMID:return out.set(2.4f,2.6f,2.4f);
            case TREE:return out.set(2.3f,4.8f,2.3f);
            case ROCK:return out.set(2.2f,1.45f,1.85f);
            case BUSH:return out.set(2.3f,2f,2.3f);
            default:return out.set(2,2,2);
        }
    }

    private Axis hitAxis(float sx,float sy){
        if(!hasSelection())return Axis.NONE;
        if(tool==Tool.ROTATE)return hitRotationArc(sx,sy);
        ObjData d=objects.get(selected).data; float gs=gizmoWorldScale(d);
        project(d.x,d.y,d.z,tmp2a);
        Axis best=Axis.NONE; float bestD=34f;
        Axis[] axes={Axis.X,Axis.Y,Axis.Z};
        for(Axis a:axes){ Vector3 v=axisVec(a,tmp3a).scl(gs*2.45f).add(d.x,d.y,d.z); project(v.x,v.y,v.z,tmp2b); float dd=pointSegmentDistance(sx,sy,tmp2a.x,tmp2a.y,tmp2b.x,tmp2b.y); if(dd<bestD){bestD=dd;best=a;} }
        return best;
    }

    private Axis hitRotationArc(float sx,float sy){
        ObjData d=objects.get(selected).data; float gs=gizmoWorldScale(d); Axis best=Axis.NONE; float bestD=31f; Vector2 bestTan=new Vector2(1,0);
        Axis[] axes={Axis.X,Axis.Y,Axis.Z};
        for(Axis a:axes){
            Vector2 prev=new Vector2(); boolean hp=false;
            for(int i=0;i<=18;i++){
                float deg=MathUtils.lerp(-70f,95f,i/18f); Vector3 wp=arcPoint(a,deg,gs*2.05f,tmp3a).add(d.x,d.y,d.z); Vector2 cur=new Vector2(); project(wp.x,wp.y,wp.z,cur);
                if(hp){float dd=pointSegmentDistance(sx,sy,prev.x,prev.y,cur.x,cur.y); if(dd<bestD){bestD=dd;best=a;bestTan.set(cur).sub(prev).nor();}}
                prev.set(cur);hp=true;
            }
        }
        if(best!=Axis.NONE)rotationTangent.set(bestTan);
        return best;
    }

    private float gizmoWorldScale(ObjData d){ return MathUtils.clamp(camera.position.dst(d.x,d.y,d.z)*.075f,.70f,3.8f); }
    private Vector3 axisVec(Axis a,Vector3 out){ if(a==Axis.X)return out.set(1,0,0); if(a==Axis.Y)return out.set(0,1,0); return out.set(0,0,1); }
    private Vector3 arcPoint(Axis a,float deg,float r,Vector3 out){float rad=deg*MathUtils.degreesToRadians,c=MathUtils.cos(rad)*r,s=MathUtils.sin(rad)*r;if(a==Axis.X)return out.set(0,c,s);if(a==Axis.Y)return out.set(c,0,s);return out.set(c,s,0);}

    private void project(float x,float y,float z,Vector2 out){ Vector3 p=tmp3b.set(x,y,z); camera.project(p); out.set(p.x,Gdx.graphics.getHeight()-p.y); }
    private float pointSegmentDistance(float px,float py,float ax,float ay,float bx,float by){float vx=bx-ax,vy=by-ay,wx=px-ax,wy=py-ay,c2=vx*vx+vy*vy;if(c2<.001f)return Vector2.dst(px,py,ax,ay);float t=MathUtils.clamp((wx*vx+wy*vy)/c2,0f,1f);return Vector2.dst(px,py,ax+t*vx,ay+t*vy);}

    private void beginTransform(Axis a,float x,float y){dragAxis=a;transforming=true;orbiting=false;lastX=x;lastY=y;pushUndo();}
    private void transformDrag(float x,float y){
        if(!hasSelection())return; float dx=x-lastX,dy=y-lastY; ObjData d=objects.get(selected).data;
        if(dragAxis==Axis.FREE){
            if(tool==Tool.MOVE){ Vector3 right=new Vector3(camera.direction).crs(Vector3.Y).nor(); Vector3 up=new Vector3(right).crs(camera.direction).nor(); float k=distance*.0027f; d.x+=right.x*dx*k+up.x*(-dy)*k;d.y+=right.y*dx*k+up.y*(-dy)*k;d.z+=right.z*dx*k+up.z*(-dy)*k; }
            else if(tool==Tool.SCALE){float f=(float)Math.exp((dx-dy)*.0065f);d.sx=clampScale(d.sx*f);d.sy=clampScale(d.sy*f);d.sz=clampScale(d.sz*f);}
            else {d.ry+=dx*.34f;d.rx-=dy*.34f;}
        } else if(tool==Tool.MOVE){
            float amount=axisScreenDelta(dragAxis,dx,dy,d); if(dragAxis==Axis.X)d.x+=amount;else if(dragAxis==Axis.Y)d.y+=amount;else d.z+=amount;
        } else if(tool==Tool.SCALE){
            float pix=axisProjectedPixels(dragAxis,d); if(pix<12)pix=80; float along=axisScreenPixelDelta(dragAxis,dx,dy,d); float f=MathUtils.clamp(1f+along/pix,.72f,1.35f); if(dragAxis==Axis.X)d.sx=clampScale(d.sx*f);else if(dragAxis==Axis.Y)d.sy=clampScale(d.sy*f);else d.sz=clampScale(d.sz*f);
        } else {
            float along=dx*rotationTangent.x+dy*rotationTangent.y; float sign=(dragAxis==Axis.X||dragAxis==Axis.Z)?-1f:1f; float ang=along*.55f*sign; if(dragAxis==Axis.X)d.rx+=ang;else if(dragAxis==Axis.Y)d.ry+=ang;else d.rz+=ang;
        }
        apply(objects.get(selected)); pivot.set(d.x,d.y,d.z); emitSelection(); lastX=x;lastY=y;
    }

    private float clampScale(float v){return MathUtils.clamp(v,.08f,12f);}
    private float axisScreenDelta(Axis a,float dx,float dy,ObjData d){float pixels=axisScreenPixelDelta(a,dx,dy,d);float len=axisProjectedPixels(a,d);if(len<8)return 0;return pixels*(gizmoWorldScale(d)*2.45f/len);}
    private float axisScreenPixelDelta(Axis a,float dx,float dy,ObjData d){Vector2 dir=axisScreenDir(a,d,tmp2a);return dx*dir.x+dy*dir.y;}
    private float axisProjectedPixels(Axis a,ObjData d){project(d.x,d.y,d.z,tmp2a);Vector3 e=axisVec(a,tmp3a).scl(gizmoWorldScale(d)*2.45f).add(d.x,d.y,d.z);project(e.x,e.y,e.z,tmp2b);return tmp2a.dst(tmp2b);}
    private Vector2 axisScreenDir(Axis a,ObjData d,Vector2 out){project(d.x,d.y,d.z,tmp2a);Vector3 e=axisVec(a,tmp3a).scl(gizmoWorldScale(d)*2.45f).add(d.x,d.y,d.z);project(e.x,e.y,e.z,tmp2b);return out.set(tmp2b).sub(tmp2a).nor();}

    private class EditorInput extends InputAdapter {
        @Override public boolean touchDown(int x,int y,int pointer,int button){
            if(Gdx.input.isTouched(1)){ initTwoFinger(); return true; }
            if(ignoreFirstSingleAfterPinch){lastX=x;lastY=y;ignoreFirstSingleAfterPinch=false;return true;}
            lastX=x;lastY=y; Axis h=hitAxis(x,y); if(h!=Axis.NONE){beginTransform(h,x,y);return true;}
            int obj=pickObject(x,y); if(obj>=0){selected=obj;updatePivotFromSelection();emitSelection();beginTransform(Axis.FREE,x,y);return true;}
            selected=-1;emitSelection();orbiting=true;transforming=false;return true;
        }
        @Override public boolean touchDragged(int x,int y,int pointer){
            if(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1)){ if(!twoFingerActive)initTwoFinger();else handleTwoFinger(); return true; }
            if(twoFingerActive)return true;
            if(transforming){transformDrag(x,y);return true;}
            if(orbiting){float dx=x-lastX,dy=y-lastY;yaw-=dx*.24f;pitch=MathUtils.clamp(pitch+dy*.20f,8f,82f);lastX=x;lastY=y;return true;}
            return true;
        }
        @Override public boolean touchUp(int x,int y,int pointer,int button){
            if(twoFingerActive && !(Gdx.input.isTouched(0)&&Gdx.input.isTouched(1))){twoFingerActive=false;ignoreFirstSingleAfterPinch=true;}
            if(!Gdx.input.isTouched(0)&&!Gdx.input.isTouched(1)){transforming=false;orbiting=false;dragAxis=Axis.NONE;twoFingerActive=false;}
            return true;
        }
        private void initTwoFinger(){twoFingerActive=true;transforming=false;orbiting=false;float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);lastMidX=(x0+x1)*.5f;lastMidY=(y0+y1)*.5f;lastPinch=Vector2.dst(x0,y0,x1,y1);}
        private void handleTwoFinger(){float x0=Gdx.input.getX(0),y0=Gdx.input.getY(0),x1=Gdx.input.getX(1),y1=Gdx.input.getY(1);float mx=(x0+x1)*.5f,my=(y0+y1)*.5f,p=Vector2.dst(x0,y0,x1,y1);float dx=mx-lastMidX,dy=my-lastMidY;yaw-=dx*.20f;pitch=MathUtils.clamp(pitch+dy*.17f,8f,82f);distance=MathUtils.clamp(distance-(p-lastPinch)*.028f,4.5f,80f);lastMidX=mx;lastMidY=my;lastPinch=p;}
    }

    private void status(String s){if(ui!=null)ui.onStatus(s);}
    private void emitSelection(){if(ui==null)return;if(!hasSelection()){ui.onSelection("لا يوجد مجسم محدد");return;}ObjData d=objects.get(selected).data;ui.onSelection(typeName(d.type)+"  X:"+one(d.x)+" Y:"+one(d.y)+" Z:"+one(d.z)+"  |  S "+one(d.sx)+","+one(d.sy)+","+one(d.sz));}
    private String one(float v){return String.format(java.util.Locale.US,"%.1f",v);}
    private boolean hasSelection(){return selected>=0&&selected<objects.size;}
    private String toolName(){return tool==Tool.MOVE?"تحريك • اسحب المجسم بحرية أو اسحب محورًا":tool==Tool.ROTATE?"تدوير • اسحب المجسم أو القوس الملون":"حجم • اسحب المجسم لكل المحاور أو محورًا واحدًا";}
    private String typeName(int t){String[] n={"أرض","مكعب","كرة","أسطوانة","مخروط","هرم","شجرة","صخرة","شجيرة"};return n[MathUtils.clamp(t,0,n.length-1)];}

    @Override public void resize(int w,int h){if(camera!=null){camera.viewportWidth=w;camera.viewportHeight=h;camera.update();}}
    @Override public void dispose(){if(sceneBatch!=null)sceneBatch.dispose();if(gizmoBatch!=null)gizmoBatch.dispose();if(shadowBatch!=null)shadowBatch.dispose();if(shadowLight!=null)shadowLight.dispose();if(gridModel!=null)gridModel.dispose();if(moveGizmoModel!=null)moveGizmoModel.dispose();if(scaleGizmoModel!=null)scaleGizmoModel.dispose();if(rotateGizmoModel!=null)rotateGizmoModel.dispose();for(Model m:models)if(m!=null)m.dispose();}

    private static class SceneObj { final ObjData data; final ModelInstance instance; SceneObj(ObjData d,ModelInstance i){data=d;instance=i;} }
    public static class ObjData { public int type; public float x,y,z,rx,ry,rz,sx=1,sy=1,sz=1; public ObjData(){} ObjData(ObjData o){type=o.type;x=o.x;y=o.y;z=o.z;rx=o.rx;ry=o.ry;rz=o.rz;sx=o.sx;sy=o.sy;sz=o.sz;} }
    public static class SaveData { public Array<ObjData> objects=new Array<>(); }
    private static class Snapshot { Array<ObjData> objects=new Array<>(); }
}
