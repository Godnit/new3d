using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace TerrainStudio
{
    public sealed class TerrainSaveSystem : MonoBehaviour
    {
        public RuntimeTerrain terrain;
        public TerrainEditorController editor;

        private string SavePath => Path.Combine(Application.persistentDataPath, "terrain_studio_map.json");

        public bool Save()
        {
            if (terrain == null || editor == null) return false;

            TerrainSnapshot snapshot = terrain.CaptureSnapshot();
            TerrainMapData data = new TerrainMapData
            {
                resolution = snapshot.resolution,
                size = snapshot.size,
                heights = snapshot.heights,
                colors = PackColors(snapshot.colors),
                props = new List<PropData>()
            };

            foreach (GameObject prop in editor.Props)
            {
                if (prop == null) continue;
                data.props.Add(new PropData
                {
                    type = prop.name == "Rock" ? 1 : 0,
                    position = prop.transform.position,
                    rotation = prop.transform.eulerAngles,
                    scale = prop.transform.localScale
                });
            }

            File.WriteAllText(SavePath, JsonUtility.ToJson(data));
            return true;
        }

        public bool Load()
        {
            if (terrain == null || editor == null || !File.Exists(SavePath)) return false;

            try
            {
                TerrainMapData data = JsonUtility.FromJson<TerrainMapData>(File.ReadAllText(SavePath));
                if (data == null || data.heights == null) return false;

                Color32[] unpacked = UnpackColors(data.colors, data.heights.Length);
                terrain.RestoreSnapshot(new TerrainSnapshot(data.resolution, data.size, data.heights, unpacked));
                editor.ClearPropsForLoad();

                if (data.props != null)
                {
                    foreach (PropData prop in data.props)
                    {
                        GameObject instance = prop.type == 1
                            ? PropFactory.CreateRock(prop.position)
                            : PropFactory.CreateTree(prop.position);
                        instance.transform.position = prop.position;
                        instance.transform.eulerAngles = prop.rotation;
                        instance.transform.localScale = prop.scale;
                        editor.RegisterLoadedProp(instance);
                    }
                }
                return true;
            }
            catch (Exception exception)
            {
                Debug.LogWarning("Terrain Studio load failed: " + exception.Message);
                return false;
            }
        }

        private static byte[] PackColors(Color32[] source)
        {
            if (source == null) return Array.Empty<byte>();
            byte[] bytes = new byte[source.Length * 4];
            for (int i = 0; i < source.Length; i++)
            {
                int p = i * 4;
                bytes[p] = source[i].r;
                bytes[p + 1] = source[i].g;
                bytes[p + 2] = source[i].b;
                bytes[p + 3] = source[i].a;
            }
            return bytes;
        }

        private static Color32[] UnpackColors(byte[] bytes, int count)
        {
            Color32[] result = new Color32[count];
            Color32 fallback = new Color32(56, 122, 43, 255);
            for (int i = 0; i < count; i++)
            {
                int p = i * 4;
                result[i] = bytes != null && p + 3 < bytes.Length
                    ? new Color32(bytes[p], bytes[p + 1], bytes[p + 2], bytes[p + 3])
                    : fallback;
            }
            return result;
        }
    }

    [Serializable]
    public sealed class TerrainMapData
    {
        public int resolution;
        public float size;
        public float[] heights;
        public byte[] colors;
        public List<PropData> props;
    }

    [Serializable]
    public sealed class PropData
    {
        public int type;
        public Vector3 position;
        public Vector3 rotation;
        public Vector3 scale;
    }
}
