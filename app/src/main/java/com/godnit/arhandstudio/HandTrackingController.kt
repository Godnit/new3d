package com.godnit.arhandstudio

import android.content.Context
import android.media.Image
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.framework.image.MPImage
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerResult
import java.io.Closeable
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import kotlin.math.hypot

/**
 * Offline MediaPipe hand tracking for ARCore camera frames.
 * A pinch between thumb and index finger becomes the grab gesture.
 */
class HandTrackingController(
    context: Context,
    private val onState: (HandTrackingState) -> Unit,
    private val onError: (String) -> Unit
) : Closeable {
    private val appContext = context.applicationContext
    private val mainHandler = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor()
    private val frameInFlight = AtomicBoolean(false)
    private var lastSubmittedAt = 0L
    private var previousPinching = false

    private val handLandmarker: HandLandmarker = HandLandmarker.createFromOptions(
        appContext,
        HandLandmarker.HandLandmarkerOptions.builder()
            .setBaseOptions(
                BaseOptions.builder()
                    .setModelAssetPath("hand_landmarker.task")
                    .setDelegate(Delegate.CPU)
                    .build()
            )
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setNumHands(1)
            .setMinHandDetectionConfidence(0.55f)
            .setMinHandPresenceConfidence(0.55f)
            .setMinTrackingConfidence(0.55f)
            .setResultListener(::handleResult)
            .setErrorListener { error ->
                frameInFlight.set(false)
                mainHandler.post { onError(error.message ?: "حدث خطأ في تتبع اليد") }
            }
            .build()
    )

    private val pendingImage = AtomicReference<PendingImage?>(null)
    val latestState = AtomicReference(HandTrackingState())

    /** The controller intentionally processes at a modest rate to preserve AR frame rate. */
    fun submit(image: Image, rotationDegrees: Int, minimumIntervalMs: Long = 125L) {
        val now = SystemClock.uptimeMillis()
        if (now - lastSubmittedAt < minimumIntervalMs || !frameInFlight.compareAndSet(false, true)) {
            image.close()
            return
        }
        lastSubmittedAt = now

        worker.execute {
            try {
                val bitmap = image.use { YuvImageConverter.toBitmap(it, rotationDegrees) }
                val mpImage = BitmapImageBuilder(bitmap).build()
                pendingImage.getAndSet(PendingImage(mpImage, bitmap))?.close()
                handLandmarker.detectAsync(mpImage, now)
            } catch (t: Throwable) {
                pendingImage.getAndSet(null)?.close()
                frameInFlight.set(false)
                mainHandler.post { onError(t.message ?: "تعذر تحليل صورة الكاميرا") }
            }
        }
    }

    private fun handleResult(result: HandLandmarkerResult, input: MPImage) {
        val pending = pendingImage.getAndSet(null)
        val state = result.toTrackingState(input.width, input.height)
        latestState.set(state)
        frameInFlight.set(false)
        pending?.close()
        mainHandler.post { onState(state) }
    }

    private fun HandLandmarkerResult.toTrackingState(
        imageWidth: Int,
        imageHeight: Int
    ): HandTrackingState {
        val hand = landmarks().firstOrNull()
            ?: return HandTrackingState(imageWidth = imageWidth, imageHeight = imageHeight)

        val thumb = hand[4]
        val index = hand[8]
        val wrist = hand[0]
        val middleMcp = hand[9]

        val pinchDistance = hypot(thumb.x() - index.x(), thumb.y() - index.y())
        val palmSize = hypot(wrist.x() - middleMcp.x(), wrist.y() - middleMcp.y())
            .coerceAtLeast(0.02f)
        val ratio = pinchDistance / palmSize

        // Hysteresis prevents rapid grab/release flicker around one threshold.
        val isPinching = if (previousPinching) ratio < 0.58f else ratio < 0.42f
        previousPinching = isPinching

        val points = hand.map { HandPoint(it.x(), it.y()) }
        return HandTrackingState(
            isHandVisible = true,
            isPinching = isPinching,
            cursorX = (thumb.x() + index.x()) / 2f,
            cursorY = (thumb.y() + index.y()) / 2f,
            pinchRatio = ratio,
            landmarks = points,
            imageWidth = imageWidth,
            imageHeight = imageHeight
        )
    }

    override fun close() {
        pendingImage.getAndSet(null)?.close()
        handLandmarker.close()
        worker.shutdownNow()
    }

    private data class PendingImage(val image: MPImage, val bitmap: android.graphics.Bitmap) : Closeable {
        override fun close() {
            image.close()
            if (!bitmap.isRecycled) bitmap.recycle()
        }
    }
}

data class HandPoint(val x: Float, val y: Float)

data class HandTrackingState(
    val isHandVisible: Boolean = false,
    val isPinching: Boolean = false,
    val cursorX: Float = 0.5f,
    val cursorY: Float = 0.5f,
    val pinchRatio: Float = 1f,
    val landmarks: List<HandPoint> = emptyList(),
    val imageWidth: Int = 1,
    val imageHeight: Int = 1
)
