using UnityEngine;
using UnityEngine.Rendering;

namespace TerrainStudio
{
    public sealed class TerrainStudioBootstrap : MonoBehaviour
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void AutoStart()
        {
            if (FindAnyObjectByType<TerrainStudioBootstrap>() != null)
                return;
            new GameObject("TerrainStudioBootstrap").AddComponent<TerrainStudioBootstrap>();
        }

        private void Awake()
        {
            Application.targetFrameRate = 60;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Screen.orientation = ScreenOrientation.LandscapeLeft;
            QualitySettings.vSyncCount = 0;
            QualitySettings.antiAliasing = 2;
            QualitySettings.shadowDistance = 40f;
            QualitySettings.shadows = ShadowQuality.All;
            QualitySettings.shadowResolution = ShadowResolution.Medium;

            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.58f, 0.76f, 0.88f);
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogStartDistance = 38f;
            RenderSettings.fogEndDistance = 82f;
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.52f, 0.58f, 0.64f);

            Camera camera = CreateCamera();
            CreateSun();
            RuntimeTerrain terrain = CreateTerrain();

            GameObject systems = new GameObject("TerrainStudioSystems");
            TerrainEditorController editor = systems.AddComponent<TerrainEditorController>();
            OrbitTouchCamera orbit = camera.GetComponent<OrbitTouchCamera>();
            editor.Initialize(terrain, camera, orbit);

            TerrainSaveSystem saveSystem = systems.AddComponent<TerrainSaveSystem>();
            saveSystem.terrain = terrain;
            saveSystem.editor = editor;

            TerrainStudioUI ui = systems.AddComponent<TerrainStudioUI>();
            ui.Initialize(editor, saveSystem);
        }

        private static Camera CreateCamera()
        {
            GameObject go = new GameObject("Main Camera");
            go.tag = "MainCamera";
            Camera camera = go.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.42f, 0.69f, 0.88f);
            camera.fieldOfView = 48f;
            camera.nearClipPlane = 0.15f;
            camera.farClipPlane = 180f;
            camera.allowHDR = false;
            camera.allowMSAA = true;

            OrbitTouchCamera orbit = go.AddComponent<OrbitTouchCamera>();
            orbit.target = new Vector3(0f, 0.8f, 0f);
            orbit.distance = 34f;
            orbit.yaw = 40f;
            orbit.pitch = 52f;
            return camera;
        }

        private static void CreateSun()
        {
            GameObject go = new GameObject("Sun");
            Light light = go.AddComponent<Light>();
            light.type = LightType.Directional;
            light.color = new Color(1f, 0.955f, 0.84f);
            light.intensity = 1.18f;
            light.shadows = LightShadows.Soft;
            light.shadowStrength = 0.78f;
            light.shadowBias = 0.045f;
            light.shadowNormalBias = 0.35f;
            light.transform.rotation = Quaternion.Euler(48f, -32f, 0f);
            RenderSettings.sun = light;
        }

        private static RuntimeTerrain CreateTerrain()
        {
            GameObject terrainObject = new GameObject("EditableTerrain", typeof(MeshFilter), typeof(MeshRenderer), typeof(MeshCollider), typeof(RuntimeTerrain));
            RuntimeTerrain terrain = terrainObject.GetComponent<RuntimeTerrain>();

            Shader shader = Shader.Find("TerrainStudio/VertexLit");
            if (shader == null) shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");

            Material material = new Material(shader) { name = "TerrainRuntimeMaterial" };
            if (material.HasProperty("_Tint")) material.SetColor("_Tint", Color.white);
            if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", Color.white);
            terrain.Initialize(material);
            terrainObject.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.On;
            terrainObject.GetComponent<MeshRenderer>().receiveShadows = true;
            return terrain;
        }
    }
}
