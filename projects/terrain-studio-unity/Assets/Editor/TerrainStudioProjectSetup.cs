#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TerrainStudio.Editor
{
    public static class TerrainStudioProjectSetup
    {
        private const string PipelinePath = "Assets/Settings/TerrainStudioURP.asset";

        [InitializeOnLoadMethod]
        private static void ScheduleSetup()
        {
            EditorApplication.delayCall += EnsureSetup;
        }

        public static void EnsureSetup()
        {
            ConfigurePipeline();
            ConfigureAndroid();
            AssetDatabase.SaveAssets();
        }

        private static void ConfigurePipeline()
        {
            Directory.CreateDirectory("Assets/Settings");
            UniversalRenderPipelineAsset pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelinePath);
            if (pipeline == null)
            {
                pipeline = ScriptableObject.CreateInstance<UniversalRenderPipelineAsset>();
                AssetDatabase.CreateAsset(pipeline, PipelinePath);
                ScriptableRendererData renderer = pipeline.LoadBuiltinRendererData(RendererType.UniversalRenderer);
                if (renderer != null && !AssetDatabase.Contains(renderer))
                    AssetDatabase.AddObjectToAsset(renderer, pipeline);
            }

            pipeline.name = "TerrainStudioURP";
            pipeline.renderScale = 0.88f;
            pipeline.msaaSampleCount = 2;
            pipeline.shadowDistance = 40f;
            pipeline.shadowCascadeCount = 2;
            pipeline.supportsHDR = false;
            pipeline.supportsCameraDepthTexture = false;
            pipeline.supportsCameraOpaqueTexture = false;
            pipeline.supportsMainLightShadows = true;
            pipeline.supportsAdditionalLightShadows = false;
            pipeline.supportsSoftShadows = true;
            pipeline.useSRPBatcher = true;

            GraphicsSettings.defaultRenderPipeline = pipeline;
            QualitySettings.renderPipeline = pipeline;
            EditorUtility.SetDirty(pipeline);
        }

        private static void ConfigureAndroid()
        {
            PlayerSettings.companyName = "Godnit";
            PlayerSettings.productName = "Terrain Studio";
            PlayerSettings.bundleVersion = "0.2.0";
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, "com.godnit.terrainstudio.unity");
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.LandscapeLeft;
            PlayerSettings.colorSpace = ColorSpace.Gamma;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel23;
            PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevelAuto;
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARMv7;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.Mono2x);
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.Android, false);
            PlayerSettings.SetGraphicsAPIs(BuildTarget.Android, new[] { GraphicsDeviceType.OpenGLES3 });
            PlayerSettings.MTRendering = true;
            PlayerSettings.graphicsJobs = false;
            PlayerSettings.stripEngineCode = true;
            EditorUserBuildSettings.androidBuildSystem = AndroidBuildSystem.Gradle;
            EditorUserBuildSettings.buildAppBundle = false;
        }
    }
}
#endif
