#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;

namespace TerrainStudio.Editor
{
    public static class TerrainStudioBuild
    {
        public static void BuildAndroid()
        {
            TerrainStudioProjectSetup.EnsureSetup();

            const string generatedFolder = "Assets/Generated";
            const string scenePath = generatedFolder + "/TerrainStudioMain.unity";
            Directory.CreateDirectory(generatedFolder);

            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorSceneManager.SaveScene(scene, scenePath);
            AssetDatabase.SaveAssets();

            string output = Environment.GetEnvironmentVariable("UNITY_BUILD_PATH");
            if (string.IsNullOrWhiteSpace(output))
                output = "Build/TerrainStudio-Unity6.apk";

            string directory = Path.GetDirectoryName(output);
            if (!string.IsNullOrEmpty(directory))
                Directory.CreateDirectory(directory);

            BuildPlayerOptions options = new BuildPlayerOptions
            {
                scenes = new[] { scenePath },
                locationPathName = output,
                target = BuildTarget.Android,
                options = BuildOptions.CompressWithLz4HC
            };

            BuildReport report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded)
                throw new Exception("Terrain Studio Android build failed: " + report.summary.result);

            UnityEngine.Debug.Log($"Terrain Studio APK built: {output} ({report.summary.totalSize} bytes)");
        }
    }
}
#endif
