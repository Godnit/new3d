package com.godnit.terrainstudio;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.view.MotionEvent;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.nio.ShortBuffer;
import java.util.ArrayList;
import java.util.List;

public class TerrainGLView extends GLSurfaceView {
    public static final int MODE_CAMERA = 0;
    public static final int MODE_RAISE = 1;
    public static final int MODE_LOWER = 2;
    public static final int MODE_SMOOTH = 3;
    public static final int MODE_PAINT = 4;
    public static final int MODE_TREE = 5;
    public static final int MODE_ROCK = 6;
    public static final int MODE_ERASE = 7;

    public interface StatusListener { void onStatus(String text); }

    private final TerrainRenderer renderer;
    private StatusListener statusListener;
    private float lastX;
    private float lastY;
    private float lastPinch = -1f;
    private int currentMode = MODE_CAMERA;

    public TerrainGLView(Context context) {
        super(context);
        setEGLContextClientVersion(2);
        renderer = new TerrainRenderer(context, this);
        setRenderer(renderer);
        setRenderMode(GLSurfaceView.RENDERMODE_WHEN_DIRTY);
        setPreserveEGLContextOnPause(true);
        setBackgroundColor(Color.TRANSPARENT);
    }

    public void setStatusListener(StatusListener listener) { this.statusListener = listener; }
    void emitStatus(final String text) { if (statusListener != null) post(() -> statusListener.onStatus(text)); }

    public void setToolMode(int mode) {
        currentMode = mode;
        queueEvent(() -> renderer.setMode(mode));
        requestRender();
    }

    public void setBrushRadius(float value) { queueEvent(() -> renderer.setBrushRadius(value)); }
    public void setBrushStrength(float value) { queueEvent(() -> renderer.setBrushStrength(value)); }
    public void setPaintColor(int color) { queueEvent(() -> renderer.setPaintColor(color)); }
    public void undo() { queueEvent(() -> { renderer.undo(); requestRender(); }); }
    public void saveMap() { queueEvent(renderer::saveMap); }
    public void loadMap() { queueEvent(() -> { renderer.loadMap(); requestRender(); }); }
    public void newMap() { queueEvent(() -> { renderer.newMap(); requestRender(); }); }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        int action = e.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            lastX = e.getX();
            lastY = e.getY();
            lastPinch = -1f;
            if (currentMode != MODE_CAMERA) {
                final float x = lastX, y = lastY;
                queueEvent(() -> { renderer.beginStroke(); renderer.applyAtScreen(x, y, true); });
                requestRender();
            }
            return true;
        }

        if (action == MotionEvent.ACTION_POINTER_DOWN && e.getPointerCount() >= 2) {
            lastPinch = pointerDistance(e);
            return true;
        }

        if (action == MotionEvent.ACTION_MOVE) {
            if (e.getPointerCount() >= 2) {
                float d = pointerDistance(e);
                if (lastPinch > 0f) {
                    final float delta = d - lastPinch;
                    queueEvent(() -> renderer.zoom(delta));
                    requestRender();
                }
                lastPinch = d;
                return true;
            }

            float x = e.getX();
            float y = e.getY();
            float dx = x - lastX;
            float dy = y - lastY;
            lastX = x;
            lastY = y;

            if (currentMode == MODE_CAMERA) {
                queueEvent(() -> renderer.rotateCamera(dx, dy));
            } else {
                queueEvent(() -> renderer.applyAtScreen(x, y, false));
            }
            requestRender();
            return true;
        }

        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            lastPinch = -1f;
            return true;
        }
        return true;
    }

    private float pointerDistance(MotionEvent e) {
        if (e.getPointerCount() < 2) return -1f;
        float dx = e.getX(0) - e.getX(1);
        float dy = e.getY(0) - e.getY(1);
        return (float)Math.sqrt(dx * dx + dy * dy);
    }
}

class TerrainRenderer implements GLSurfaceView.Renderer {
    private static final int GRID = 33;
    private static final float CELL = 1.05f;
    private static final float HALF = (GRID - 1) * CELL * 0.5f;
    private static final int MAX_UNDO = 8;
    private static final String PREFS = "terrain_studio_native";
    private static final String SAVE_KEY = "map";

    private final Context context;
    private final TerrainGLView owner;

    private final float[] heights = new float[GRID * GRID];
    private final float[] colors = new float[GRID * GRID * 4];
    private final List<PlacedObject> objects = new ArrayList<>();
    private final List<Snapshot> undo = new ArrayList<>();

    private FloatBuffer terrainPositions;
    private FloatBuffer terrainNormals;
    private FloatBuffer terrainColors;
    private ShortBuffer terrainIndices;
    private FloatBuffer cubePositions;
    private FloatBuffer cubeNormals;
    private int indexCount;

    private int program;
    private int aPosition, aNormal, aColor, uMvp;
    private int width = 1, height = 1;

    private final float[] projection = new float[16];
    private final float[] view = new float[16];
    private final float[] vp = new float[16];
    private final float[] model = new float[16];
    private final float[] mvp = new float[16];

    private float yaw = 38f;
    private float pitch = 48f;
    private float distance = 30f;
    private int mode = TerrainGLView.MODE_CAMERA;
    private float brushRadius = 2.7f;
    private float brushStrength = 0.42f;
    private int paintColor = 0xFF4F823B;

    TerrainRenderer(Context context, TerrainGLView owner) {
        this.context = context.getApplicationContext();
        this.owner = owner;
        resetData();
        buildIndexBuffer();
        buildCubeBuffers();
    }

    void setMode(int mode) { this.mode = mode; }
    void setBrushRadius(float value) { brushRadius = Math.max(0.7f, Math.min(6.0f, value)); }
    void setBrushStrength(float value) { brushStrength = Math.max(0.05f, Math.min(1f, value)); }
    void setPaintColor(int value) { paintColor = value; }

    @Override
    public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 gl, javax.microedition.khronos.egl.EGLConfig config) {
        GLES20.glClearColor(0.35f, 0.66f, 0.88f, 1f);
        GLES20.glEnable(GLES20.GL_DEPTH_TEST);
        GLES20.glDisable(GLES20.GL_CULL_FACE);
        program = createProgram(VERTEX_SHADER, FRAGMENT_SHADER);
        aPosition = GLES20.glGetAttribLocation(program, "aPosition");
        aNormal = GLES20.glGetAttribLocation(program, "aNormal");
        aColor = GLES20.glGetAttribLocation(program, "aColor");
        uMvp = GLES20.glGetUniformLocation(program, "uMVP");
        rebuildTerrainBuffers();
        owner.emitStatus("جاهز - محرك OpenGL مباشر");
    }

    @Override
    public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 gl, int width, int height) {
        this.width = Math.max(1, width);
        this.height = Math.max(1, height);
        GLES20.glViewport(0, 0, this.width, this.height);
        float aspect = this.width / (float)this.height;
        Matrix.perspectiveM(projection, 0, 52f, aspect, 0.1f, 140f);
        updateView();
    }

    @Override
    public void onDrawFrame(javax.microedition.khronos.opengles.GL10 gl) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);
        GLES20.glUseProgram(program);
        updateView();

        drawCube(0f, -0.36f, 0f, HALF * 2.05f, 0.55f, HALF * 2.05f, 0f, 0xFF315B32);
        drawTerrain();
        drawObjects();
    }

    private void drawTerrain() {
        Matrix.setIdentityM(model, 0);
        Matrix.multiplyMM(mvp, 0, vp, 0, model, 0);
        GLES20.glUniformMatrix4fv(uMvp, 1, false, mvp, 0);

        terrainPositions.position(0);
        GLES20.glEnableVertexAttribArray(aPosition);
        GLES20.glVertexAttribPointer(aPosition, 3, GLES20.GL_FLOAT, false, 0, terrainPositions);

        terrainNormals.position(0);
        GLES20.glEnableVertexAttribArray(aNormal);
        GLES20.glVertexAttribPointer(aNormal, 3, GLES20.GL_FLOAT, false, 0, terrainNormals);

        terrainColors.position(0);
        GLES20.glEnableVertexAttribArray(aColor);
        GLES20.glVertexAttribPointer(aColor, 4, GLES20.GL_FLOAT, false, 0, terrainColors);

        terrainIndices.position(0);
        GLES20.glDrawElements(GLES20.GL_TRIANGLES, indexCount, GLES20.GL_UNSIGNED_SHORT, terrainIndices);
    }

    private void drawObjects() {
        for (PlacedObject o : objects) {
            float y = terrainHeightAt(o.x, o.z);
            if (o.type == TerrainGLView.MODE_TREE) {
                drawCube(o.x, y + 0.9f, o.z, 0.34f, 1.8f, 0.34f, o.rotation, 0xFF714A2F);
                drawCube(o.x, y + 2.05f, o.z, 2.0f, 1.45f, 2.0f, o.rotation, 0xFF397A42);
                drawCube(o.x, y + 2.9f, o.z, 1.35f, 0.85f, 1.35f, o.rotation + 18f, 0xFF2E6A39);
            } else if (o.type == TerrainGLView.MODE_ROCK) {
                drawCube(o.x, y + 0.42f, o.z, 1.35f, 0.84f, 1.08f, o.rotation, 0xFF777974);
            }
        }
    }

    private void drawCube(float x, float y, float z, float sx, float sy, float sz, float rotationY, int color) {
        Matrix.setIdentityM(model, 0);
        Matrix.translateM(model, 0, x, y, z);
        Matrix.rotateM(model, 0, rotationY, 0f, 1f, 0f);
        Matrix.scaleM(model, 0, sx, sy, sz);
        Matrix.multiplyMM(mvp, 0, vp, 0, model, 0);
        GLES20.glUniformMatrix4fv(uMvp, 1, false, mvp, 0);

        cubePositions.position(0);
        GLES20.glEnableVertexAttribArray(aPosition);
        GLES20.glVertexAttribPointer(aPosition, 3, GLES20.GL_FLOAT, false, 0, cubePositions);
        cubeNormals.position(0);
        GLES20.glEnableVertexAttribArray(aNormal);
        GLES20.glVertexAttribPointer(aNormal, 3, GLES20.GL_FLOAT, false, 0, cubeNormals);

        GLES20.glDisableVertexAttribArray(aColor);
        GLES20.glVertexAttrib4f(aColor,
                Color.red(color) / 255f,
                Color.green(color) / 255f,
                Color.blue(color) / 255f,
                1f);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, 36);
    }

    void rotateCamera(float dx, float dy) {
        yaw -= dx * 0.22f;
        pitch = clamp(pitch + dy * 0.16f, 22f, 76f);
        updateView();
    }

    void zoom(float pinchDelta) {
        distance = clamp(distance - pinchDelta * 0.045f, 10f, 50f);
        updateView();
    }

    private void updateView() {
        float yr = (float)Math.toRadians(yaw);
        float pr = (float)Math.toRadians(pitch);
        float horizontal = (float)Math.cos(pr) * distance;
        float eyeX = (float)Math.sin(yr) * horizontal;
        float eyeY = (float)Math.sin(pr) * distance + 1.2f;
        float eyeZ = (float)Math.cos(yr) * horizontal;
        Matrix.setLookAtM(view, 0, eyeX, eyeY, eyeZ, 0f, 0f, 0f, 0f, 1f, 0f);
        Matrix.multiplyMM(vp, 0, projection, 0, view, 0);
    }

    void beginStroke() { pushUndo(); }

    void applyAtScreen(float sx, float sy, boolean first) {
        float[] p = pickTerrain(sx, sy);
        if (p == null) return;
        if (Math.abs(p[0]) > HALF + 1f || Math.abs(p[2]) > HALF + 1f) return;

        if (mode == TerrainGLView.MODE_RAISE) sculpt(p[0], p[2], 1f);
        else if (mode == TerrainGLView.MODE_LOWER) sculpt(p[0], p[2], -1f);
        else if (mode == TerrainGLView.MODE_SMOOTH) smooth(p[0], p[2]);
        else if (mode == TerrainGLView.MODE_PAINT) paint(p[0], p[2]);
        else if (mode == TerrainGLView.MODE_TREE && first) placeObject(TerrainGLView.MODE_TREE, p[0], p[2]);
        else if (mode == TerrainGLView.MODE_ROCK && first) placeObject(TerrainGLView.MODE_ROCK, p[0], p[2]);
        else if (mode == TerrainGLView.MODE_ERASE && first) eraseNearest(p[0], p[2]);
    }

    private void sculpt(float cx, float cz, float direction) {
        for (int z = 0; z < GRID; z++) {
            for (int x = 0; x < GRID; x++) {
                float wx = x * CELL - HALF;
                float wz = z * CELL - HALF;
                float dx = wx - cx, dz = wz - cz;
                float d = (float)Math.sqrt(dx * dx + dz * dz);
                if (d <= brushRadius) {
                    float falloff = 1f - d / brushRadius;
                    int i = idx(x, z);
                    heights[i] = clamp(heights[i] + direction * brushStrength * 0.32f * falloff * falloff, -5f, 11f);
                }
            }
        }
        rebuildTerrainBuffers();
    }

    private void smooth(float cx, float cz) {
        float[] src = heights.clone();
        for (int z = 0; z < GRID; z++) {
            for (int x = 0; x < GRID; x++) {
                float wx = x * CELL - HALF;
                float wz = z * CELL - HALF;
                float dx = wx - cx, dz = wz - cz;
                float d = (float)Math.sqrt(dx * dx + dz * dz);
                if (d > brushRadius) continue;
                float total = 0f;
                int count = 0;
                for (int oz = -1; oz <= 1; oz++) {
                    for (int ox = -1; ox <= 1; ox++) {
                        int nx = x + ox, nz = z + oz;
                        if (nx >= 0 && nx < GRID && nz >= 0 && nz < GRID) {
                            total += src[idx(nx, nz)];
                            count++;
                        }
                    }
                }
                float avg = total / Math.max(1, count);
                float mix = clamp(brushStrength * (1f - d / brushRadius) * 0.55f, 0f, 1f);
                int i = idx(x, z);
                heights[i] = src[i] + (avg - src[i]) * mix;
            }
        }
        rebuildTerrainBuffers();
    }

    private void paint(float cx, float cz) {
        float tr = Color.red(paintColor) / 255f;
        float tg = Color.green(paintColor) / 255f;
        float tb = Color.blue(paintColor) / 255f;
        for (int z = 0; z < GRID; z++) {
            for (int x = 0; x < GRID; x++) {
                float wx = x * CELL - HALF;
                float wz = z * CELL - HALF;
                float dx = wx - cx, dz = wz - cz;
                float d = (float)Math.sqrt(dx * dx + dz * dz);
                if (d <= brushRadius) {
                    float mix = clamp(brushStrength * (1f - d / brushRadius) * 0.58f, 0f, 1f);
                    int c = idx(x, z) * 4;
                    colors[c] += (tr - colors[c]) * mix;
                    colors[c + 1] += (tg - colors[c + 1]) * mix;
                    colors[c + 2] += (tb - colors[c + 2]) * mix;
                }
            }
        }
        rebuildTerrainBuffers();
    }

    private void placeObject(int type, float x, float z) {
        PlacedObject o = new PlacedObject();
        o.type = type;
        o.x = x;
        o.z = z;
        o.rotation = (float)(Math.random() * 360.0);
        objects.add(o);
        owner.emitStatus(type == TerrainGLView.MODE_TREE ? "تمت إضافة شجرة" : "تمت إضافة صخرة");
    }

    private void eraseNearest(float x, float z) {
        int best = -1;
        float bestD = brushRadius;
        for (int i = 0; i < objects.size(); i++) {
            PlacedObject o = objects.get(i);
            float dx = o.x - x, dz = o.z - z;
            float d = (float)Math.sqrt(dx * dx + dz * dz);
            if (d < bestD) { bestD = d; best = i; }
        }
        if (best >= 0) {
            objects.remove(best);
            owner.emitStatus("تم حذف العنصر");
        } else owner.emitStatus("لا يوجد عنصر قريب");
    }

    private float[] pickTerrain(float sx, float sy) {
        float nx = (2f * sx / width) - 1f;
        float ny = 1f - (2f * sy / height);
        float[] inv = new float[16];
        if (!Matrix.invertM(inv, 0, vp, 0)) return null;
        float[] near = unproject(inv, nx, ny, -1f);
        float[] far = unproject(inv, nx, ny, 1f);
        float dx = far[0] - near[0];
        float dy = far[1] - near[1];
        float dz = far[2] - near[2];
        if (Math.abs(dy) < 0.0001f) return null;

        float targetY = 0f;
        float px = 0f, pz = 0f;
        for (int i = 0; i < 3; i++) {
            float t = (targetY - near[1]) / dy;
            if (t < 0f) return null;
            px = near[0] + dx * t;
            pz = near[2] + dz * t;
            targetY = terrainHeightAt(px, pz);
        }
        return new float[]{px, targetY, pz};
    }

    private float[] unproject(float[] inv, float x, float y, float z) {
        float[] in = {x, y, z, 1f};
        float[] out = new float[4];
        Matrix.multiplyMV(out, 0, inv, 0, in, 0);
        float w = Math.abs(out[3]) < 0.00001f ? 1f : out[3];
        return new float[]{out[0] / w, out[1] / w, out[2] / w};
    }

    private float terrainHeightAt(float x, float z) {
        float gx = clamp((x + HALF) / CELL, 0f, GRID - 1.001f);
        float gz = clamp((z + HALF) / CELL, 0f, GRID - 1.001f);
        int x0 = (int)Math.floor(gx), z0 = (int)Math.floor(gz);
        int x1 = Math.min(GRID - 1, x0 + 1), z1 = Math.min(GRID - 1, z0 + 1);
        float tx = gx - x0, tz = gz - z0;
        float h0 = heights[idx(x0, z0)] * (1f - tx) + heights[idx(x1, z0)] * tx;
        float h1 = heights[idx(x0, z1)] * (1f - tx) + heights[idx(x1, z1)] * tx;
        return h0 * (1f - tz) + h1 * tz;
    }

    private void rebuildTerrainBuffers() {
        int vertices = GRID * GRID;
        float[] pos = new float[vertices * 3];
        float[] nor = new float[vertices * 3];
        for (int z = 0; z < GRID; z++) {
            for (int x = 0; x < GRID; x++) {
                int i = idx(x, z);
                int p = i * 3;
                pos[p] = x * CELL - HALF;
                pos[p + 1] = heights[i];
                pos[p + 2] = z * CELL - HALF;

                float hL = heights[idx(Math.max(0, x - 1), z)];
                float hR = heights[idx(Math.min(GRID - 1, x + 1), z)];
                float hD = heights[idx(x, Math.max(0, z - 1))];
                float hU = heights[idx(x, Math.min(GRID - 1, z + 1))];
                float nx = hL - hR, ny = 2f * CELL, nz = hD - hU;
                float len = (float)Math.sqrt(nx * nx + ny * ny + nz * nz);
                nor[p] = nx / len;
                nor[p + 1] = ny / len;
                nor[p + 2] = nz / len;
            }
        }
        terrainPositions = floatBuffer(pos);
        terrainNormals = floatBuffer(nor);
        terrainColors = floatBuffer(colors);
    }

    private void buildIndexBuffer() {
        short[] idx = new short[(GRID - 1) * (GRID - 1) * 6];
        int k = 0;
        for (int z = 0; z < GRID - 1; z++) {
            for (int x = 0; x < GRID - 1; x++) {
                short a = (short)idx(x, z);
                short b = (short)idx(x + 1, z);
                short c = (short)idx(x, z + 1);
                short d = (short)idx(x + 1, z + 1);
                idx[k++] = a; idx[k++] = c; idx[k++] = b;
                idx[k++] = b; idx[k++] = c; idx[k++] = d;
            }
        }
        indexCount = idx.length;
        ByteBuffer bb = ByteBuffer.allocateDirect(idx.length * 2).order(ByteOrder.nativeOrder());
        terrainIndices = bb.asShortBuffer();
        terrainIndices.put(idx).position(0);
    }

    private void buildCubeBuffers() {
        float[] p = new float[36 * 3];
        float[] n = new float[36 * 3];
        int cursor = 0;
        cursor = addFace(p, n, cursor, 0, 1, 0, new float[][]{{-.5f,.5f,-.5f},{-.5f,.5f,.5f},{.5f,.5f,-.5f},{.5f,.5f,.5f}});
        cursor = addFace(p, n, cursor, 0,-1, 0, new float[][]{{-.5f,-.5f,.5f},{-.5f,-.5f,-.5f},{.5f,-.5f,.5f},{.5f,-.5f,-.5f}});
        cursor = addFace(p, n, cursor, 0, 0, 1, new float[][]{{-.5f,-.5f,.5f},{.5f,-.5f,.5f},{-.5f,.5f,.5f},{.5f,.5f,.5f}});
        cursor = addFace(p, n, cursor, 0, 0,-1, new float[][]{{.5f,-.5f,-.5f},{-.5f,-.5f,-.5f},{.5f,.5f,-.5f},{-.5f,.5f,-.5f}});
        cursor = addFace(p, n, cursor, 1, 0, 0, new float[][]{{.5f,-.5f,.5f},{.5f,-.5f,-.5f},{.5f,.5f,.5f},{.5f,.5f,-.5f}});
        addFace(p, n, cursor,-1, 0, 0, new float[][]{{-.5f,-.5f,-.5f},{-.5f,-.5f,.5f},{-.5f,.5f,-.5f},{-.5f,.5f,.5f}});
        cubePositions = floatBuffer(p);
        cubeNormals = floatBuffer(n);
    }

    private int addFace(float[] p, float[] n, int cursor, float nx, float ny, float nz, float[][] v) {
        int[] order = {0,1,2,2,1,3};
        for (int oi : order) {
            p[cursor] = v[oi][0]; n[cursor++] = nx;
            p[cursor] = v[oi][1]; n[cursor++] = ny;
            p[cursor] = v[oi][2]; n[cursor++] = nz;
        }
        return cursor;
    }

    private FloatBuffer floatBuffer(float[] data) {
        ByteBuffer bb = ByteBuffer.allocateDirect(data.length * 4).order(ByteOrder.nativeOrder());
        FloatBuffer fb = bb.asFloatBuffer();
        fb.put(data).position(0);
        return fb;
    }

    private void resetData() {
        int base = 0xFF4F823B;
        float r = Color.red(base) / 255f, g = Color.green(base) / 255f, b = Color.blue(base) / 255f;
        for (int i = 0; i < heights.length; i++) {
            heights[i] = 0f;
            int c = i * 4;
            colors[c] = r; colors[c + 1] = g; colors[c + 2] = b; colors[c + 3] = 1f;
        }
        objects.clear();
    }

    private void pushUndo() {
        Snapshot s = new Snapshot();
        s.heights = heights.clone();
        s.colors = colors.clone();
        for (PlacedObject o : objects) s.objects.add(o.copy());
        undo.add(s);
        while (undo.size() > MAX_UNDO) undo.remove(0);
    }

    void undo() {
        if (undo.isEmpty()) { owner.emitStatus("لا يوجد تراجع"); return; }
        Snapshot s = undo.remove(undo.size() - 1);
        System.arraycopy(s.heights, 0, heights, 0, heights.length);
        System.arraycopy(s.colors, 0, colors, 0, colors.length);
        objects.clear();
        for (PlacedObject o : s.objects) objects.add(o.copy());
        rebuildTerrainBuffers();
        owner.emitStatus("تم التراجع");
    }

    void newMap() {
        pushUndo();
        resetData();
        rebuildTerrainBuffers();
        owner.emitStatus("خريطة جديدة");
    }

    void saveMap() {
        try {
            JSONObject root = new JSONObject();
            JSONArray hs = new JSONArray();
            for (float h : heights) hs.put(h);
            root.put("h", hs);
            JSONArray cs = new JSONArray();
            for (float c : colors) cs.put(c);
            root.put("c", cs);
            JSONArray os = new JSONArray();
            for (PlacedObject o : objects) {
                JSONObject j = new JSONObject();
                j.put("t", o.type); j.put("x", o.x); j.put("z", o.z); j.put("r", o.rotation);
                os.put(j);
            }
            root.put("o", os);
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putString(SAVE_KEY, root.toString()).apply();
            owner.emitStatus("تم حفظ الخريطة");
        } catch (Exception e) { owner.emitStatus("تعذر الحفظ"); }
    }

    void loadMap() {
        try {
            SharedPreferences p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
            String raw = p.getString(SAVE_KEY, null);
            if (raw == null) { owner.emitStatus("لا توجد خريطة محفوظة"); return; }
            pushUndo();
            JSONObject root = new JSONObject(raw);
            JSONArray hs = root.getJSONArray("h");
            JSONArray cs = root.getJSONArray("c");
            for (int i = 0; i < heights.length && i < hs.length(); i++) heights[i] = (float)hs.getDouble(i);
            for (int i = 0; i < colors.length && i < cs.length(); i++) colors[i] = (float)cs.getDouble(i);
            objects.clear();
            JSONArray os = root.getJSONArray("o");
            for (int i = 0; i < os.length(); i++) {
                JSONObject j = os.getJSONObject(i);
                PlacedObject o = new PlacedObject();
                o.type = j.getInt("t"); o.x = (float)j.getDouble("x"); o.z = (float)j.getDouble("z"); o.rotation = (float)j.getDouble("r");
                objects.add(o);
            }
            rebuildTerrainBuffers();
            owner.emitStatus("تم فتح الخريطة");
        } catch (Exception e) { owner.emitStatus("ملف الحفظ غير صالح"); }
    }

    private int idx(int x, int z) { return z * GRID + x; }
    private float clamp(float v, float min, float max) { return Math.max(min, Math.min(max, v)); }

    private int createProgram(String vs, String fs) {
        int vertex = compileShader(GLES20.GL_VERTEX_SHADER, vs);
        int fragment = compileShader(GLES20.GL_FRAGMENT_SHADER, fs);
        int p = GLES20.glCreateProgram();
        GLES20.glAttachShader(p, vertex);
        GLES20.glAttachShader(p, fragment);
        GLES20.glLinkProgram(p);
        int[] ok = new int[1];
        GLES20.glGetProgramiv(p, GLES20.GL_LINK_STATUS, ok, 0);
        if (ok[0] == 0) throw new RuntimeException("Program link: " + GLES20.glGetProgramInfoLog(p));
        GLES20.glDeleteShader(vertex);
        GLES20.glDeleteShader(fragment);
        return p;
    }

    private int compileShader(int type, String source) {
        int s = GLES20.glCreateShader(type);
        GLES20.glShaderSource(s, source);
        GLES20.glCompileShader(s);
        int[] ok = new int[1];
        GLES20.glGetShaderiv(s, GLES20.GL_COMPILE_STATUS, ok, 0);
        if (ok[0] == 0) throw new RuntimeException("Shader: " + GLES20.glGetShaderInfoLog(s));
        return s;
    }

    private static class PlacedObject {
        int type; float x, z, rotation;
        PlacedObject copy() { PlacedObject p = new PlacedObject(); p.type = type; p.x = x; p.z = z; p.rotation = rotation; return p; }
    }

    private static class Snapshot {
        float[] heights;
        float[] colors;
        List<PlacedObject> objects = new ArrayList<>();
    }

    private static final String VERTEX_SHADER =
            "uniform mat4 uMVP;\n" +
            "attribute vec3 aPosition;\n" +
            "attribute vec3 aNormal;\n" +
            "attribute vec4 aColor;\n" +
            "varying vec4 vColor;\n" +
            "varying float vLight;\n" +
            "void main(){\n" +
            "  vec3 n=normalize(aNormal);\n" +
            "  vec3 l=normalize(vec3(-0.45,0.88,0.28));\n" +
            "  vLight=0.62+0.38*max(dot(n,l),0.0);\n" +
            "  vColor=aColor;\n" +
            "  gl_Position=uMVP*vec4(aPosition,1.0);\n" +
            "}";

    private static final String FRAGMENT_SHADER =
            "precision mediump float;\n" +
            "varying vec4 vColor;\n" +
            "varying float vLight;\n" +
            "void main(){ gl_FragColor=vec4(vColor.rgb*vLight,vColor.a); }";
}
