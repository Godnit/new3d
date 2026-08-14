using UnityEngine;

namespace TerrainStudio
{
    public static class PropFactory
    {
        private static Material trunkMaterial;
        private static Material leafMaterial;
        private static Material rockMaterial;

        public static GameObject CreateTree(Vector3 position)
        {
            EnsureMaterials();
            GameObject root = new GameObject("Tree");
            root.transform.position = position;

            GameObject trunk = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            trunk.name = "Trunk";
            trunk.transform.SetParent(root.transform, false);
            trunk.transform.localPosition = new Vector3(0f, 1.1f, 0f);
            trunk.transform.localScale = new Vector3(0.35f, 1.1f, 0.35f);
            trunk.GetComponent<Renderer>().sharedMaterial = trunkMaterial;

            GameObject crownA = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            crownA.name = "CrownA";
            crownA.transform.SetParent(root.transform, false);
            crownA.transform.localPosition = new Vector3(0f, 2.65f, 0f);
            crownA.transform.localScale = new Vector3(2.0f, 1.6f, 2.0f);
            crownA.GetComponent<Renderer>().sharedMaterial = leafMaterial;

            GameObject crownB = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            crownB.name = "CrownB";
            crownB.transform.SetParent(root.transform, false);
            crownB.transform.localPosition = new Vector3(0.35f, 3.35f, 0.15f);
            crownB.transform.localScale = new Vector3(1.4f, 1.2f, 1.4f);
            crownB.GetComponent<Renderer>().sharedMaterial = leafMaterial;

            float scale = Random.Range(0.85f, 1.2f);
            root.transform.localScale = Vector3.one * scale;
            root.transform.rotation = Quaternion.Euler(0f, Random.Range(0f, 360f), 0f);
            return root;
        }

        public static GameObject CreateRock(Vector3 position)
        {
            EnsureMaterials();
            GameObject rock = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            rock.name = "Rock";
            rock.transform.position = position + Vector3.up * 0.35f;
            rock.transform.localScale = new Vector3(Random.Range(1.1f, 1.8f), Random.Range(0.55f, 0.9f), Random.Range(0.9f, 1.5f));
            rock.transform.rotation = Quaternion.Euler(Random.Range(-15f, 15f), Random.Range(0f, 360f), Random.Range(-12f, 12f));
            rock.GetComponent<Renderer>().sharedMaterial = rockMaterial;
            return rock;
        }

        private static void EnsureMaterials()
        {
            if (trunkMaterial != null) return;
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");

            trunkMaterial = new Material(shader) { color = new Color(0.28f, 0.13f, 0.055f) };
            leafMaterial = new Material(shader) { color = new Color(0.12f, 0.42f, 0.10f) };
            rockMaterial = new Material(shader) { color = new Color(0.38f, 0.40f, 0.39f) };

            SetSmoothness(trunkMaterial, 0.1f);
            SetSmoothness(leafMaterial, 0.16f);
            SetSmoothness(rockMaterial, 0.22f);
        }

        private static void SetSmoothness(Material material, float value)
        {
            if (material.HasProperty("_Smoothness")) material.SetFloat("_Smoothness", value);
        }
    }
}
