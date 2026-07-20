# رفيق الهدى — مشروع Android المستعاد

هذه النسخة محفوظة خصيصًا حتى يمكن مواصلة تطوير تطبيق **رفيق الهدى** دون الاعتماد على ملف APK فقط.

## حالة المشروع

- التطبيق: رفيق الهدى
- التقنية: Android Java + WebView + HTML/CSS/JavaScript محلي
- الحزمة: `com.mastermedia.quranoffline`
- المصدر المستعاد: فرع `agent/rafiq-alhuda-official-v4`
- فرع النسخة الاحتياطية: `backup/rafiq-alhuda-v4.7-recovered`
- قارئ القرآن: 604 صفحات مصحف تُجهّز أثناء البناء
- المحتوى: قرآن، أحاديث، أذكار، مواقيت الصلاة، القبلة، المفضلة، الملاحظات والبحث
- الصوت المخطط: تلاوة ياسر الدوسري لـ 114 سورة بصيغة Ogg/Opus تعمل دون إنترنت

## بنية المشروع

```text
quran-offline/
├── app/
│   ├── build.gradle
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/mastermedia/quranoffline/
│       │   ├── MainActivity.java
│       │   ├── AudioService.java
│       │   ├── PrayerScheduler.java
│       │   ├── PrayerAlarmReceiver.java
│       │   └── BootReceiver.java
│       ├── assets/
│       │   ├── index.html
│       │   ├── app-v*.js
│       │   ├── app-v*.css
│       │   └── ملفات المصحف والصوت التي تُجهّز أثناء البناء
│       └── res/
├── scripts/
├── build.gradle
├── gradle.properties
└── settings.gradle
```

## البناء محليًا

يتطلب المشروع Java 17 وAndroid SDK 35 وGradle 8.9.

```bash
cd quran-offline
gradle :app:assembleRelease --stacktrace
```

ملف APK غير الموقّع يظهر عادة هنا:

```text
quran-offline/app/build/outputs/apk/release/app-release-unsigned.apk
```

## البناء عبر GitHub Actions

الملف الرئيسي:

```text
.github/workflows/quran-apk.yml
```

هو المسؤول عن تنزيل وتجهيز:

1. صفحات المصحف الـ604.
2. بيانات القرآن والحديث.
3. خط المصحف.
4. الأذان.
5. تلاوة السور الـ114 وضغطها إلى Ogg/Opus.
6. بناء APK ورفعه كـ Artifact.

## مهم جدًا: مفتاح التوقيع

لا ترفع مفتاح توقيع التطبيق إلى GitHub، خصوصًا أن المستودع عام. احتفظ به في مكان خاص. يلزم استخدام المفتاح نفسه حتى تُثبت النسخ الجديدة كتحديث فوق النسخة القديمة.

## الخطوة التالية

الهدف الأول هو إصلاح فشل Workflow الخاص بالإصدار v4.7، ثم إنتاج APK اختباري غير موقّع، وبعد اختباره يُوقّع محليًا بالمفتاح الرسمي المحفوظ خارج GitHub.
