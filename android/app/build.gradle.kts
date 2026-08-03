import java.util.Properties
import java.io.FileInputStream

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("dev.flutter.flutter-gradle-plugin")
}
val keyProperties = Properties()
val keyPropertiesFile = rootProject.file("key.properties")
if (keyPropertiesFile.exists()) keyProperties.load(FileInputStream(keyPropertiesFile))

android {
    namespace = "com.pianoviolin.academy"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = JavaVersion.VERSION_17.toString() }
    defaultConfig { applicationId = "com.pianoviolin.academy"; minSdk = 23; targetSdk = flutter.targetSdkVersion; versionCode = flutter.versionCode; versionName = flutter.versionName }
    signingConfigs { if (keyPropertiesFile.exists()) create("release") { keyAlias = keyProperties["keyAlias"] as String; keyPassword = keyProperties["keyPassword"] as String; storeFile = file(keyProperties["storeFile"] as String); storePassword = keyProperties["storePassword"] as String } }
    buildTypes { release { signingConfig = if (keyPropertiesFile.exists()) signingConfigs.getByName("release") else signingConfigs.getByName("debug"); isMinifyEnabled = false } }
}
flutter { source = "../.." }
