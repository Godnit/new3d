from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
engine_path = ROOT / 'app/src/main/java/com/godnit/terrainstudio/gdx/MiniBlenderGameV4.java'
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

# Blender has single-axis, two-axis plane, and free/view-plane handles.
s = must_replace(
    s,
    '    private enum Axis { NONE, X, Y, Z, FREE }',
    '    private enum Axis { NONE, X, Y, Z, XY, XZ, YZ, FREE }',
    'extended blender handles'
)

# Stable 3D drag state. Transform math is calculated from the original touch-down
# position, not accumulated screen deltas. This avoids reversed/accelerating axes.
s = must_replace(
    s,
    '    private static final float DRAG_START_PX = 12f;',
    '''    private static final float DRAG_START_PX = 12f;
    private final Plane blenderDragPlane = new Plane(new Vector3(0, 1, 0), 0f);
    private final Vector3 blenderStartHit = new Vector3();
    private final Vector3 blenderAxis = new Vector3();
    private final Vector3 blenderStartPos = new Vector3();
    private final Vector3 blenderStartScale = new Vector3();
    private final Vector3 blenderStartRot = new Vector3();
    private float blenderDownX = 0f, blenderDownY = 0f;
    private float blenderStartParam = 0f;
    private float blenderStartRadius = 1f;
    private float blenderStartScreenAngle = 0f;
    private boolean blenderFallback = false;''',
    'v8 transform state'
)

# Replace the old partial gizmos with Blender-style full transform manipulators.
s = must_sub(
    s,
    r'''    private void buildGizmos\(\) \{.*?\n    \}\n\n    @Override\n    public void render\(\) \{''',
    '''    private void buildGizmos() {
        long a = VertexAttributes.Usage.Position | VertexAttributes.Usage.Normal;
        Material red = gizmoMat(new Color(0.95f, 0.10f, 0.08f, 1));
        Material green = gizmoMat(new Color(0.18f, 0.78f, 0.18f, 1));
        Material blue = gizmoMat(new Color(0.10f, 0.35f, 1.00f, 1));
        Material white = gizmoMat(new Color(0.90f, 0.92f, 0.94f, 1));

        ModelBuilder mb = new ModelBuilder();
        mb.begin();
        blenderAxisParts(mb, a, red, green, blue, false);
        blenderPlaneHandles(mb, a, red, green, blue);
        MeshPartBuilder centerMove = mb.part("moveCenter", GL20.GL_TRIANGLES, a, white);
        centerMove.sphere(0.30f, 0.30f, 0.30f, 10, 8);
        moveGizmoModel = mb.end();

        mb = new ModelBuilder();
        mb.begin();
        blenderAxisParts(mb, a, red, green, blue, true);
        blenderPlaneHandles(mb, a, red, green, blue);
        MeshPartBuilder centerScale = mb.part("scaleCenter", GL20.GL_TRIANGLES, a, white);
        centerScale.box(0.28f, 0.28f, 0.28f);
        scaleGizmoModel = mb.end();

        mb = new ModelBuilder();
        mb.begin();
        blenderRing(mb, a, red, Axis.X, 2.55f);
        blenderRing(mb, a, green, Axis.Y, 2.55f);
        blenderRing(mb, a, blue, Axis.Z, 2.55f);
        rotateGizmoModel = mb.end();
    }

    private void blenderAxisParts(ModelBuilder mb, long a, Material red, Material green, Material blue, boolean scale) {
        float len = 2.85f;
        float shaft = 0.065f;

        MeshPartBuilder x = mb.part("axisX", GL20.GL_TRIANGLES, a, red);
        x.setVertexTransform(new Matrix4().setToTranslation(len * 0.5f, 0, 0).rotate(Vector3.Z, -90f));
        x.cylinder(shaft, len, shaft, 10);
        MeshPartBuilder y = mb.part("axisY", GL20.GL_TRIANGLES, a, green);
        y.setVertexTransform(new Matrix4().setToTranslation(0, len * 0.5f, 0));
        y.cylinder(shaft, len, shaft, 10);
        MeshPartBuilder z = mb.part("axisZ", GL20.GL_TRIANGLES, a, blue);
        z.setVertexTransform(new Matrix4().setToTranslation(0, 0, len * 0.5f).rotate(Vector3.X, 90f));
        z.cylinder(shaft, len, shaft, 10);

        if (scale) {
            MeshPartBuilder hx = mb.part("scaleX", GL20.GL_TRIANGLES, a, red);
            hx.setVertexTransform(new Matrix4().setToTranslation(len + 0.13f, 0, 0));
            hx.box(0.30f, 0.30f, 0.30f);
            MeshPartBuilder hy = mb.part("scaleY", GL20.GL_TRIANGLES, a, green);
            hy.setVertexTransform(new Matrix4().setToTranslation(0, len + 0.13f, 0));
            hy.box(0.30f, 0.30f, 0.30f);
            MeshPartBuilder hz = mb.part("scaleZ", GL20.GL_TRIANGLES, a, blue);
            hz.setVertexTransform(new Matrix4().setToTranslation(0, 0, len + 0.13f));
            hz.box(0.30f, 0.30f, 0.30f);
        } else {
            MeshPartBuilder tx = mb.part("moveX", GL20.GL_TRIANGLES, a, red);
            tx.setVertexTransform(new Matrix4().setToTranslation(len + 0.16f, 0, 0).rotate(Vector3.Z, -90f));
            tx.cone(0.30f, 0.55f, 0.30f, 10);
            MeshPartBuilder ty = mb.part("moveY", GL20.GL_TRIANGLES, a, green);
            ty.setVertexTransform(new Matrix4().setToTranslation(0, len + 0.16f, 0));
            ty.cone(0.30f, 0.55f, 0.30f, 10);
            MeshPartBuilder tz = mb.part("moveZ", GL20.GL_TRIANGLES, a, blue);
            tz.setVertexTransform(new Matrix4().setToTranslation(0, 0, len + 0.16f).rotate(Vector3.X, 90f));
            tz.cone(0.30f, 0.55f, 0.30f, 10);
        }
    }

    // Plane handles follow Blender's convention: the handle color identifies the
    // axis perpendicular to the plane (XY blue, XZ green, YZ red).
    private void blenderPlaneHandles(ModelBuilder mb, long a, Material red, Material green, Material blue) {
        float c = 0.82f, size = 0.48f, thick = 0.045f;
        MeshPartBuilder xy = mb.part("planeXY", GL20.GL_TRIANGLES, a, blue);
        xy.setVertexTransform(new Matrix4().setToTranslation(c, c, 0));
        xy.box(size, size, thick);
        MeshPartBuilder xz = mb.part("planeXZ", GL20.GL_TRIANGLES, a, green);
        xz.setVertexTransform(new Matrix4().setToTranslation(c, 0, c));
        xz.box(size, thick, size);
        MeshPartBuilder yz = mb.part("planeYZ", GL20.GL_TRIANGLES, a, red);
        yz.setVertexTransform(new Matrix4().setToTranslation(0, c, c));
        yz.box(thick, size, size);
    }

    private void blenderRing(ModelBuilder mb, long a, Material material, Axis axis, float r) {
        MeshPartBuilder part = mb.part("ring" + axis, GL20.GL_TRIANGLES, a, material);
        int segs = 64;
        for (int i = 0; i < segs; i++) {
            float t0 = MathUtils.PI2 * i / segs;
            float t1 = MathUtils.PI2 * (i + 1f) / segs;
            float c0 = MathUtils.cos(t0), s0 = MathUtils.sin(t0);
            float c1 = MathUtils.cos(t1), s1 = MathUtils.sin(t1);
            if (axis == Axis.Z) {
                float x0=r*c0,y0=r*s0,x1=r*c1,y1=r*s1;
                float dx=x1-x0,dy=y1-y0,len=(float)Math.sqrt(dx*dx+dy*dy);
                float ang=MathUtils.atan2(dy,dx)*MathUtils.radiansToDegrees;
                part.setVertexTransform(new Matrix4().setToTranslation((x0+x1)*.5f,(y0+y1)*.5f,0).rotate(Vector3.Z,ang));
                part.box(len,0.065f,0.065f);
            } else if (axis == Axis.Y) {
                float x0=r*c0,z0=r*s0,x1=r*c1,z1=r*s1;
                float dx=x1-x0,dz=z1-z0,len=(float)Math.sqrt(dx*dx+dz*dz);
                float ang=MathUtils.atan2(dz,dx)*MathUtils.radiansToDegrees;
                part.setVertexTransform(new Matrix4().setToTranslation((x0+x1)*.5f,0,(z0+z1)*.5f).rotate(Vector3.Y,-ang));
                part.box(len,0.065f,0.065f);
            } else {
                float y0=r*c0,z0=r*s0,y1=r*c1,z1=r*s1;
                float dy=y1-y0,dz=z1-z0,len=(float)Math.sqrt(dy*dy+dz*dz);
                float ang=MathUtils.atan2(dz,dy)*MathUtils.radiansToDegrees;
                part.setVertexTransform(new Matrix4().setToTranslation(0,(y0+y1)*.5f,(z0+z1)*.5f).rotate(Vector3.X,ang));
                part.box(0.065f,len,0.065f);
            }
        }
    }

    @Override
    public void render() {''',
    'v8 blender gizmo geometry'
)

# Precise gizmo hit-testing. End points remain selectable even when an axis is
# almost pointing at the camera, which was the main reason Z/blue felt dead.
s = must_sub(
    s,
    r'''    private Axis hitAxis\(float sx,float sy\)\{.*?\n    \}\n\n    private Axis hitRotationArc\(float sx,float sy\)\{.*?\n    \}''',
    '''    private Axis hitAxis(float sx,float sy){
        if(!hasSelection()) return Axis.NONE;
        if(tool==Tool.ROTATE) return hitRotationArc(sx,sy);

        ObjData d=objects.get(selected).data;
        float gs=gizmoWorldScale(d);
        project(d.x,d.y,d.z,tmp2a);

        // Blender's center handle: view-plane move / uniform scale.
        if(Vector2.dst(sx,sy,tmp2a.x,tmp2a.y) <= 27f) return Axis.FREE;

        Axis plane = hitPlaneHandle(sx,sy,d,gs);
        if(plane!=Axis.NONE) return plane;

        Axis best=Axis.NONE;
        float bestD=25f;
        Axis[] axes={Axis.X,Axis.Y,Axis.Z};
        for(Axis a:axes){
            Vector3 av=axisVec(a,new Vector3());
            Vector3 ws=new Vector3(av).scl(gs*.28f).add(d.x,d.y,d.z);
            Vector3 we=new Vector3(av).scl(gs*3.20f).add(d.x,d.y,d.z);
            Vector2 ps=new Vector2(), pe=new Vector2();
            project(ws.x,ws.y,ws.z,ps); project(we.x,we.y,we.z,pe);
            float seg=pointSegmentDistance(sx,sy,ps.x,ps.y,pe.x,pe.y);
            float head=Vector2.dst(sx,sy,pe.x,pe.y);
            float dd=Math.min(seg,head*.78f);
            if(dd<bestD){bestD=dd;best=a;}
        }
        return best;
    }

    private Axis hitPlaneHandle(float sx,float sy,ObjData d,float gs){
        if(hitProjectedQuad(sx,sy,d,gs,Axis.XY))return Axis.XY;
        if(hitProjectedQuad(sx,sy,d,gs,Axis.XZ))return Axis.XZ;
        if(hitProjectedQuad(sx,sy,d,gs,Axis.YZ))return Axis.YZ;
        return Axis.NONE;
    }

    private boolean hitProjectedQuad(float sx,float sy,ObjData d,float gs,Axis plane){
        float lo=.58f*gs, hi=1.06f*gs;
        Vector3[] w=new Vector3[4];
        if(plane==Axis.XY){
            w[0]=new Vector3(d.x+lo,d.y+lo,d.z); w[1]=new Vector3(d.x+hi,d.y+lo,d.z);
            w[2]=new Vector3(d.x+hi,d.y+hi,d.z); w[3]=new Vector3(d.x+lo,d.y+hi,d.z);
        } else if(plane==Axis.XZ){
            w[0]=new Vector3(d.x+lo,d.y,d.z+lo); w[1]=new Vector3(d.x+hi,d.y,d.z+lo);
            w[2]=new Vector3(d.x+hi,d.y,d.z+hi); w[3]=new Vector3(d.x+lo,d.y,d.z+hi);
        } else {
            w[0]=new Vector3(d.x,d.y+lo,d.z+lo); w[1]=new Vector3(d.x,d.y+hi,d.z+lo);
            w[2]=new Vector3(d.x,d.y+hi,d.z+hi); w[3]=new Vector3(d.x,d.y+lo,d.z+hi);
        }
        Vector2[] p={new Vector2(),new Vector2(),new Vector2(),new Vector2()};
        for(int i=0;i<4;i++) project(w[i].x,w[i].y,w[i].z,p[i]);
        return pointInTri(sx,sy,p[0],p[1],p[2]) || pointInTri(sx,sy,p[0],p[2],p[3]);
    }

    private boolean pointInTri(float x,float y,Vector2 a,Vector2 b,Vector2 c){
        float d1=(x-b.x)*(a.y-b.y)-(a.x-b.x)*(y-b.y);
        float d2=(x-c.x)*(b.y-c.y)-(b.x-c.x)*(y-c.y);
        float d3=(x-a.x)*(c.y-a.y)-(c.x-a.x)*(y-a.y);
        boolean neg=d1<0||d2<0||d3<0, pos=d1>0||d2>0||d3>0;
        return !(neg&&pos);
    }

    private Axis hitRotationArc(float sx,float sy){
        ObjData d=objects.get(selected).data;
        float gs=gizmoWorldScale(d);
        Axis best=Axis.NONE;
        float bestD=23f;
        Axis[] axes={Axis.X,Axis.Y,Axis.Z};
        for(Axis a:axes){
            Vector2 prev=new Vector2(); boolean hp=false;
            for(int i=0;i<=64;i++){
                float deg=360f*i/64f;
                Vector3 wp=arcPoint(a,deg,gs*2.55f,new Vector3()).add(d.x,d.y,d.z);
                Vector2 cur=new Vector2(); project(wp.x,wp.y,wp.z,cur);
                if(hp){
                    float dd=pointSegmentDistance(sx,sy,prev.x,prev.y,cur.x,cur.y);
                    if(dd<bestD){bestD=dd;best=a;}
                }
                prev.set(cur); hp=true;
            }
        }
        return best;
    }''',
    'v8 gizmo picking'
)

# Replace approximate screen-delta transforms with ray/plane 3D transforms.
s = must_sub(
    s,
    r'''    private void beginTransform\(Axis a,float x,float y\)\{.*?\n    \}\n\n    private float clampScale''',
    '''    private void beginTransform(Axis a,float x,float y){
        dragAxis=a; transforming=true; orbiting=false; pendingEmptyDrag=false;
        lastX=x; lastY=y; blenderDownX=x; blenderDownY=y; pushUndo();
        if(!hasSelection()) return;

        ObjData d=objects.get(selected).data;
        blenderStartPos.set(d.x,d.y,d.z);
        blenderStartScale.set(d.sx,d.sy,d.sz);
        blenderStartRot.set(d.rx,d.ry,d.rz);
        blenderFallback=false;
        blenderStartParam=0f;
        blenderStartRadius=1f;

        project(d.x,d.y,d.z,tmp2a);
        blenderStartScreenAngle=MathUtils.atan2(-(y-tmp2a.y),x-tmp2a.x);

        if(tool==Tool.MOVE){
            initBlenderMove(a,x,y,d);
        } else if(tool==Tool.SCALE){
            initBlenderScale(a,x,y,d);
        } else if(tool==Tool.ROTATE && (a==Axis.X||a==Axis.Y||a==Axis.Z)){
            initBlenderRotate(a,x,y,d);
        }
    }

    private boolean singleAxis(Axis a){return a==Axis.X||a==Axis.Y||a==Axis.Z;}
    private boolean planeAxis(Axis a){return a==Axis.XY||a==Axis.XZ||a==Axis.YZ;}

    private Vector3 planeNormalFor(Axis a,Vector3 out){
        if(a==Axis.XY)return out.set(0,0,1);
        if(a==Axis.XZ)return out.set(0,1,0);
        if(a==Axis.YZ)return out.set(1,0,0);
        return out.set(camera.direction).nor();
    }

    private void setupAxisDragPlane(Axis a,ObjData d){
        axisVec(a,blenderAxis).nor();
        Vector3 view=new Vector3(camera.direction).nor();
        Vector3 n=new Vector3(view).sub(new Vector3(blenderAxis).scl(view.dot(blenderAxis)));
        if(n.len2()<0.0001f){
            n.set(camera.up).sub(new Vector3(blenderAxis).scl(camera.up.dot(blenderAxis)));
        }
        if(n.len2()<0.0001f){
            n.set(blenderAxis).crs(Math.abs(blenderAxis.y)<.9f?Vector3.Y:Vector3.X);
        }
        n.nor();
        blenderDragPlane.set(n,blenderStartPos);
    }

    private boolean dragPlaneHit(float sx,float sy,Vector3 out){
        return Intersector.intersectRayPlane(camera.getPickRay(sx,sy),blenderDragPlane,out);
    }

    private void initBlenderMove(Axis a,float x,float y,ObjData d){
        if(singleAxis(a)){
            setupAxisDragPlane(a,d);
            Vector3 hp=new Vector3();
            if(dragPlaneHit(x,y,hp)) blenderStartParam=new Vector3(hp).sub(blenderStartPos).dot(blenderAxis);
            else blenderFallback=true;
        } else {
            Vector3 n=planeNormalFor(a,new Vector3());
            blenderDragPlane.set(n,blenderStartPos);
            if(!dragPlaneHit(x,y,blenderStartHit)) blenderFallback=true;
        }
    }

    private void initBlenderScale(Axis a,float x,float y,ObjData d){
        if(singleAxis(a)){
            setupAxisDragPlane(a,d);
            Vector3 hp=new Vector3();
            if(dragPlaneHit(x,y,hp)){
                blenderStartParam=new Vector3(hp).sub(blenderStartPos).dot(blenderAxis);
                if(Math.abs(blenderStartParam)<gizmoWorldScale(d)*.20f) blenderStartParam=gizmoWorldScale(d)*2.85f;
            } else blenderFallback=true;
        } else if(planeAxis(a)){
            blenderDragPlane.set(planeNormalFor(a,new Vector3()),blenderStartPos);
            if(dragPlaneHit(x,y,blenderStartHit)){
                blenderStartRadius=Math.max(.0001f,new Vector3(blenderStartHit).sub(blenderStartPos).len());
            } else blenderFallback=true;
        } else {
            project(d.x,d.y,d.z,tmp2a);
            blenderStartRadius=Math.max(18f,Vector2.dst(x,y,tmp2a.x,tmp2a.y));
        }
    }

    private void initBlenderRotate(Axis a,float x,float y,ObjData d){
        axisVec(a,blenderAxis).nor();
        blenderDragPlane.set(blenderAxis,blenderStartPos);
        Vector3 hp=new Vector3();
        if(dragPlaneHit(x,y,hp)){
            blenderStartHit.set(hp).sub(blenderStartPos);
            if(blenderStartHit.len2()>0.000001f) blenderStartHit.nor(); else blenderFallback=true;
        } else blenderFallback=true;
    }

    private void transformDrag(float x,float y){
        if(!hasSelection())return;
        ObjData d=objects.get(selected).data;

        if(tool==Tool.MOVE){
            blenderMoveDrag(x,y,d);
        } else if(tool==Tool.SCALE){
            blenderScaleDrag(x,y,d);
        } else if(tool==Tool.ROTATE){
            blenderRotateDrag(x,y,d);
        }

        apply(objects.get(selected));
        pivot.set(d.x,d.y,d.z);
        emitSelection();
        lastX=x; lastY=y;
    }

    private void blenderMoveDrag(float x,float y,ObjData d){
        if(singleAxis(dragAxis)){
            float amount;
            Vector3 hp=new Vector3();
            if(!blenderFallback && dragPlaneHit(x,y,hp)){
                float p=new Vector3(hp).sub(blenderStartPos).dot(blenderAxis);
                amount=p-blenderStartParam;
            } else {
                amount=screenAxisWorldAmount(dragAxis,x-blenderDownX,y-blenderDownY,d);
            }
            Vector3 v=axisVec(dragAxis,new Vector3()).scl(amount);
            d.x=blenderStartPos.x+v.x; d.y=blenderStartPos.y+v.y; d.z=blenderStartPos.z+v.z;
            return;
        }

        Vector3 hp=new Vector3();
        if(!blenderFallback && dragPlaneHit(x,y,hp)){
            Vector3 delta=hp.sub(blenderStartHit);
            if(dragAxis==Axis.XY)delta.z=0;
            else if(dragAxis==Axis.XZ)delta.y=0;
            else if(dragAxis==Axis.YZ)delta.x=0;
            d.x=blenderStartPos.x+delta.x; d.y=blenderStartPos.y+delta.y; d.z=blenderStartPos.z+delta.z;
        } else {
            float dx=x-blenderDownX,dy=y-blenderDownY;
            Vector3 right=new Vector3(camera.direction).crs(camera.up).nor();
            Vector3 up=new Vector3(right).crs(camera.direction).nor();
            float k=Math.max(.00005f,distance*.0030f);
            Vector3 delta=right.scl(dx*k).mulAdd(up,-dy*k);
            if(dragAxis==Axis.XY)delta.z=0; else if(dragAxis==Axis.XZ)delta.y=0; else if(dragAxis==Axis.YZ)delta.x=0;
            d.x=blenderStartPos.x+delta.x; d.y=blenderStartPos.y+delta.y; d.z=blenderStartPos.z+delta.z;
        }
    }

    private void blenderScaleDrag(float x,float y,ObjData d){
        if(singleAxis(dragAxis)){
            float factor;
            Vector3 hp=new Vector3();
            if(!blenderFallback && dragPlaneHit(x,y,hp)){
                float p=new Vector3(hp).sub(blenderStartPos).dot(blenderAxis);
                factor=p/blenderStartParam;
                if(factor<.0001f)factor=.0001f;
            } else {
                float along=axisScreenPixelDelta(dragAxis,x-blenderDownX,y-blenderDownY,d);
                factor=(float)Math.exp(along*.010f);
            }
            if(dragAxis==Axis.X)d.sx=clampScale(blenderStartScale.x*factor);
            else if(dragAxis==Axis.Y)d.sy=clampScale(blenderStartScale.y*factor);
            else d.sz=clampScale(blenderStartScale.z*factor);
            return;
        }

        float factor=1f;
        if(planeAxis(dragAxis)){
            Vector3 hp=new Vector3();
            if(!blenderFallback && dragPlaneHit(x,y,hp)) factor=Math.max(.0001f,new Vector3(hp).sub(blenderStartPos).len()/blenderStartRadius);
            else factor=(float)Math.exp(((x-blenderDownX)-(y-blenderDownY))*.006f);
            if(dragAxis==Axis.XY){d.sx=clampScale(blenderStartScale.x*factor);d.sy=clampScale(blenderStartScale.y*factor);}
            else if(dragAxis==Axis.XZ){d.sx=clampScale(blenderStartScale.x*factor);d.sz=clampScale(blenderStartScale.z*factor);}
            else {d.sy=clampScale(blenderStartScale.y*factor);d.sz=clampScale(blenderStartScale.z*factor);}
            return;
        }

        project(blenderStartPos.x,blenderStartPos.y,blenderStartPos.z,tmp2a);
        float r=Math.max(1f,Vector2.dst(x,y,tmp2a.x,tmp2a.y));
        factor=Math.max(.0001f,r/blenderStartRadius);
        d.sx=clampScale(blenderStartScale.x*factor);
        d.sy=clampScale(blenderStartScale.y*factor);
        d.sz=clampScale(blenderStartScale.z*factor);
    }

    private void blenderRotateDrag(float x,float y,ObjData d){
        if(singleAxis(dragAxis)){
            float angle;
            Vector3 hp=new Vector3();
            if(!blenderFallback && dragPlaneHit(x,y,hp)){
                Vector3 cur=hp.sub(blenderStartPos);
                if(cur.len2()<.000001f)return;
                cur.nor();
                float sin=blenderAxis.dot(new Vector3(blenderStartHit).crs(cur));
                float cos=MathUtils.clamp(blenderStartHit.dot(cur),-1f,1f);
                angle=MathUtils.atan2(sin,cos)*MathUtils.radiansToDegrees;
            } else {
                project(blenderStartPos.x,blenderStartPos.y,blenderStartPos.z,tmp2a);
                float now=MathUtils.atan2(-(y-tmp2a.y),x-tmp2a.x);
                float da=now-blenderStartScreenAngle;
                while(da>MathUtils.PI)da-=MathUtils.PI2;
                while(da<-MathUtils.PI)da+=MathUtils.PI2;
                float facing=axisVec(dragAxis,new Vector3()).dot(camera.direction);
                angle=da*MathUtils.radiansToDegrees*(facing<0?-1f:1f);
            }
            d.rx=blenderStartRot.x; d.ry=blenderStartRot.y; d.rz=blenderStartRot.z;
            if(dragAxis==Axis.X)d.rx+=angle; else if(dragAxis==Axis.Y)d.ry+=angle; else d.rz+=angle;
            return;
        }

        // Trackball-like free rotation for the center/object drag.
        float dx=x-blenderDownX,dy=y-blenderDownY;
        d.rx=blenderStartRot.x+dy*.32f;
        d.ry=blenderStartRot.y-dx*.32f;
        d.rz=blenderStartRot.z;
    }

    private float screenAxisWorldAmount(Axis a,float dx,float dy,ObjData d){
        Vector2 dir=axisScreenDir(a,d,new Vector2());
        float projected=axisProjectedPixels(a,d);
        if(projected<5f){
            // An axis looking almost straight into the camera collapses to a point.
            // Blender still lets the handle be picked; vertical finger motion is used
            // here as the stable mobile equivalent for depth motion.
            return -dy*Math.max(.00005f,distance*.0030f);
        }
        float along=dx*dir.x+dy*dir.y;
        return along*(gizmoWorldScale(d)*2.85f/projected);
    }

    private float clampScale''',
    'v8 blender transform math'
)

engine_path.write_text(s, encoding='utf-8')

b = build_path.read_text(encoding='utf-8')
b = re.sub(r'versionCode\s+\d+', 'versionCode 8', b)
b = re.sub(r"versionName\s+'[^']+'", "versionName '0.8-blender-gizmo'", b)
build_path.write_text(b, encoding='utf-8')

print('V8 Blender-style gizmo patch applied successfully')
