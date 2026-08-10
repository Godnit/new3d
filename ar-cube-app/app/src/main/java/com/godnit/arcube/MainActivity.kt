package com.godnit.arcube

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.google.ar.core.ArCoreApk
import io.github.sceneview.ar.PlacementController
import io.github.sceneview.ar.PlacementScene
import io.github.sceneview.rememberEngine
import io.github.sceneview.rememberMaterialLoader
import io.github.sceneview.rememberModelInstance
import io.github.sceneview.rememberModelLoader

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                ARCubeGate()
            }
        }
    }
}

@Composable
private fun ARCubeGate() {
    val context = LocalContext.current
    var availability by remember { mutableStateOf<ArCoreApk.Availability?>(null) }

    LaunchedEffect(Unit) {
        ArCoreApk.getInstance().checkAvailabilityAsync(context) {
            availability = it
        }
    }

    when {
        availability == null -> StatusScreen("جارِ التحقق من دعم الواقع المعزز…")
        availability!!.isUnsupported -> StatusScreen(
            "هذا الهاتف غير معتمد من ARCore.\n" +
                "جرّب الـAPK على هاتف يدعم Google Play Services for AR."
        )
        availability!!.isUnknown -> StatusScreen(
            "تعذر التأكد من دعم ARCore الآن.\n" +
                "تأكد من الإنترنت وخدمات Google Play ثم افتح التطبيق من جديد."
        )
        else -> ARCubeScreen()
    }
}

@Composable
private fun ARCubeScreen() {
    val engine = rememberEngine()
    val modelLoader = rememberModelLoader(engine)
    val materialLoader = rememberMaterialLoader(engine)
    var controller by remember { mutableStateOf<PlacementController?>(null) }

    Box(modifier = Modifier.fillMaxSize()) {
        PlacementScene(
            modifier = Modifier.fillMaxSize(),
            engine = engine,
            modelLoader = modelLoader,
            materialLoader = materialLoader,
            coaching = true,
            groundShadows = true,
            instantPlacement = true,
            onPlaced = { anchor ->
                AnchorNode(anchor = anchor) {
                    val cube = rememberModelInstance(modelLoader, "models/cube.glb")
                    cube?.let {
                        ModelNode(
                            modelInstance = it,
                            scaleToUnits = 0.18f,
                        )
                    }
                }
            },
            content = { liveController ->
                controller = liveController
            },
        )

        Surface(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .fillMaxWidth()
                .padding(12.dp),
            color = Color.Black.copy(alpha = 0.68f),
            shape = RoundedCornerShape(16.dp),
        ) {
            Text(
                text = if ((controller?.count ?: 0) == 0) {
                    "حرّك الهاتف ببطء حتى يظهر السطح، ثم وجّه الحلقة واضغط لوضع المكعب."
                } else {
                    "المكعب مثبت في المكان. امشِ حوله وشاهده من الجهات المختلفة."
                },
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                textAlign = TextAlign.Center,
                color = Color.White,
            )
        }

        Button(
            onClick = { controller?.clear() },
            enabled = (controller?.count ?: 0) > 0,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 28.dp),
        ) {
            Text("مسح المكعبات")
        }
    }
}

@Composable
private fun StatusScreen(message: String) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0B1018)),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = "AR Cube",
                style = MaterialTheme.typography.headlineMedium,
                color = Color.White,
            )
            Text(
                text = message,
                modifier = Modifier.padding(top = 14.dp),
                textAlign = TextAlign.Center,
                color = Color.White.copy(alpha = 0.86f),
            )
        }
    }
}
