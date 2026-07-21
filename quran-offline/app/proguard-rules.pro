# WebView application. Keep JavaScript bridge methods if added later.
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
