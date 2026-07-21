package com.godnit.arhandstudio

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Matrix
import android.graphics.Rect
import android.graphics.YuvImage
import android.media.Image
import java.io.ByteArrayOutputStream

/** Converts ARCore's YUV_420_888 CPU camera image into a rotated ARGB bitmap. */
object YuvImageConverter {
    fun toBitmap(image: Image, rotationDegrees: Int): Bitmap {
        require(image.format == ImageFormat.YUV_420_888) {
            "Unsupported camera image format: ${image.format}"
        }

        val nv21 = yuv420888ToNv21(image)
        val jpeg = ByteArrayOutputStream().use { stream ->
            val yuv = YuvImage(nv21, ImageFormat.NV21, image.width, image.height, null)
            check(yuv.compressToJpeg(Rect(0, 0, image.width, image.height), 88, stream)) {
                "Unable to encode camera frame"
            }
            stream.toByteArray()
        }

        val decoded = BitmapFactory.decodeByteArray(jpeg, 0, jpeg.size)
            ?: error("Unable to decode camera frame")

        if (rotationDegrees % 360 == 0) return decoded
        val matrix = Matrix().apply { postRotate(rotationDegrees.toFloat()) }
        return Bitmap.createBitmap(decoded, 0, 0, decoded.width, decoded.height, matrix, true)
            .also { if (it !== decoded) decoded.recycle() }
    }

    private fun yuv420888ToNv21(image: Image): ByteArray {
        val width = image.width
        val height = image.height
        val output = ByteArray(width * height + width * height / 2)

        copyPlane(
            plane = image.planes[0],
            width = width,
            height = height,
            output = output,
            outputOffset = 0,
            outputPixelStride = 1
        )

        // NV21 chroma order is interleaved VU.
        val chromaWidth = width / 2
        val chromaHeight = height / 2
        copyPlane(
            plane = image.planes[2],
            width = chromaWidth,
            height = chromaHeight,
            output = output,
            outputOffset = width * height,
            outputPixelStride = 2
        )
        copyPlane(
            plane = image.planes[1],
            width = chromaWidth,
            height = chromaHeight,
            output = output,
            outputOffset = width * height + 1,
            outputPixelStride = 2
        )
        return output
    }

    private fun copyPlane(
        plane: Image.Plane,
        width: Int,
        height: Int,
        output: ByteArray,
        outputOffset: Int,
        outputPixelStride: Int
    ) {
        val buffer = plane.buffer.duplicate()
        val rowStride = plane.rowStride
        val pixelStride = plane.pixelStride
        var outputIndex = outputOffset

        for (row in 0 until height) {
            val rowStart = row * rowStride
            for (column in 0 until width) {
                output[outputIndex] = buffer.get(rowStart + column * pixelStride)
                outputIndex += outputPixelStride
            }
        }
    }
}
