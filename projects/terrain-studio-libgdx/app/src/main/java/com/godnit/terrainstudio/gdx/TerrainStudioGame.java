package com.godnit.terrainstudio.gdx;

import com.badlogic.gdx.ApplicationAdapter;
import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.InputAdapter;
import com.badlogic.gdx.Preferences;
import com.badlogic.gdx.graphics.Color;
import com.badlogic.gdx.graphics.GL20;
import com.badlogic.gdx.graphics.Mesh;
import com.badlogic.gdx.graphics.PerspectiveCamera;
import com.badlogic.gdx.graphics.VertexAttribute;
import com.badlogic.gdx.graphics.VertexAttributes;
import com.badlogic.gdx.graphics.g3d.Environment;
import com.badlogic.gdx.graphics.g3d.Material;
import com.badlogic.gdx.graphics.g3d.Model;
import com.badlogic.gdx.graphics.g3d.ModelBatch;
import com.badlogic.gdx.graphics.g3d.ModelInstance;
import com.badlogic.gdx.graphics.g3d.attributes.ColorAttribute;
import com.badlogic.gdx.graphics.g3d.environment.DirectionalShadowLight;
import com.badlogic.gdx.graphics.g3d.model.MeshPart;
import com.badlogic.gdx.graphics.g3d.model.Node;
import com.badlogic.gdx.graphics.g3d.model.NodePart;
import com.badlogic.gdx.graphics.g3d.utils.DepthShaderProvider;
import com.badlogic.gdx.graphics.g3d.utils.MeshPartBuilder;
import com.badlogic.gdx.graphics.g3d.utils.ModelBuilder;
import com.badlogic.gdx.math.MathUtils;
import com.badlogic.gdx.math.Matrix4;
import com.badlogic.gdx.math.Vector2;
import com.badlogic.gdx.math.Vector3;
import com.badlogic.gdx.math.collision.Ray;
import com.badlogic.gdx.utils.Array;
import com.badlogic.gdx.utils.Disposable;
import com.badlogic.gdx.utils.Json;

public class TerrainStudioGame extends ApplicationAdapter {
    public enum Tool {
        CAMERA, SELECT,
        RAISE, LOWER, SMOOTH, FLATTEN, NOISE, PAINT,
        TREE, ROCK, BUSH, CRATE, PILLAR,
        DELETE
    }

    public interface StatusListener { void onStatus(String text); }
    public interface SelectionListener { void onSelection(String text); }

    private PerspectiveCamera camera;
    private ModelBatch modelBatch;
    private ModelBatch shadowBatch;
    private Environment environment;
    private DirectionalShadowLight shadowLight;
    private boolean shadowsEnabled = true;

    private TerrainSurface terrain;
    private Model treeModel;
    private Model rockModel;
    private Model bushModel;
    private Model crateModel;
    private Model pillarModel;
    private Model gizmoModel;
    private ModelInstance gizmoInstance;

    private final Array<Prop> props = new Array<>();
    private final Array<Snapshot> undo = new Array<>();
    private int selectedIndex = -1;
    private boolean selectionDragSnapshotTaken = false;

    private volatile Tool tool = Tool.CAMERA;
    private volatile float brushRadius = 2.8f;
    private volatile float brushStrength = 0.42f;
    private final Color paintColor = new Color(0.30f, 0.52f, 0.20f, 1f);
    private float flattenHeight = 0f;

    private float yaw = 42f;
    private float pitch = 48f;
    private float distance = 30f;
    private final Vector3 target = new Vector3(0, 0, 0);
    private final Vector3 hit = new Vector3();
    private float lastX, lastY;
    private float lastMidX, lastMidY, lastPinch;
    private boolean gestureWasTwoFinger;
    private StatusListener statusListener;
    private SelectionListener selectionListener;

    @Override
    public void create() {
        Gdx.gl.glEnable(GL20.GL_DEPTH_TEST);
        Gdx.gl.glEnable(GL20.GL_CULL_FACE);
        Gdx.gl.glCullFace(GL20.GL_BACK);

        camera = new PerspectiveCamera(58f, Gdx.graphics.getWidth(), Gdx.graphics.getHeight());
        camera.near = 0.35f;
        camera.far = 120f;
        updateCamera();

        modelBatch = new ModelBatch();
        environment = new Environment();
        environment.set(new ColorAttribute(ColorAttribute.AmbientLight, 0.48f, 0.50f, 0.52f, 1f));

        try {
            shadowLight = new DirectionalShadowLight(512, 512, 42f, 42f, 1f, 80f);
            shadowLight.set(0.92f, 0.86f, 0.75f, -0.65f, -1.0f, -0.35f);
            environment.add(shadowLight);
            environment.shadowMap = shadowLight;
            shadowBatch = new ModelBatch(new DepthShaderProvider());
        } catch (Throwable t) {
            shadowsEnabled = false;
            shadowLight = null;
            shadowBatch = null;
            environment.add(new com.badlogic.gdx.graphics.g3d.environment.DirectionalLight()
                    .set(0.92f, 0.86f, 0.75f, -0.65f, -1.0f, -0.35f));
        }

        terrain = new TerrainSurface(49, 36f);
        buildPropModels();
        buildGizmo();
        Gdx.input.setInputProcessor(new EditorInput());
        emitSelection();
        status("جاهز للتحرير");
    }

    private void buildPropModels() {
        final long attrs = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;

        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        Material trunkMat = new Material(ColorAttribute.createDiffuse(new Color(0.34f, 0.19f, 0.08f, 1f)));
        Material leafMat = new Material(ColorAttribute.createDiffuse(new Color(0.17f, 0.46f, 0.17f, 1f)));
        MeshPartBuilder trunk = mb.part("trunk", GL20.GL_TRIANGLES, attrs, trunkMat);
        trunk.setVertexTransform(new Matrix4().setToTranslation(0f, 1.15f, 0f));
        trunk.cylinder(0.38f, 2.3f, 0.38f, 9);
        MeshPartBuilder crownA = mb.part("crownA", GL20.GL_TRIANGLES, attrs, leafMat);
        crownA.setVertexTransform(new Matrix4().setToTranslation(0f, 2.7f, 0f));
        crownA.cone(2.15f, 3.0f, 2.15f, 11);
        MeshPartBuilder crownB = mb.part("crownB", GL20.GL_TRIANGLES, attrs, leafMat);
        crownB.setVertexTransform(new Matrix4().setToTranslation(0f, 3.65f, 0f));
        crownB.cone(1.55f, 2.35f, 1.55f, 11);
        treeModel = mb.end();

        Material rockMat = new Material(ColorAttribute.createDiffuse(new Color(0.42f, 0.44f, 0.42f, 1f)));
        rockModel = new ModelBuilder().createSphere(1.7f, 1.15f, 1.5f, 9, 6, rockMat, attrs);

        mb = new ModelBuilder();
        mb.begin();
        Material bushStem = new Material(ColorAttribute.createDiffuse(new Color(0.26f, 0.18f, 0.08f, 1f)));
        Material bushLeaf = new Material(ColorAttribute.createDiffuse(new Color(0.20f, 0.55f, 0.20f, 1f)));
        MeshPartBuilder stem = mb.part("stem", GL20.GL_TRIANGLES, attrs, bushStem);
        stem.setVertexTransform(new Matrix4().setToTranslation(0f, 0.45f, 0f));
        stem.cylinder(0.24f, 0.9f, 0.24f, 8);
        MeshPartBuilder bush = mb.part("bush", GL20.GL_TRIANGLES, attrs, bushLeaf);
        bush.setVertexTransform(new Matrix4().setToTranslation(0f, 1.15f, 0f));
        bush.sphere(2.15f, 1.55f, 2.15f, 10, 7);
        bushModel = mb.end();

        Material crateMat = new Material(ColorAttribute.createDiffuse(new Color(0.52f, 0.31f, 0.13f, 1f)));
        crateModel = new ModelBuilder().createBox(1.65f, 1.65f, 1.65f, crateMat, attrs);

        Material pillarMat = new Material(ColorAttribute.createDiffuse(new Color(0.63f, 0.63f, 0.60f, 1f)));
        pillarModel = new ModelBuilder().createCylinder(1.15f, 3.25f, 1.15f, 12, pillarMat, attrs);
    }

    private void buildGizmo() {
        final long attrs = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;
        Material red = new Material(ColorAttribute.createDiffuse(new Color(0.95f, 0.18f, 0.16f, 1f)));
        Material green = new Material(ColorAttribute.createDiffuse(new Color(0.18f, 0.92f, 0.28f, 1f)));
        Material blue = new Material(ColorAttribute.createDiffuse(new Color(0.16f, 0.42f, 0.98f, 1f)));
        Material centerMat = new Material(ColorAttribute.createDiffuse(new Color(1.0f, 0.82f, 0.14f, 1f)));

        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        MeshPartBuilder xAxis = mb.part("x", GL20.GL_TRIANGLES, attrs, red);
        xAxis.setVertexTransform(new Matrix4().setToTranslation(1.25f, 0.14f, 0f));
        xAxis.box(2.5f, 0.10f, 0.10f);
        MeshPartBuilder yAxis = mb.part("y", GL20.GL_TRIANGLES, attrs, green);
        yAxis.setVertexTransform(new Matrix4().setToTranslation(0f, 1.38f, 0f));
        yAxis.box(0.10f, 2.75f, 0.10f);
        MeshPartBuilder zAxis = mb.part("z", GL20.GL_TRIANGLES, attrs, blue);
        zAxis.setVertexTransform(new Matrix4().setToTranslation(0f, 0.14f, 1.25f));
        zAxis.box(0.10f, 0.10f, 2.5f);
        MeshPartBuilder center = mb.part("center", GL20.GL_TRIANGLES, attrs, centerMat);
        center.setVertexTransform(new Matrix4().setToTranslation(0f, 0.14f, 0f));
        center.box(0.32f, 0.32f, 0.32f);
        gizmoModel = mb.end();
        gizmoInstance = new ModelInstance(gizmoModel);
    }

    @Override
    public void render() {
        updateCamera();
        refreshGizmoTransform();

        if (shadowsEnabled && shadowLight != null && shadowBatch != null) {
            shadowLight.begin(target, camera.direction);
            shadowBatch.begin(shadowLight.getCamera());
            shadowBatch.render(terrain.instance);
            for (Prop p : props) shadowBatch.render(p.instance);
            shadowBatch.end();
            shadowLight.end();
        }

        Gdx.gl.glViewport(0, 0, Gdx.graphics.getBackBufferWidth(), Gdx.graphics.getBackBufferHeight());
        Gdx.gl.glClearColor(0.40f, 0.67f, 0.87f, 1f);
        Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT | GL20.GL_DEPTH_BUFFER_BIT);

        modelBatch.begin(camera);
        modelBatch.render(terrain.instance, environment);
        for (Prop p : props) modelBatch.render(p.instance, environment);
        if (hasSelection() && gizmoInstance != null) modelBatch.render(gizmoInstance, environment);
        modelBatch.end();
    }

    private void updateCamera() {
        float py = MathUtils.sinDeg(pitch) * distance;
        float horizontal = MathUtils.cosDeg(pitch) * distance;
        float px = MathUtils.sinDeg(yaw) * horizontal;
        float pz = MathUtils.cosDeg(yaw) * horizontal;
        camera.position.set(target.x + px, target.y + py, target.z + pz);
        camera.up.set(Vector3.Y);
        camera.lookAt(target);
        camera.update();
    }

    private void refreshGizmoTransform() {
        if (!hasSelection() || gizmoInstance == null) return;
        Prop p = props.get(selectedIndex);
        float y = terrain.sampleHeight(p.data.x, p.data.z) + p.data.yOffset;
        float s = MathUtils.clamp(distance / 27f, 0.72f, 1.45f);
        gizmoInstance.transform.setToTranslation(p.data.x, y + 0.08f, p.data.z).scale(s, s, s);
    }

    public void setStatusListener(StatusListener listener) { this.statusListener = listener; }
    public void setSelectionListener(SelectionListener listener) {
        this.selectionListener = listener;
        if (Gdx.app != null) runOnGameThread(this::emitSelection);
    }

    public void setTool(Tool value) {
        tool = value;
        if (value == Tool.SELECT) status("اضغط مجسمًا لتحديده ثم اسحبه");
        else status("الأداة: " + arabicTool(value));
    }

    public void setBrushRadius(float value) { brushRadius = MathUtils.clamp(value, 0.7f, 6.5f); }
    public void setBrushStrength(float value) { brushStrength = MathUtils.clamp(value, 0.05f, 1.0f); }

    public void setPaintColor(final Color color) {
        runOnGameThread(() -> paintColor.set(color));
    }

    public void setShadowsEnabled(boolean enabled) {
        runOnGameThread(() -> {
            shadowsEnabled = enabled && shadowLight != null;
            if (shadowLight != null) environment.shadowMap = shadowsEnabled ? shadowLight : null;
            status(shadowsEnabled ? "تم تشغيل الظلال" : "تم إيقاف الظلال");
        });
    }

    public void resetView() {
        runOnGameThread(() -> {
            yaw = 42f;
            pitch = 48f;
            distance = 30f;
            target.set(0f, 0f, 0f);
            status("تمت إعادة الكاميرا");
        });
    }

    public void clearSelection() {
        runOnGameThread(() -> {
            selectedIndex = -1;
            emitSelection();
            status("تم إلغاء التحديد");
        });
    }

    public void nudgeSelected(float rightAmount, float forwardAmount) {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            pushUndo();
            Vector3 forward = new Vector3(camera.direction.x, 0f, camera.direction.z);
            if (forward.len2() < 0.0001f) forward.set(0f, 0f, -1f);
            else forward.nor();
            Vector3 right = new Vector3(forward).crs(Vector3.Y).nor();
            Prop p = props.get(selectedIndex);
            float nx = p.data.x + right.x * rightAmount + forward.x * forwardAmount;
            float nz = p.data.z + right.z * rightAmount + forward.z * forwardAmount;
            if (!terrain.inside(nx, nz)) { status("وصل العنصر إلى حافة الخريطة"); return; }
            p.data.x = nx;
            p.data.z = nz;
            applyPropTransform(p);
            emitSelection();
        });
    }

    public void raiseSelected(float delta) {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            pushUndo();
            Prop p = props.get(selectedIndex);
            p.data.yOffset = MathUtils.clamp(p.data.yOffset + delta, -4f, 10f);
            applyPropTransform(p);
            emitSelection();
        });
    }

    public void rotateSelected(float degrees) {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            pushUndo();
            Prop p = props.get(selectedIndex);
            p.data.rotation = (p.data.rotation + degrees) % 360f;
            if (p.data.rotation < 0f) p.data.rotation += 360f;
            applyPropTransform(p);
            emitSelection();
        });
    }

    public void scaleSelected(float factor) {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            pushUndo();
            Prop p = props.get(selectedIndex);
            p.data.scale = MathUtils.clamp(p.data.scale * factor, 0.25f, 4.0f);
            applyPropTransform(p);
            emitSelection();
        });
    }

    public void resetSelectedTransform() {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            pushUndo();
            Prop p = props.get(selectedIndex);
            p.data.rotation = 0f;
            p.data.scale = 1f;
            p.data.yOffset = 0f;
            applyPropTransform(p);
            emitSelection();
            status("تمت إعادة تحويلات العنصر");
        });
    }

    public void duplicateSelected() {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            Prop src = props.get(selectedIndex);
            pushUndo();
            float nx = MathUtils.clamp(src.data.x + 1.25f, -terrain.half + 0.2f, terrain.half - 0.2f);
            float nz = MathUtils.clamp(src.data.z + 1.25f, -terrain.half + 0.2f, terrain.half - 0.2f);
            addProp(src.data.type, nx, nz, src.data.rotation, src.data.scale, src.data.yOffset, false);
            selectedIndex = props.size - 1;
            emitSelection();
            status("تم نسخ العنصر");
        });
    }

    public void deleteSelected() {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            pushUndo();
            props.removeIndex(selectedIndex);
            selectedIndex = -1;
            emitSelection();
            status("تم حذف العنصر");
        });
    }

    public void focusSelected() {
        runOnGameThread(() -> {
            if (!hasSelection()) { status("حدد مجسمًا أولًا"); return; }
            Prop p = props.get(selectedIndex);
            target.set(p.data.x, terrain.sampleHeight(p.data.x, p.data.z) + p.data.yOffset + 0.7f, p.data.z);
            distance = MathUtils.clamp(10f + p.data.scale * 2.5f, 9f, 18f);
            status("تم تركيز الكاميرا على العنصر");
        });
    }

    public void undo() {
        runOnGameThread(() -> {
            if (undo.size == 0) { status("لا يوجد تراجع"); return; }
            Snapshot s = undo.pop();
            terrain.restore(s.heights, s.colors);
            restoreProps(s.props);
            selectedIndex = -1;
            emitSelection();
            status("تم التراجع");
        });
    }

    public void save() {
        runOnGameThread(() -> {
            SaveData data = new SaveData();
            data.heights = terrain.heights.clone();
            data.colors = terrain.colors.clone();
            data.props = copyPropData();
            String json = new Json().toJson(data);
            Preferences prefs = Gdx.app.getPreferences("terrain-studio-x");
            prefs.putString("map", json).flush();
            status("تم حفظ الخريطة");
        });
    }

    public void load() {
        runOnGameThread(() -> {
            Preferences prefs = Gdx.app.getPreferences("terrain-studio-x");
            String text = prefs.getString("map", "");
            if (text.length() == 0) { status("لا توجد خريطة محفوظة"); return; }
            try {
                pushUndo();
                SaveData data = new Json().fromJson(SaveData.class, text);
                if (data.heights != null && data.colors != null) terrain.restore(data.heights, data.colors);
                restoreProps(data.props == null ? new Array<PropData>() : data.props);
                selectedIndex = -1;
                emitSelection();
                status("تم فتح الخريطة");
            } catch (Throwable t) {
                status("تعذر فتح الخريطة");
            }
        });
    }

    public void newMap() {
        runOnGameThread(() -> {
            pushUndo();
            terrain.reset();
            props.clear();
            selectedIndex = -1;
            emitSelection();
            status("خريطة جديدة");
        });
    }

    private void runOnGameThread(Runnable r) {
        if (Gdx.app != null) Gdx.app.postRunnable(r);
    }

    private String arabicTool(Tool t) {
        switch (t) {
            case SELECT: return "تحديد";
            case RAISE: return "رفع";
            case LOWER: return "خفض";
            case SMOOTH: return "تنعيم";
            case FLATTEN: return "تسطيح";
            case NOISE: return "خشونة";
            case PAINT: return "طلاء";
            case TREE: return "شجرة";
            case ROCK: return "صخرة";
            case BUSH: return "شجيرة";
            case CRATE: return "صندوق";
            case PILLAR: return "عمود";
            case DELETE: return "حذف";
            default: return "كاميرا";
        }
    }

    private String assetName(int type) {
        switch (type) {
            case 1: return "صخرة";
            case 2: return "شجيرة";
            case 3: return "صندوق";
            case 4: return "عمود";
            default: return "شجرة";
        }
    }

    private void status(String text) {
        if (statusListener != null) statusListener.onStatus(text);
    }

    private void emitSelection() {
        if (selectionListener == null) return;
        if (!hasSelection()) {
            selectionListener.onSelection("لا يوجد مجسم محدد");
            return;
        }
        Prop p = props.get(selectedIndex);
        int scalePercent = Math.round(p.data.scale * 100f);
        int rot = Math.round(p.data.rotation);
        int heightCm = Math.round(p.data.yOffset * 100f);
        selectionListener.onSelection(assetName(p.data.type) + "  •  حجم " + scalePercent + "%  •  دوران " + rot + "°  •  ارتفاع " + heightCm + "سم");
    }

    private boolean hasSelection() {
        return selectedIndex >= 0 && selectedIndex < props.size;
    }

    private void pushUndo() {
        Snapshot s = new Snapshot();
        s.heights = terrain.heights.clone();
        s.colors = terrain.colors.clone();
        s.props = copyPropData();
        undo.add(s);
        if (undo.size > 20) undo.removeIndex(0);
    }

    private Array<PropData> copyPropData() {
        Array<PropData> out = new Array<>();
        for (Prop p : props) out.add(new PropData(p.data));
        return out;
    }

    private void restoreProps(Array<PropData> data) {
        props.clear();
        if (data == null) return;
        for (PropData d : data) addProp(d.type, d.x, d.z, d.rotation, d.scale, d.yOffset, false);
    }

    private Model modelForType(int type) {
        switch (type) {
            case 1: return rockModel;
            case 2: return bushModel;
            case 3: return crateModel;
            case 4: return pillarModel;
            default: return treeModel;
        }
    }

    private int propTypeForTool(Tool t) {
        switch (t) {
            case ROCK: return 1;
            case BUSH: return 2;
            case CRATE: return 3;
            case PILLAR: return 4;
            default: return 0;
        }
    }

    private boolean isPropTool(Tool t) {
        return t == Tool.TREE || t == Tool.ROCK || t == Tool.BUSH || t == Tool.CRATE || t == Tool.PILLAR;
    }

    private void addProp(int type, float x, float z, float rotation, float scale, float yOffset, boolean withUndo) {
        if (!terrain.inside(x, z)) return;
        if (withUndo) pushUndo();
        Model model = modelForType(type);
        if (model == null) return;
        ModelInstance instance = new ModelInstance(model);
        PropData data = new PropData();
        data.type = type;
        data.x = x;
        data.z = z;
        data.rotation = rotation;
        data.scale = scale;
        data.yOffset = yOffset;
        Prop prop = new Prop(data, instance);
        props.add(prop);
        applyPropTransform(prop);
    }

    private void applyPropTransform(Prop p) {
        float y = terrain.sampleHeight(p.data.x, p.data.z) + p.data.yOffset;
        p.instance.transform.setToTranslation(p.data.x, y, p.data.z)
                .rotate(Vector3.Y, p.data.rotation)
                .scale(p.data.scale, p.data.scale, p.data.scale);
    }

    private void updatePropHeights() {
        for (Prop p : props) applyPropTransform(p);
    }

    private boolean pickTerrain(float sx, float sy, Vector3 out) {
        Ray ray = camera.getPickRay(sx, sy);
        float prevT = 0f;
        Vector3 p = new Vector3();
        float prevDiff = Float.NaN;
        boolean prevInside = false;
        for (float t = 0.5f; t <= 100f; t += 0.65f) {
            p.set(ray.direction).scl(t).add(ray.origin);
            boolean inside = terrain.inside(p.x, p.z);
            if (inside) {
                float diff = p.y - terrain.sampleHeight(p.x, p.z);
                if (prevInside && !Float.isNaN(prevDiff) && prevDiff > 0f && diff <= 0f) {
                    float lo = prevT, hi = t;
                    for (int i = 0; i < 8; i++) {
                        float mid = (lo + hi) * 0.5f;
                        p.set(ray.direction).scl(mid).add(ray.origin);
                        float md = p.y - terrain.sampleHeight(p.x, p.z);
                        if (md > 0f) lo = mid; else hi = mid;
                    }
                    float finalT = (lo + hi) * 0.5f;
                    out.set(ray.direction).scl(finalT).add(ray.origin);
                    out.y = terrain.sampleHeight(out.x, out.z);
                    return true;
                }
                prevDiff = diff;
                prevInside = true;
                prevT = t;
            } else {
                prevInside = false;
                prevDiff = Float.NaN;
            }
        }
        return false;
    }

    private void selectNearest(float x, float z) {
        int best = -1;
        float bestDst = Float.MAX_VALUE;
        for (int i = 0; i < props.size; i++) {
            Prop p = props.get(i);
            float radius = 1.5f + p.data.scale * 1.4f;
            float d = Vector2.dst(x, z, p.data.x, p.data.z);
            if (d < radius && d < bestDst) {
                bestDst = d;
                best = i;
            }
        }
        selectedIndex = best;
        emitSelection();
        if (best >= 0) status("تم تحديد " + assetName(props.get(best).data.type));
        else status("لا يوجد مجسم هنا");
    }

    private void dragSelectedTo(float x, float z) {
        if (!hasSelection() || !terrain.inside(x, z)) return;
        if (!selectionDragSnapshotTaken) {
            pushUndo();
            selectionDragSnapshotTaken = true;
        }
        Prop p = props.get(selectedIndex);
        p.data.x = x;
        p.data.z = z;
        applyPropTransform(p);
        emitSelection();
    }

    private void deleteNearest(float x, float z) {
        int best = -1;
        float bestDst = 2.5f;
        for (int i = 0; i < props.size; i++) {
            Prop p = props.get(i);
            float d = Vector2.dst(x, z, p.data.x, p.data.z);
            if (d < bestDst) {
                bestDst = d;
                best = i;
            }
        }
        if (best >= 0) {
            pushUndo();
            props.removeIndex(best);
            if (selectedIndex == best) selectedIndex = -1;
            else if (selectedIndex > best) selectedIndex--;
            emitSelection();
            status("تم حذف العنصر");
        }
    }

    private void editAt(float sx, float sy, boolean firstTouch) {
        if (!pickTerrain(sx, sy, hit)) return;

        if (tool == Tool.SELECT) {
            if (firstTouch) {
                selectionDragSnapshotTaken = false;
                selectNearest(hit.x, hit.z);
            } else if (hasSelection()) {
                dragSelectedTo(hit.x, hit.z);
            }
            return;
        }

        if (isPropTool(tool)) {
            if (firstTouch) {
                int type = propTypeForTool(tool);
                float scale = type == 1 ? MathUtils.random(0.75f, 1.25f) : MathUtils.random(0.88f, 1.12f);
                addProp(type, hit.x, hit.z, MathUtils.random(0f, 360f), scale, 0f, true);
            }
            return;
        }

        if (tool == Tool.DELETE) {
            if (firstTouch) deleteNearest(hit.x, hit.z);
            return;
        }

        if (tool == Tool.CAMERA) return;

        if (firstTouch) {
            pushUndo();
            if (tool == Tool.FLATTEN) flattenHeight = terrain.sampleHeight(hit.x, hit.z);
        }
        terrain.apply(tool, hit.x, hit.z, brushRadius, brushStrength, flattenHeight, paintColor);
        updatePropHeights();
    }

    private class EditorInput extends InputAdapter {
        @Override
        public boolean touchDown(int screenX, int screenY, int pointer, int button) {
            if (Gdx.input.isTouched(1)) {
                beginTwoFinger();
                return true;
            }
            lastX = screenX;
            lastY = screenY;
            gestureWasTwoFinger = false;
            selectionDragSnapshotTaken = false;
            if (tool != Tool.CAMERA) editAt(screenX, screenY, true);
            return true;
        }

        @Override
        public boolean touchDragged(int screenX, int screenY, int pointer) {
            if (Gdx.input.isTouched(0) && Gdx.input.isTouched(1)) {
                handleTwoFinger();
                gestureWasTwoFinger = true;
                return true;
            }
            if (gestureWasTwoFinger) return true;

            if (tool == Tool.CAMERA) {
                float dx = screenX - lastX;
                float dy = screenY - lastY;
                yaw -= dx * 0.22f;
                pitch = MathUtils.clamp(pitch + dy * 0.18f, 18f, 78f);
            } else {
                editAt(screenX, screenY, false);
            }
            lastX = screenX;
            lastY = screenY;
            return true;
        }

        @Override
        public boolean touchUp(int screenX, int screenY, int pointer, int button) {
            if (!Gdx.input.isTouched(0) && !Gdx.input.isTouched(1)) gestureWasTwoFinger = false;
            selectionDragSnapshotTaken = false;
            return true;
        }

        private void beginTwoFinger() {
            float x0 = Gdx.input.getX(0), y0 = Gdx.input.getY(0);
            float x1 = Gdx.input.getX(1), y1 = Gdx.input.getY(1);
            lastMidX = (x0 + x1) * 0.5f;
            lastMidY = (y0 + y1) * 0.5f;
            lastPinch = Vector2.dst(x0, y0, x1, y1);
        }

        private void handleTwoFinger() {
            float x0 = Gdx.input.getX(0), y0 = Gdx.input.getY(0);
            float x1 = Gdx.input.getX(1), y1 = Gdx.input.getY(1);
            float midX = (x0 + x1) * 0.5f;
            float midY = (y0 + y1) * 0.5f;
            float pinch = Vector2.dst(x0, y0, x1, y1);
            if (lastPinch <= 0f) {
                beginTwoFinger();
                return;
            }

            distance = MathUtils.clamp(distance - (pinch - lastPinch) * 0.035f, 7f, 62f);

            float dx = midX - lastMidX;
            float dy = midY - lastMidY;
            Vector3 right = new Vector3(camera.direction).crs(Vector3.Y).nor();
            Vector3 forward = new Vector3(camera.direction.x, 0f, camera.direction.z).nor();
            float panScale = distance * 0.0018f;
            target.mulAdd(right, -dx * panScale);
            target.mulAdd(forward, dy * panScale);
            target.x = MathUtils.clamp(target.x, -16f, 16f);
            target.z = MathUtils.clamp(target.z, -16f, 16f);
            target.y = terrain.sampleHeight(target.x, target.z) * 0.35f;

            lastMidX = midX;
            lastMidY = midY;
            lastPinch = pinch;
        }
    }

    @Override
    public void resize(int width, int height) {
        if (camera != null) {
            camera.viewportWidth = width;
            camera.viewportHeight = height;
            camera.update();
        }
    }

    @Override
    public void dispose() {
        if (modelBatch != null) modelBatch.dispose();
        if (shadowBatch != null) shadowBatch.dispose();
        if (shadowLight != null) shadowLight.dispose();
        if (terrain != null) terrain.dispose();
        if (treeModel != null) treeModel.dispose();
        if (rockModel != null) rockModel.dispose();
        if (bushModel != null) bushModel.dispose();
        if (crateModel != null) crateModel.dispose();
        if (pillarModel != null) pillarModel.dispose();
        if (gizmoModel != null) gizmoModel.dispose();
    }

    private static class Prop {
        final PropData data;
        final ModelInstance instance;
        Prop(PropData data, ModelInstance instance) {
            this.data = data;
            this.instance = instance;
        }
    }

    public static class PropData {
        public int type;
        public float x, z, rotation, scale, yOffset;
        public PropData() {}
        PropData(PropData other) {
            type = other.type;
            x = other.x;
            z = other.z;
            rotation = other.rotation;
            scale = other.scale;
            yOffset = other.yOffset;
        }
    }

    public static class SaveData {
        public float[] heights;
        public float[] colors;
        public Array<PropData> props = new Array<>();
    }

    private static class Snapshot {
        float[] heights;
        float[] colors;
        Array<PropData> props;
    }

    private static class TerrainSurface implements Disposable {
        final int n;
        final float size;
        final float spacing;
        final float half;
        final float[] heights;
        final float[] colors;
        final float[] vertices;
        final short[] indices;
        final Mesh mesh;
        final Model model;
        final ModelInstance instance;

        TerrainSurface(int n, float size) {
            this.n = n;
            this.size = size;
            this.spacing = size / (n - 1f);
            this.half = size * 0.5f;
            int count = n * n;
            heights = new float[count];
            colors = new float[count * 4];
            vertices = new float[count * 10];
            indices = new short[(n - 1) * (n - 1) * 6];

            for (int i = 0; i < count; i++) {
                colors[i * 4] = 0.31f;
                colors[i * 4 + 1] = 0.53f;
                colors[i * 4 + 2] = 0.22f;
                colors[i * 4 + 3] = 1f;
            }

            int k = 0;
            for (int z = 0; z < n - 1; z++) {
                for (int x = 0; x < n - 1; x++) {
                    short a = (short)(z * n + x);
                    short b = (short)(a + 1);
                    short c = (short)(a + n);
                    short d = (short)(c + 1);
                    indices[k++] = a;
                    indices[k++] = c;
                    indices[k++] = b;
                    indices[k++] = b;
                    indices[k++] = c;
                    indices[k++] = d;
                }
            }

            mesh = new Mesh(false, count, indices.length,
                    new VertexAttribute(VertexAttributes.Usage.Position, 3, "a_position"),
                    new VertexAttribute(VertexAttributes.Usage.Normal, 3, "a_normal"),
                    new VertexAttribute(VertexAttributes.Usage.ColorUnpacked, 4, "a_color"));
            mesh.setIndices(indices);
            updateMesh();

            MeshPart part = new MeshPart("terrain", mesh, 0, indices.length, GL20.GL_TRIANGLES);
            part.update();
            Material material = new Material(ColorAttribute.createDiffuse(Color.WHITE));
            Node node = new Node();
            node.id = "terrain-node";
            node.parts.add(new NodePart(part, material));
            model = new Model();
            model.meshes.add(mesh);
            model.meshParts.add(part);
            model.materials.add(material);
            model.nodes.add(node);
            model.manageDisposable(mesh);
            instance = new ModelInstance(model);
        }

        boolean inside(float x, float z) {
            return x >= -half && x <= half && z >= -half && z <= half;
        }

        float sampleHeight(float x, float z) {
            if (!inside(x, z)) return 0f;
            float gx = (x + half) / spacing;
            float gz = (z + half) / spacing;
            int x0 = MathUtils.clamp((int)Math.floor(gx), 0, n - 1);
            int z0 = MathUtils.clamp((int)Math.floor(gz), 0, n - 1);
            int x1 = Math.min(x0 + 1, n - 1);
            int z1 = Math.min(z0 + 1, n - 1);
            float tx = gx - x0;
            float tz = gz - z0;
            float h00 = heights[z0 * n + x0];
            float h10 = heights[z0 * n + x1];
            float h01 = heights[z1 * n + x0];
            float h11 = heights[z1 * n + x1];
            return MathUtils.lerp(MathUtils.lerp(h00, h10, tx), MathUtils.lerp(h01, h11, tx), tz);
        }

        void apply(Tool tool, float cx, float cz, float radius, float strength, float flatHeight, Color paint) {
            float[] old = tool == Tool.SMOOTH ? heights.clone() : null;
            for (int z = 0; z < n; z++) {
                float wz = -half + z * spacing;
                for (int x = 0; x < n; x++) {
                    float wx = -half + x * spacing;
                    float d = Vector2.dst(wx, wz, cx, cz);
                    if (d > radius) continue;
                    float t = 1f - d / radius;
                    float falloff = t * t * (3f - 2f * t);
                    int idx = z * n + x;
                    switch (tool) {
                        case RAISE:
                            heights[idx] = MathUtils.clamp(heights[idx] + 0.22f * strength * falloff, -7f, 14f);
                            break;
                        case LOWER:
                            heights[idx] = MathUtils.clamp(heights[idx] - 0.22f * strength * falloff, -7f, 14f);
                            break;
                        case FLATTEN:
                            heights[idx] = MathUtils.lerp(heights[idx], flatHeight, 0.18f * strength * falloff);
                            break;
                        case SMOOTH:
                            float sum = 0f;
                            int count = 0;
                            for (int oz = -1; oz <= 1; oz++) {
                                for (int ox = -1; ox <= 1; ox++) {
                                    int nx = x + ox;
                                    int nz = z + oz;
                                    if (nx >= 0 && nx < n && nz >= 0 && nz < n) {
                                        sum += old[nz * n + nx];
                                        count++;
                                    }
                                }
                            }
                            heights[idx] = MathUtils.lerp(heights[idx], sum / Math.max(1, count), 0.35f * strength * falloff);
                            break;
                        case NOISE:
                            heights[idx] = MathUtils.clamp(
                                    heights[idx] + MathUtils.random(-0.18f, 0.18f) * strength * falloff,
                                    -7f, 14f);
                            break;
                        case PAINT:
                            int ci = idx * 4;
                            float a = 0.30f * strength * falloff;
                            colors[ci] = MathUtils.lerp(colors[ci], paint.r, a);
                            colors[ci + 1] = MathUtils.lerp(colors[ci + 1], paint.g, a);
                            colors[ci + 2] = MathUtils.lerp(colors[ci + 2], paint.b, a);
                            break;
                        default:
                            break;
                    }
                }
            }
            updateMesh();
        }

        void reset() {
            for (int i = 0; i < heights.length; i++) heights[i] = 0f;
            for (int i = 0; i < heights.length; i++) {
                colors[i * 4] = 0.31f;
                colors[i * 4 + 1] = 0.53f;
                colors[i * 4 + 2] = 0.22f;
                colors[i * 4 + 3] = 1f;
            }
            updateMesh();
        }

        void restore(float[] h, float[] c) {
            if (h.length != heights.length || c.length != colors.length) return;
            System.arraycopy(h, 0, heights, 0, heights.length);
            System.arraycopy(c, 0, colors, 0, colors.length);
            updateMesh();
        }

        void updateMesh() {
            int v = 0;
            Vector3 normal = new Vector3();
            for (int z = 0; z < n; z++) {
                for (int x = 0; x < n; x++) {
                    int idx = z * n + x;
                    float wx = -half + x * spacing;
                    float wz = -half + z * spacing;
                    float hl = heights[z * n + Math.max(0, x - 1)];
                    float hr = heights[z * n + Math.min(n - 1, x + 1)];
                    float hd = heights[Math.max(0, z - 1) * n + x];
                    float hu = heights[Math.min(n - 1, z + 1) * n + x];
                    normal.set(hl - hr, spacing * 2f, hd - hu).nor();
                    vertices[v++] = wx;
                    vertices[v++] = heights[idx];
                    vertices[v++] = wz;
                    vertices[v++] = normal.x;
                    vertices[v++] = normal.y;
                    vertices[v++] = normal.z;
                    int ci = idx * 4;
                    vertices[v++] = colors[ci];
                    vertices[v++] = colors[ci + 1];
                    vertices[v++] = colors[ci + 2];
                    vertices[v++] = colors[ci + 3];
                }
            }
            mesh.setVertices(vertices);
        }

        @Override
        public void dispose() {
            model.dispose();
        }
    }
}
