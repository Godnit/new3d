using System;
using UnityEngine;

namespace TerrainStudio
{
    public enum TerrainTool
    {
        Camera,
        Raise,
        Lower,
        Smooth,
        Flatten,
        Paint,
        Tree,
        Rock,
        Erase
    }

    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer), typeof(MeshCollider))]
    public sealed class RuntimeTerrain : MonoBehaviour
    {
        [SerializeField] private int resolution = 65;
        [SerializeField] private float size = 48f;
        [SerializeField] private float maxHeight = 12f;

        private Mesh mesh;
        private MeshCollider meshCollider;
        private Vector3[] vertices;
        private int[] triangles;
        private Color[] colors;
        private Vector2[] uvs;
        private float[] smoothBuffer;

        public int Resolution => resolution;
        public float Size => size;
        public Vector3[] Vertices => vertices;
        public Color[] Colors => colors;

        public void Initialize(Material terrainMaterial)
        {
            resolution = Mathf.Clamp(resolution, 17, 129);
            meshCollider = GetComponent<MeshCollider>();
            GetComponent<MeshRenderer>().sharedMaterial = terrainMaterial;
            BuildFlatMesh();
        }

        private void BuildFlatMesh()
        {
            int count = resolution * resolution;
            vertices = new Vector3[count];
            colors = new Color[count];
            uvs = new Vector2[count];
            smoothBuffer = new float[count];

            float step = size / (resolution - 1);
            float half = size * 0.5f;
            Color baseColor = new Color(0.22f, 0.48f, 0.17f, 1f);

            for (int z = 0; z < resolution; z++)
            {
                for (int x = 0; x < resolution; x++)
                {
                    int i = z * resolution + x;
                    vertices[i] = new Vector3(-half + x * step, 0f, -half + z * step);
                    colors[i] = baseColor;
                    uvs[i] = new Vector2((float)x / (resolution - 1), (float)z / (resolution - 1));
                }
            }

            triangles = new int[(resolution - 1) * (resolution - 1) * 6];
            int t = 0;
            for (int z = 0; z < resolution - 1; z++)
            {
                for (int x = 0; x < resolution - 1; x++)
                {
                    int i = z * resolution + x;
                    triangles[t++] = i;
                    triangles[t++] = i + resolution;
                    triangles[t++] = i + 1;
                    triangles[t++] = i + 1;
                    triangles[t++] = i + resolution;
                    triangles[t++] = i + resolution + 1;
                }
            }

            mesh = new Mesh { name = "TerrainStudio_RuntimeTerrain" };
            mesh.indexFormat = count > 65535
                ? UnityEngine.Rendering.IndexFormat.UInt32
                : UnityEngine.Rendering.IndexFormat.UInt16;
            mesh.MarkDynamic();
            mesh.vertices = vertices;
            mesh.triangles = triangles;
            mesh.colors = colors;
            mesh.uv = uvs;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();

            GetComponent<MeshFilter>().sharedMesh = mesh;
            meshCollider.sharedMesh = mesh;
        }

        public bool ApplyBrush(Vector3 worldPoint, TerrainTool tool, float radius, float strength, Color paintColor)
        {
            if (tool == TerrainTool.Camera || tool == TerrainTool.Tree || tool == TerrainTool.Rock || tool == TerrainTool.Erase)
                return false;

            Vector3 local = transform.InverseTransformPoint(worldPoint);
            float radiusSq = radius * radius;
            bool changed = false;

            if (tool == TerrainTool.Smooth)
                PrepareSmoothValues();

            for (int i = 0; i < vertices.Length; i++)
            {
                Vector3 v = vertices[i];
                float dx = v.x - local.x;
                float dz = v.z - local.z;
                float distSq = dx * dx + dz * dz;
                if (distSq > radiusSq)
                    continue;

                float dist = Mathf.Sqrt(distSq);
                float falloff = 1f - Mathf.SmoothStep(0f, 1f, dist / Mathf.Max(0.001f, radius));
                float amount = strength * falloff * Time.deltaTime * 8f;

                switch (tool)
                {
                    case TerrainTool.Raise:
                        v.y = Mathf.Min(maxHeight, v.y + amount);
                        vertices[i] = v;
                        changed = true;
                        break;
                    case TerrainTool.Lower:
                        v.y = Mathf.Max(-maxHeight * 0.35f, v.y - amount);
                        vertices[i] = v;
                        changed = true;
                        break;
                    case TerrainTool.Flatten:
                        v.y = Mathf.Lerp(v.y, local.y, Mathf.Clamp01(amount * 0.7f));
                        vertices[i] = v;
                        changed = true;
                        break;
                    case TerrainTool.Smooth:
                        v.y = Mathf.Lerp(v.y, smoothBuffer[i], Mathf.Clamp01(amount));
                        vertices[i] = v;
                        changed = true;
                        break;
                    case TerrainTool.Paint:
                        colors[i] = Color.Lerp(colors[i], paintColor, Mathf.Clamp01(amount * 0.8f));
                        changed = true;
                        break;
                }
            }

            if (changed)
                ApplyMeshChanges(tool != TerrainTool.Paint);

            return changed;
        }

        private void PrepareSmoothValues()
        {
            for (int z = 0; z < resolution; z++)
            {
                for (int x = 0; x < resolution; x++)
                {
                    float total = 0f;
                    int count = 0;
                    for (int oz = -1; oz <= 1; oz++)
                    {
                        int zz = z + oz;
                        if (zz < 0 || zz >= resolution) continue;
                        for (int ox = -1; ox <= 1; ox++)
                        {
                            int xx = x + ox;
                            if (xx < 0 || xx >= resolution) continue;
                            total += vertices[zz * resolution + xx].y;
                            count++;
                        }
                    }
                    smoothBuffer[z * resolution + x] = total / Mathf.Max(1, count);
                }
            }
        }

        private void ApplyMeshChanges(bool geometryChanged)
        {
            if (geometryChanged)
            {
                mesh.vertices = vertices;
                mesh.RecalculateNormals();
                mesh.RecalculateBounds();
                meshCollider.sharedMesh = null;
                meshCollider.sharedMesh = mesh;
            }
            mesh.colors = colors;
        }

        public float SampleHeight(Vector3 worldPosition)
        {
            Vector3 local = transform.InverseTransformPoint(worldPosition);
            float half = size * 0.5f;
            float nx = Mathf.Clamp01((local.x + half) / size) * (resolution - 1);
            float nz = Mathf.Clamp01((local.z + half) / size) * (resolution - 1);
            int x0 = Mathf.Clamp(Mathf.FloorToInt(nx), 0, resolution - 1);
            int z0 = Mathf.Clamp(Mathf.FloorToInt(nz), 0, resolution - 1);
            int x1 = Mathf.Min(x0 + 1, resolution - 1);
            int z1 = Mathf.Min(z0 + 1, resolution - 1);
            float tx = nx - x0;
            float tz = nz - z0;
            float a = Mathf.Lerp(vertices[z0 * resolution + x0].y, vertices[z0 * resolution + x1].y, tx);
            float b = Mathf.Lerp(vertices[z1 * resolution + x0].y, vertices[z1 * resolution + x1].y, tx);
            return Mathf.Lerp(a, b, tz) + transform.position.y;
        }

        public TerrainSnapshot CaptureSnapshot()
        {
            float[] heights = new float[vertices.Length];
            Color32[] packedColors = new Color32[colors.Length];
            for (int i = 0; i < vertices.Length; i++)
            {
                heights[i] = vertices[i].y;
                packedColors[i] = colors[i];
            }
            return new TerrainSnapshot(resolution, size, heights, packedColors);
        }

        public void RestoreSnapshot(TerrainSnapshot snapshot)
        {
            if (snapshot == null || snapshot.resolution != resolution || snapshot.heights == null || snapshot.heights.Length != vertices.Length)
                return;

            for (int i = 0; i < vertices.Length; i++)
            {
                Vector3 v = vertices[i];
                v.y = snapshot.heights[i];
                vertices[i] = v;
                if (snapshot.colors != null && i < snapshot.colors.Length)
                    colors[i] = snapshot.colors[i];
            }
            ApplyMeshChanges(true);
        }
    }

    [Serializable]
    public sealed class TerrainSnapshot
    {
        public int resolution;
        public float size;
        public float[] heights;
        public Color32[] colors;

        public TerrainSnapshot(int resolution, float size, float[] heights, Color32[] colors)
        {
            this.resolution = resolution;
            this.size = size;
            this.heights = heights;
            this.colors = colors;
        }
    }
}
