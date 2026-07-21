package com.godnit.arhandstudio

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.os.Bundle
import android.os.SystemClock
import android.view.MotionEvent
import android.view.Surface as AndroidSurface
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ClearAll
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.HelpOutline
import androidx.compose.material.icons.filled.PanTool
import androidx.compose.material.icons.filled.RotateLeft
import androidx.compose.material.icons.filled.RotateRight
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.google.ar.core.Anchor
import com.google.ar.core.Config
import com.google.ar.core.Frame
import com.google.ar.core.Plane
import com.google.ar.core.Session
import com.google.ar.core.TrackingState
import com.google.ar.core.exceptions.NotYetAvailableException
import io.github.sceneview.ar.ARSceneView
import io.github.sceneview.math.Position
import io.github.sceneview.math.Rotation
import io.github.sceneview.math.Scale
import io.github.sceneview.math.Size
import io.github.sceneview.rememberEngine
import io.github.sceneview.rememberMaterialLoader
import kotlin.math.max

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                MaterialTheme(
                    colorScheme = androidx.compose.material3.darkColorScheme(
                        primary = Color(0xFF65D6A6),
                        secondary = Color(0xFFF4C96B),
                        surface = Color(0xFF151B1D)
                    )
                ) {
                    AppRoot(this)
                }
            }
        }
    }
}

@Composable
private fun AppRoot(activity: Activity) {
    val context = LocalContext.current
    var granted by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        granted = it
    }
    if (granted) {
        Studio(activity)
    } else {
        PermissionPage { launcher.launch(Manifest.permission.CAMERA) }
    }
}

@Composable
private fun PermissionPage(onGrant: () -> Unit) {
    Surface(Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier.fillMaxSize().padding(28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(Icons.Default.PanTool, null, modifier = Modifier.size(80.dp))
            Spacer(Modifier.height(18.dp))
            Text("استوديو الواقع باليد", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(12.dp))
            Text("يستخدم التطبيق الكاميرا لاكتشاف الأسطح وتتبع يدك. المعالجة تتم داخل الهاتف.")
            Spacer(Modifier.height(24.dp))
            Button(onClick = onGrant) { Text("السماح بالكاميرا والبدء") }
        }
    }
}

private enum class ShapeKind(val title: String) {
    CUBE("مكعب"), SPHERE("كرة"), CYLINDER("أسطوانة"), PLATFORM("منصّة")
}

private data class PlacedObject(
    val id: Long,
    val kind: ShapeKind,
    val anchor: Anchor,
    val color: Int,
    val scale: Float = 1f,
    val rotation: Float = 0f
)

@Composable
private fun Studio(activity: Activity) {
    val context = LocalContext.current
    val engine = rememberEngine()
    val materialLoader = rememberMaterialLoader(engine)
    val materials = remember(materialLoader) {
        listOf(
            materialLoader.createColorInstance(Color(0xFF65D6A6), .15f, .28f),
            materialLoader.createColorInstance(Color(0xFFF4C96B), .2f, .32f),
            materialLoader.createColorInstance(Color(0xFF70A7FF), .1f, .3f),
            materialLoader.createColorInstance(Color(0xFFE985A8), .1f, .35f)
        )
    }

    var selectedKind by remember { mutableStateOf(ShapeKind.CUBE) }
    var placed by remember { mutableStateOf<List<PlacedObject>>(emptyList()) }
    var selectedId by remember { mutableStateOf<Long?>(null) }
    var counter by remember { mutableLongStateOf(0L) }
    var pendingTap by remember { mutableStateOf<Offset?>(null) }
    var handMode by remember { mutableStateOf(false) }
    var handState by remember { mutableStateOf(HandTrackingState()) }
    var status by remember { mutableStateOf("حرّك الهاتف ببطء حتى تظهر شبكة السطح") }
    var help by remember { mutableStateOf(true) }
    var viewWidth by remember { mutableFloatStateOf(1f) }
    var viewHeight by remember { mutableFloatStateOf(1f) }
    var lastHandMove by remember { mutableLongStateOf(0L) }

    val placedNow by rememberUpdatedState(placed)
    val selectedNow by rememberUpdatedState(selectedId)
    val handModeNow by rememberUpdatedState(handMode)

    val handController = remember {
        HandTrackingController(
            context,
            onState = { handState = it },
            onError = { status = it }
        )
    }
    DisposableEffect(handController) {
        onDispose {
            handController.close()
            placedNow.forEach { runCatching { it.anchor.detach() } }
        }
    }

    fun anchorAt(frame: Frame, x: Float, y: Float): Anchor? {
        val hit = frame.hitTest(x, y).firstOrNull { result ->
            val plane = result.trackable as? Plane
            plane != null && plane.trackingState == TrackingState.TRACKING &&
                plane.isPoseInPolygon(result.hitPose)
        } ?: return null
        return runCatching { hit.createAnchor() }.getOrNull()
    }

    fun placeOrMove(frame: Frame, x: Float, y: Float, moveId: Long? = null): Boolean {
        val newAnchor = anchorAt(frame, x, y) ?: return false
        if (moveId == null) {
            counter += 1
            val object3d = PlacedObject(
                id = counter,
                kind = selectedKind,
                anchor = newAnchor,
                color = ((counter - 1) % materials.size).toInt()
            )
            placed = placed + object3d
            selectedId = object3d.id
        } else {
            placed = placed.map {
                if (it.id == moveId) {
                    runCatching { it.anchor.detach() }
                    it.copy(anchor = newAnchor)
                } else it
            }
        }
        return true
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .onSizeChanged {
                viewWidth = it.width.coerceAtLeast(1).toFloat()
                viewHeight = it.height.coerceAtLeast(1).toFloat()
            }
    ) {
        ARSceneView(
            modifier = Modifier.fillMaxSize(),
            engine = engine,
            materialLoader = materialLoader,
            planeRenderer = true,
            depthMode = Config.DepthMode.AUTOMATIC,
            instantPlacementMode = Config.InstantPlacementMode.LOCAL_Y_UP,
            onTouchEvent = { event, _ ->
                if (event.actionMasked == MotionEvent.ACTION_UP) {
                    pendingTap = Offset(event.x, event.y)
                }
                true
            },
            onSessionUpdated = { session, frame ->
                status = when (frame.camera.trackingState) {
                    TrackingState.TRACKING -> if (handModeNow) status else "اضغط على سطح لوضع ${selectedKind.title}"
                    TrackingState.PAUSED -> "حرّك الهاتف ببطء لتحسين التتبع"
                    TrackingState.STOPPED -> "توقف تتبع الواقع المعزز"
                }

                pendingTap?.let {
                    status = if (placeOrMove(frame, it.x, it.y)) {
                        "تم وضع ${selectedKind.title}"
                    } else {
                        "لم يُكتشف سطح هنا"
                    }
                    pendingTap = null
                }

                if (handModeNow && frame.camera.trackingState == TrackingState.TRACKING) {
                    try {
                        handController.submit(
                            frame.acquireCameraImage(),
                            cameraRotation(activity, session)
                        )
                    } catch (_: NotYetAvailableException) {
                    } catch (_: Throwable) {
                    }

                    val tracked = handController.latestState.get()
                    status = when {
                        !tracked.isHandVisible -> "ضع يدك كاملة أمام الكاميرا"
                        tracked.isPinching -> "تم الإمساك؛ حرّك يدك"
                        else -> "قرّب الإبهام والسبابة للإمساك"
                    }
                    val now = SystemClock.uptimeMillis()
                    val id = selectedNow
                    if (id != null && tracked.isHandVisible && tracked.isPinching && now - lastHandMove > 125) {
                        val cursor = tracked.toViewport(viewWidth, viewHeight)
                        if (placeOrMove(frame, cursor.x, cursor.y, id)) lastHandMove = now
                    }
                }
            }
        ) {
            placed.forEach { item ->
                AnchorNode(anchor = item.anchor) {
                    Node(
                        position = Position(y = item.kind.lift),
                        rotation = Rotation(y = item.rotation),
                        scale = Scale(item.scale)
                    ) {
                        when (item.kind) {
                            ShapeKind.CUBE -> CubeNode(
                                size = Size(.18f, .18f, .18f),
                                materialInstance = materials[item.color]
                            )
                            ShapeKind.SPHERE -> SphereNode(
                                radius = .11f,
                                materialInstance = materials[item.color]
                            )
                            ShapeKind.CYLINDER -> CylinderNode(
                                radius = .08f,
                                height = .24f,
                                materialInstance = materials[item.color]
                            )
                            ShapeKind.PLATFORM -> CubeNode(
                                size = Size(.32f, .055f, .22f),
                                materialInstance = materials[item.color]
                            )
                        }
                    }
                }
            }
        }

        HandOverlay(handState, handMode, Modifier.fillMaxSize())

        StatusPanel(
            status = status,
            handMode = handMode,
            onHandMode = { handMode = it },
            onHelp = { help = true },
            modifier = Modifier.align(Alignment.TopCenter)
        )

        Controls(
            selectedKind = selectedKind,
            onKind = { selectedKind = it },
            placed = placed,
            selectedId = selectedId,
            onSelect = { selectedId = it },
            onScale = { value ->
                val id = selectedId
                if (id != null) placed = placed.map { if (it.id == id) it.copy(scale = value) else it }
            },
            onRotate = { amount ->
                val id = selectedId
                if (id != null) placed = placed.map { if (it.id == id) it.copy(rotation = it.rotation + amount) else it }
            },
            onDelete = {
                val id = selectedId
                if (id != null) {
                    placed.firstOrNull { it.id == id }?.anchor?.detach()
                    val remaining = placed.filterNot { it.id == id }
                    placed = remaining
                    selectedId = remaining.lastOrNull()?.id
                }
            },
            onClear = {
                placed.forEach { runCatching { it.anchor.detach() } }
                placed = emptyList()
                selectedId = null
            },
            modifier = Modifier.align(Alignment.BottomCenter)
        )
    }

    if (help) HelpDialog { help = false }
}

private val ShapeKind.lift: Float
    get() = when (this) {
        ShapeKind.CUBE -> .09f
        ShapeKind.SPHERE -> .11f
        ShapeKind.CYLINDER -> .12f
        ShapeKind.PLATFORM -> .0275f
    }

@Composable
private fun StatusPanel(
    status: String,
    handMode: Boolean,
    onHandMode: (Boolean) -> Unit,
    onHelp: () -> Unit,
    modifier: Modifier
) {
    Card(
        modifier = modifier.statusBarsPadding().padding(10.dp).fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xE01A2224)),
        shape = RoundedCornerShape(18.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                modifier = Modifier.size(10.dp),
                shape = CircleShape,
                color = if (handMode) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.secondary
            ) {}
            Text(status, modifier = Modifier.weight(1f).padding(horizontal = 10.dp))
            IconButton(onClick = onHelp) { Icon(Icons.Default.HelpOutline, "مساعدة") }
        }
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(Icons.Default.PanTool, null)
            Text("التحكم باليد", modifier = Modifier.weight(1f).padding(horizontal = 8.dp))
            Switch(checked = handMode, onCheckedChange = onHandMode)
        }
    }
}

@Composable
private fun Controls(
    selectedKind: ShapeKind,
    onKind: (ShapeKind) -> Unit,
    placed: List<PlacedObject>,
    selectedId: Long?,
    onSelect: (Long) -> Unit,
    onScale: (Float) -> Unit,
    onRotate: (Float) -> Unit,
    onDelete: () -> Unit,
    onClear: () -> Unit,
    modifier: Modifier
) {
    val selected = placed.firstOrNull { it.id == selectedId }
    Card(
        modifier = modifier.fillMaxWidth().navigationBarsPadding().padding(10.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xEE151B1D)),
        shape = RoundedCornerShape(20.dp)
    ) {
        Column(Modifier.padding(10.dp)) {
            Row(
                modifier = Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(7.dp)
            ) {
                ShapeKind.entries.forEach { kind ->
                    if (kind == selectedKind) {
                        Button(onClick = { onKind(kind) }) { Text(kind.title) }
                    } else {
                        TextButton(onClick = { onKind(kind) }) { Text(kind.title) }
                    }
                }
            }
            if (placed.isNotEmpty()) {
                Row(
                    modifier = Modifier.horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(5.dp)
                ) {
                    placed.forEach { item ->
                        TextButton(onClick = { onSelect(item.id) }) {
                            Text(if (item.id == selectedId) "● ${item.kind.title} ${item.id}" else "${item.kind.title} ${item.id}")
                        }
                    }
                }
            }
            if (selected != null) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("الحجم")
                    Slider(
                        value = selected.scale,
                        onValueChange = onScale,
                        valueRange = .45f..2.3f,
                        modifier = Modifier.weight(1f).padding(horizontal = 7.dp)
                    )
                    FilledIconButton(onClick = { onRotate(-15f) }) {
                        Icon(Icons.Default.RotateRight, "يمين")
                    }
                    FilledIconButton(onClick = { onRotate(15f) }) {
                        Icon(Icons.Default.RotateLeft, "يسار")
                    }
                    IconButton(onClick = onDelete) {
                        Icon(Icons.Default.Delete, "حذف", tint = Color(0xFFFF8B8B))
                    }
                    IconButton(onClick = onClear) {
                        Icon(Icons.Default.ClearAll, "مسح الكل")
                    }
                }
            }
        }
    }
}

@Composable
private fun HandOverlay(state: HandTrackingState, visible: Boolean, modifier: Modifier) {
    if (!visible || !state.isHandVisible) return
    val connections = remember {
        listOf(
            0 to 1, 1 to 2, 2 to 3, 3 to 4, 0 to 5, 5 to 6, 6 to 7, 7 to 8,
            5 to 9, 9 to 10, 10 to 11, 11 to 12, 9 to 13, 13 to 14, 14 to 15,
            15 to 16, 13 to 17, 17 to 18, 18 to 19, 19 to 20, 0 to 17
        )
    }
    Canvas(modifier) {
        fun p(index: Int) = state.toViewport(size.width, size.height, index)
        connections.forEach { (a, b) ->
            if (a < state.landmarks.size && b < state.landmarks.size) {
                drawLine(Color(0xCC65D6A6), p(a), p(b), 4f, cap = StrokeCap.Round)
            }
        }
        state.landmarks.indices.forEach { drawCircle(Color.White, 4.5f, p(it)) }
        drawCircle(
            if (state.isPinching) Color(0xFFF4C96B) else Color(0xFF65D6A6),
            if (state.isPinching) 28f else 19f,
            state.toViewport(size.width, size.height),
            style = Stroke(6f)
        )
    }
}

private fun HandTrackingState.toViewport(width: Float, height: Float, index: Int? = null): Offset {
    val point = index?.let { landmarks.getOrNull(it) }
    val x = point?.x ?: cursorX
    val y = point?.y ?: cursorY
    val sourceWidth = imageWidth.coerceAtLeast(1).toFloat()
    val sourceHeight = imageHeight.coerceAtLeast(1).toFloat()
    val scale = max(width / sourceWidth, height / sourceHeight)
    val renderedWidth = sourceWidth * scale
    val renderedHeight = sourceHeight * scale
    return Offset(
        (x * renderedWidth - (renderedWidth - width) / 2f).coerceIn(0f, width),
        (y * renderedHeight - (renderedHeight - height) / 2f).coerceIn(0f, height)
    )
}

private fun cameraRotation(activity: Activity, session: Session): Int = runCatching {
    val manager = activity.getSystemService(CameraManager::class.java)
    val sensor = manager.getCameraCharacteristics(session.cameraConfig.cameraId)
        .get(CameraCharacteristics.SENSOR_ORIENTATION) ?: 90
    val display = when (activity.windowManager.defaultDisplay.rotation) {
        AndroidSurface.ROTATION_90 -> 90
        AndroidSurface.ROTATION_180 -> 180
        AndroidSurface.ROTATION_270 -> 270
        else -> 0
    }
    (sensor - display + 360) % 360
}.getOrDefault(90)

@Composable
private fun HelpDialog(onClose: () -> Unit) {
    AlertDialog(
        onDismissRequest = onClose,
        title = { Text("طريقة الاستخدام") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("١. حرّك الهاتف ببطء حتى تظهر شبكة السطح.")
                Text("٢. اختر مجسماً واضغط على الأرض أو الطاولة.")
                Text("٣. اختر المجسم من القائمة لتكبيره أو تدويره أو حذفه.")
                Text("٤. فعّل التحكم باليد، ثم قرّب الإبهام والسبابة وحرك يدك.")
                Text("الإضاءة الجيدة وظهور اليد كاملة يحسنان الدقة.")
            }
        },
        confirmButton = { TextButton(onClick = onClose) { Text("ابدأ") } }
    )
}
