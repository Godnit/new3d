using UnityEngine;
using UnityEngine.EventSystems;

namespace TerrainStudio
{
    public sealed class OrbitTouchCamera : MonoBehaviour
    {
        public Vector3 target = Vector3.zero;
        public float distance = 34f;
        public float yaw = 38f;
        public float pitch = 52f;
        public float minDistance = 8f;
        public float maxDistance = 70f;

        private float targetDistance;
        private float targetYaw;
        private float targetPitch;
        private float previousPinch;
        private Vector2 previousCenter;
        private bool hadTwoTouches;

        private void Awake()
        {
            targetDistance = distance;
            targetYaw = yaw;
            targetPitch = pitch;
        }

        private void Update()
        {
            HandleTouchCamera();
            yaw = Mathf.LerpAngle(yaw, targetYaw, 1f - Mathf.Exp(-12f * Time.unscaledDeltaTime));
            pitch = Mathf.Lerp(pitch, targetPitch, 1f - Mathf.Exp(-12f * Time.unscaledDeltaTime));
            distance = Mathf.Lerp(distance, targetDistance, 1f - Mathf.Exp(-12f * Time.unscaledDeltaTime));
            ApplyTransform();
        }

        private void HandleTouchCamera()
        {
            if (Input.touchCount < 2)
            {
                hadTwoTouches = false;
                return;
            }

            Touch a = Input.GetTouch(0);
            Touch b = Input.GetTouch(1);
            if ((EventSystem.current != null && EventSystem.current.IsPointerOverGameObject(a.fingerId)) ||
                (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject(b.fingerId)))
                return;

            Vector2 center = (a.position + b.position) * 0.5f;
            float pinch = Vector2.Distance(a.position, b.position);

            if (!hadTwoTouches)
            {
                previousPinch = pinch;
                previousCenter = center;
                hadTwoTouches = true;
                return;
            }

            Vector2 centerDelta = center - previousCenter;
            float pinchDelta = pinch - previousPinch;

            targetYaw += centerDelta.x * 0.11f;
            targetPitch = Mathf.Clamp(targetPitch - centerDelta.y * 0.08f, 18f, 78f);
            targetDistance = Mathf.Clamp(targetDistance - pinchDelta * 0.025f, minDistance, maxDistance);

            previousPinch = pinch;
            previousCenter = center;
        }

        public void Orbit(float deltaYaw, float deltaPitch)
        {
            targetYaw += deltaYaw;
            targetPitch = Mathf.Clamp(targetPitch + deltaPitch, 18f, 78f);
        }

        public void Zoom(float amount)
        {
            targetDistance = Mathf.Clamp(targetDistance + amount, minDistance, maxDistance);
        }

        private void ApplyTransform()
        {
            Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
            Vector3 offset = rotation * new Vector3(0f, 0f, -distance);
            transform.position = target + offset;
            transform.rotation = Quaternion.LookRotation(target - transform.position, Vector3.up);
        }
    }
}
