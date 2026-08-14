using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace TerrainStudio
{
    public sealed class TerrainStudioUI : MonoBehaviour
    {
        private TerrainEditorController editor;
        private TerrainSaveSystem saveSystem;
        private Font uiFont;
        private Text statusText;
        private Slider radiusSlider;
        private Slider strengthSlider;

        private static readonly Color PanelColor = new Color(0.055f, 0.065f, 0.085f, 0.94f);
        private static readonly Color ButtonColor = new Color(0.11f, 0.14f, 0.18f, 0.96f);
        private static readonly Color AccentColor = new Color(0.15f, 0.74f, 0.58f, 1f);

        public void Initialize(TerrainEditorController controller, TerrainSaveSystem saver)
        {
            editor = controller;
            saveSystem = saver;
            uiFont = ResolveFont();
            EnsureEventSystem();
            BuildCanvas();
        }

        private void BuildCanvas()
        {
            GameObject canvasObject = new GameObject("TerrainStudioCanvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            canvasObject.transform.SetParent(transform, false);
            Canvas canvas = canvasObject.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            CanvasScaler scaler = canvasObject.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;

            RectTransform top = CreatePanel(canvasObject.transform, "TopBar", new Vector2(0f, 0.915f), new Vector2(1f, 1f));
            CreateText(top, "Terrain Studio • Unity 6", 34, TextAnchor.MiddleLeft, new Vector2(0.02f, 0f), new Vector2(0.32f, 1f));
            statusText = CreateText(top, "جاهز", 28, TextAnchor.MiddleCenter, new Vector2(0.34f, 0f), new Vector2(0.64f, 1f));
            CreateButton(top, "جديد", new Vector2(0.66f, 0.12f), new Vector2(0.76f, 0.88f), () => { editor.NewMap(); SetStatus("خريطة جديدة"); });
            CreateButton(top, "حفظ", new Vector2(0.77f, 0.12f), new Vector2(0.87f, 0.88f), () => SetStatus(saveSystem.Save() ? "تم الحفظ" : "تعذر الحفظ"));
            CreateButton(top, "فتح", new Vector2(0.88f, 0.12f), new Vector2(0.98f, 0.88f), () => SetStatus(saveSystem.Load() ? "تم الفتح" : "لا توجد خريطة محفوظة"));

            RectTransform tools = CreatePanel(canvasObject.transform, "BottomTools", new Vector2(0f, 0f), new Vector2(1f, 0.14f));
            string[] labels = { "كاميرا", "رفع", "خفض", "تنعيم", "تسطيح", "طلاء", "شجرة", "صخرة", "حذف", "تراجع" };
            TerrainTool[] modes = { TerrainTool.Camera, TerrainTool.Raise, TerrainTool.Lower, TerrainTool.Smooth, TerrainTool.Flatten, TerrainTool.Paint, TerrainTool.Tree, TerrainTool.Rock, TerrainTool.Erase };
            float gap = 0.006f;
            float width = 0.092f;
            for (int i = 0; i < 9; i++)
            {
                int index = i;
                float x0 = 0.01f + i * (width + gap);
                CreateButton(tools, labels[i], new Vector2(x0, 0.12f), new Vector2(x0 + width, 0.88f), () =>
                {
                    editor.SetTool(modes[index]);
                    SetStatus("الأداة: " + labels[index]);
                });
            }
            CreateButton(tools, labels[9], new Vector2(0.895f, 0.12f), new Vector2(0.985f, 0.88f), () => { editor.Undo(); SetStatus("تراجع"); });

            RectTransform settings = CreatePanel(canvasObject.transform, "Settings", new Vector2(0.01f, 0.17f), new Vector2(0.245f, 0.53f));
            CreateText(settings, "إعدادات الفرشاة", 28, TextAnchor.MiddleCenter, new Vector2(0.05f, 0.78f), new Vector2(0.95f, 0.98f));
            CreateText(settings, "الحجم", 24, TextAnchor.MiddleRight, new Vector2(0.06f, 0.59f), new Vector2(0.31f, 0.75f));
            radiusSlider = CreateSlider(settings, new Vector2(0.34f, 0.60f), new Vector2(0.94f, 0.72f), 0.8f, 8f, editor.BrushRadius, editor.SetBrushRadius);
            CreateText(settings, "القوة", 24, TextAnchor.MiddleRight, new Vector2(0.06f, 0.40f), new Vector2(0.31f, 0.56f));
            strengthSlider = CreateSlider(settings, new Vector2(0.34f, 0.41f), new Vector2(0.94f, 0.53f), 0.15f, 2.5f, editor.BrushStrength, editor.SetBrushStrength);
            CreateText(settings, "لون الأرض", 24, TextAnchor.MiddleRight, new Vector2(0.06f, 0.19f), new Vector2(0.31f, 0.35f));
            CreateColorButton(settings, new Color(0.22f, 0.48f, 0.17f), new Vector2(0.36f, 0.18f), new Vector2(0.49f, 0.34f));
            CreateColorButton(settings, new Color(0.44f, 0.29f, 0.16f), new Vector2(0.52f, 0.18f), new Vector2(0.65f, 0.34f));
            CreateColorButton(settings, new Color(0.73f, 0.62f, 0.36f), new Vector2(0.68f, 0.18f), new Vector2(0.81f, 0.34f));
            CreateColorButton(settings, new Color(0.35f, 0.37f, 0.39f), new Vector2(0.84f, 0.18f), new Vector2(0.97f, 0.34f));
            CreateText(settings, "إصبع واحد للأداة • إصبعان للكاميرا", 19, TextAnchor.MiddleCenter, new Vector2(0.04f, 0.01f), new Vector2(0.96f, 0.14f));
        }

        private Font ResolveFont()
        {
            try
            {
                string[] candidates = { "Noto Naskh Arabic", "Noto Sans Arabic", "Droid Arabic Naskh", "Arial" };
                return Font.CreateDynamicFontFromOSFont(candidates, 32);
            }
            catch
            {
                return Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            }
        }

        private void SetStatus(string message)
        {
            if (statusText != null) statusText.text = message;
        }

        private static void EnsureEventSystem()
        {
            if (EventSystem.current != null) return;
            new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
        }

        private RectTransform CreatePanel(Transform parent, string name, Vector2 min, Vector2 max)
        {
            GameObject go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            RectTransform rt = go.GetComponent<RectTransform>();
            rt.anchorMin = min;
            rt.anchorMax = max;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            go.GetComponent<Image>().color = PanelColor;
            return rt;
        }

        private Text CreateText(Transform parent, string value, int size, TextAnchor alignment, Vector2 min, Vector2 max)
        {
            GameObject go = new GameObject("Text", typeof(RectTransform), typeof(Text));
            go.transform.SetParent(parent, false);
            RectTransform rt = go.GetComponent<RectTransform>();
            rt.anchorMin = min;
            rt.anchorMax = max;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            Text text = go.GetComponent<Text>();
            text.font = uiFont;
            text.text = value;
            text.fontSize = size;
            text.alignment = alignment;
            text.color = Color.white;
            text.resizeTextForBestFit = false;
            return text;
        }

        private void CreateButton(Transform parent, string label, Vector2 min, Vector2 max, Action onClick)
        {
            GameObject go = new GameObject(label, typeof(RectTransform), typeof(Image), typeof(Button));
            go.transform.SetParent(parent, false);
            RectTransform rt = go.GetComponent<RectTransform>();
            rt.anchorMin = min;
            rt.anchorMax = max;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            Image image = go.GetComponent<Image>();
            image.color = ButtonColor;
            Button button = go.GetComponent<Button>();
            ColorBlock colors = button.colors;
            colors.highlightedColor = new Color(0.18f, 0.24f, 0.29f, 1f);
            colors.pressedColor = AccentColor;
            colors.selectedColor = new Color(0.14f, 0.22f, 0.22f, 1f);
            button.colors = colors;
            button.onClick.AddListener(() => onClick());
            CreateText(go.transform, label, 23, TextAnchor.MiddleCenter, Vector2.zero, Vector2.one);
        }

        private Slider CreateSlider(Transform parent, Vector2 min, Vector2 max, float low, float high, float value, Action<float> changed)
        {
            GameObject root = new GameObject("Slider", typeof(RectTransform), typeof(Slider));
            root.transform.SetParent(parent, false);
            RectTransform rt = root.GetComponent<RectTransform>();
            rt.anchorMin = min;
            rt.anchorMax = max;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;

            GameObject bg = new GameObject("Background", typeof(RectTransform), typeof(Image));
            bg.transform.SetParent(root.transform, false);
            RectTransform bgrt = bg.GetComponent<RectTransform>();
            bgrt.anchorMin = new Vector2(0f, 0.35f);
            bgrt.anchorMax = new Vector2(1f, 0.65f);
            bgrt.offsetMin = Vector2.zero;
            bgrt.offsetMax = Vector2.zero;
            bg.GetComponent<Image>().color = new Color(0.16f, 0.18f, 0.22f, 1f);

            GameObject fill = new GameObject("Fill", typeof(RectTransform), typeof(Image));
            fill.transform.SetParent(root.transform, false);
            RectTransform fillRt = fill.GetComponent<RectTransform>();
            fillRt.anchorMin = new Vector2(0f, 0.35f);
            fillRt.anchorMax = new Vector2(1f, 0.65f);
            fillRt.offsetMin = Vector2.zero;
            fillRt.offsetMax = Vector2.zero;
            fill.GetComponent<Image>().color = AccentColor;

            GameObject handle = new GameObject("Handle", typeof(RectTransform), typeof(Image));
            handle.transform.SetParent(root.transform, false);
            RectTransform handleRt = handle.GetComponent<RectTransform>();
            handleRt.sizeDelta = new Vector2(24f, 24f);
            handle.GetComponent<Image>().color = Color.white;

            Slider slider = root.GetComponent<Slider>();
            slider.minValue = low;
            slider.maxValue = high;
            slider.value = value;
            slider.fillRect = fillRt;
            slider.handleRect = handleRt;
            slider.targetGraphic = handle.GetComponent<Image>();
            slider.onValueChanged.AddListener(v => changed(v));
            return slider;
        }

        private void CreateColorButton(Transform parent, Color color, Vector2 min, Vector2 max)
        {
            GameObject go = new GameObject("Color", typeof(RectTransform), typeof(Image), typeof(Button));
            go.transform.SetParent(parent, false);
            RectTransform rt = go.GetComponent<RectTransform>();
            rt.anchorMin = min;
            rt.anchorMax = max;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            Image image = go.GetComponent<Image>();
            image.color = color;
            go.GetComponent<Button>().onClick.AddListener(() =>
            {
                editor.SetPaintColor(color);
                SetStatus("أداة الطلاء");
            });
        }
    }
}
