import java.net.URI

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.godnit.arhandstudio"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.godnit.arhandstudio"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"

        vectorDrawables {
            useSupportLibrary = true
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

val generatedAssetsDir = layout.buildDirectory.dir("generated/mediapipe-assets")
val handModelFile = generatedAssetsDir.map { it.file("hand_landmarker.task") }

val downloadHandModel by tasks.registering {
    outputs.file(handModelFile)
    doLast {
        val output = handModelFile.get().asFile
        if (!output.exists() || output.length() < 1_000_000L) {
            output.parentFile.mkdirs()
            val url = URI(
                "https://storage.googleapis.com/mediapipe-models/hand_landmarker/" +
                    "hand_landmarker/float16/latest/hand_landmarker.task"
            ).toURL()
            url.openStream().use { input ->
                output.outputStream().use { target -> input.copyTo(target) }
            }
        }
    }
}

android.sourceSets["main"].assets.srcDir(generatedAssetsDir)
tasks.named("preBuild").configure { dependsOn(downloadHandModel) }

dependencies {
    implementation(platform("androidx.compose:compose-bom:2026.06.01"))
    implementation("androidx.core:core-ktx:1.18.0")
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.10.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("io.github.sceneview:arsceneview:4.23.0")
    implementation("com.google.mediapipe:tasks-vision:0.10.26")

    debugImplementation("androidx.compose.ui:ui-tooling")
}
