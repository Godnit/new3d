using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace TerrainStudio
{
    public sealed class TerrainEditorController : MonoBehaviour
    {
        public RuntimeTerrain terrain;
        public Camera sceneCamera;
        public OrbitTouchCamera orbitCamera;

        public TerrainTool CurrentTool { get; private set; } = TerrainTool.Camera;
        public float BrushRadius { get; private set; } = 3.2f;
        public float BrushStrength { get; private set; } = 0.9f;
        public Color PaintColor { get; private set; } = new Color(0.22f, 0.48f, 0.17f, 1f);

        private readonly Stack<TerrainSnapshot> undoStack = new Stack<TerrainSnapshot>();
        private readonly List<GameObject> props = new List<GameObject>();
        private TerrainSnapshot blankSnapshot;
        private Vector2 previousSingleTouch;
        private bool singleTouchActive;
        private float lastPropPlacementTime;

        public IReadOnlyList<GameObject> Props => props;

        public void Initialize(RuntimeTerrain runtimeTerrain, Camera camera, OrbitTouchCamera orbit)
        {
            terrain = runtimeTerrain;
            sceneCamera = camera;
            orbitCamera = orbit;
            blankSnapshot = terrain.CaptureSnapshot();
        }

        private void Update()
        {
            if (terrain == null || sceneCamera == null)
                return;

            if (Input.touchCount != 1)
            {
                singleTouchActive = false;
                return;
            }

            Touch touch = Input.GetTouch(0);
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject(touch.fingerId))
            {
                singleTouchActive = false;
                return;
            }

            if (touch.phase == TouchPhase.Began)
            {
                previousSingleTouch = touch.position;
                singleTouchActive = true;
                if (IsTerrainEditingTool(CurrentTool))
                    PushUndoSnapshot();
            }

            if (!singleTouchActive)
                return;

            if (CurrentTool == TerrainTool.Camera)
            {
                if (touch.phase == TouchPhase.Moved)
                {
                    Vector2 delta = touch.position - previousSingleTouch;
                    orbitCamera.Orbit(delta.x * 0.12f, -delta.y * 0.09f);
                    previousSingleTouch = touch.position;
                }
                return;
            }

            if (touch.phase == TouchPhase.Ended || touch.phase == TouchPhase.Canceled)
            {
                singleTouchActive = false;
                return;
            }

            Ray ray = sceneCamera.ScreenPointToRay(touch.position);
            if (!Physics.Raycast(ray, out RaycastHit hit, 200f))
                return;

            RuntimeTerrain hitTerrain = hit.collider.GetComponent<RuntimeTerrain>();
            bool isTerrainHit = hitTerrain == terrain;

            if (IsTerrainEditingTool(CurrentTool))
            {
                if (isTerrainHit)
                    terrain.ApplyBrush(hit.point, CurrentTool, BrushRadius, BrushStrength, PaintColor);
                return;
            }

            if (CurrentTool == TerrainTool.Tree || CurrentTool == TerrainTool.Rock)
            {
                if (!isTerrainHit || Time.unscaledTime - lastPropPlacementTime < 0.18f)
                    return;

                GameObject prop = CurrentTool == TerrainTool.Tree
                    ? PropFactory.CreateTree(hit.point)
                    : PropFactory.CreateRock(hit.point);
                props.Add(prop);
                lastPropPlacementTime = Time.unscaledTime;
                return;
            }

            if (CurrentTool == TerrainTool.Erase)
            {
                GameObject root = FindPropRoot(hit.collider.gameObject);
                if (root != null)
                {
                    props.Remove(root);
                    Destroy(root);
                }
            }
        }

        public void SetTool(TerrainTool tool)
        {
            CurrentTool = tool;
        }

        public void SetBrushRadius(float value)
        {
            BrushRadius = Mathf.Clamp(value, 0.8f, 8f);
        }

        public void SetBrushStrength(float value)
        {
            BrushStrength = Mathf.Clamp(value, 0.15f, 2.5f);
        }

        public void SetPaintColor(Color color)
        {
            PaintColor = color;
            CurrentTool = TerrainTool.Paint;
        }

        public void Undo()
        {
            if (undoStack.Count > 0)
                terrain.RestoreSnapshot(undoStack.Pop());
        }

        public void NewMap()
        {
            PushUndoSnapshot();
            terrain.RestoreSnapshot(blankSnapshot);
            for (int i = props.Count - 1; i >= 0; i--)
            {
                if (props[i] != null)
                    Destroy(props[i]);
            }
            props.Clear();
        }

        public void RegisterLoadedProp(GameObject prop)
        {
            if (prop != null)
                props.Add(prop);
        }

        public void ClearPropsForLoad()
        {
            for (int i = props.Count - 1; i >= 0; i--)
            {
                if (props[i] != null)
                    Destroy(props[i]);
            }
            props.Clear();
        }

        private void PushUndoSnapshot()
        {
            if (undoStack.Count >= 12)
            {
                TerrainSnapshot[] snapshots = undoStack.ToArray();
                undoStack.Clear();
                for (int i = snapshots.Length - 2; i >= 0; i--)
                    undoStack.Push(snapshots[i]);
            }
            undoStack.Push(terrain.CaptureSnapshot());
        }

        private static bool IsTerrainEditingTool(TerrainTool tool)
        {
            return tool == TerrainTool.Raise || tool == TerrainTool.Lower || tool == TerrainTool.Smooth ||
                   tool == TerrainTool.Flatten || tool == TerrainTool.Paint;
        }

        private static GameObject FindPropRoot(GameObject obj)
        {
            Transform t = obj.transform;
            while (t != null)
            {
                if (t.name == "Tree" || t.name == "Rock")
                    return t.gameObject;
                t = t.parent;
            }
            return null;
        }
    }
}
