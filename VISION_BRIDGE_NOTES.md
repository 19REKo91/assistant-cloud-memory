# ChatGPT Working Notes — Vision Bridge

## Purpose
Persistent working notes for the GitHub image-to-artifact → real-file → vision workflow and the Android Vision Bridge debugging workflow. Read this file before continuing so the user does not need to repeat the setup history.

## Repository
- GitHub repository: 19REKo91/assistant-cloud-memory
- Default branch: main
- User works from an Android phone; operational links/instructions should be suitable for Chrome.
- Keep project history here; do not rely only on conversation memory.

## Proven successful Android/Bridge state
A previous test established that the overall pipeline could work: the Android screen stream was captured, the bridge accepted the frame, and a screen description was produced. Therefore do NOT assume Gemini/Worker architecture is fundamentally broken merely because a later APK fails.

Known screen-stream endpoint used in successful testing:
- http://192.168.0.197:8080

Known bridge deployment used in recent testing:
- https://chatgpt-vision-bridge.flourish-gerbil.workers.dev
- A later test URL variant returned Bridge 503 with GEMINI_API_KEY_not_configured; do not immediately change the Gemini key/config because the older APK/server path had worked.

## Android APK versions — current debugging state (2026-09-21)
There were two installed APK variants during testing.

### OLD / preferred baseline
- Keep the old APK as the baseline.
- It has the floating overlay button.
- The user reports that currently it shows only the floating button and does not visibly show what fails.
- This is the preferred codebase to modify because the overlay functionality is already present and the earlier workflow had succeeded.
- Do NOT delete or replace the old baseline until the diagnostic build proves the replacement works.

### NEW / experimental APK
- It was installed alongside the old APK.
- It had NO floating overlay button.
- Its server test produced: Bridge 503 : {"error":"GEMINI_API_KEY_not_configured"}
- User was told to delete the new APK and keep the old baseline.
- Do not use the new APK as the primary base unless explicitly requested.

## Immediate next development task
Modify the OLD Android baseline, not the new APK.

Add an on-device diagnostic/log panel so every stage is explicitly recorded when the user presses شوف الشاشة / the floating button:
1. App started
2. Overlay created/shown
3. Screen-capture permission requested/granted
4. MediaProjection / ScreenStream started
5. Frame requested/received
6. JPEG/PNG encoding succeeded and byte size
7. HTTP request started
8. Bridge URL used
9. HTTP status + response body
10. Gemini/analysis stage
11. Final result received/displayed

On failure, show the exact stage plus exception/error/status. The diagnostic UI must remain usable from the floating overlay flow.

Do NOT change the Worker/Gemini configuration first. The purpose of this diagnostic build is to identify the exact failing stage instead of guessing.

## Important architecture distinction
Repository contains more than one Android Vision Bridge project:
- vision-bridge/android/...
- vision-bridge-android/...

There are also multiple workflows:
- .github/workflows/vision-bridge-android-build.yml
- .github/workflows/build-vision-bridge-android.yml
- .github/workflows/deploy-vision-bridge.yml
- .github/workflows/gemini-vision-bridge.yml
- .github/workflows/github-to-dropbox-vision-bridge.yml

Do not accidentally modify the wrong Android project or workflow. Inspect the current baseline files before editing.

Relevant baseline files include:
- vision-bridge-android/app/src/main/java/com/raiq/visionbridge/MainActivity.kt
- vision-bridge-android/app/src/main/java/com/raiq/visionbridge/OverlayService.kt
- vision-bridge-android/app/src/main/java/com/raiq/visionbridge/CaptureService.kt
- vision-bridge-android/app/src/main/AndroidManifest.xml

The repository also contains another Android implementation:
- vision-bridge/android/app/src/main/java/com/visionbridge/android/MainActivity.kt
Treat it as a separate implementation unless verified otherwise.

## GitHub image-to-artifact workflow
The proven 18/9 method was:
1. PNG is uploaded/placed in GitHub.
2. GitHub Actions processes the image.
3. actions/upload-artifact@v4 creates an artifact.
4. Download artifact ZIP.
5. ZIP contains a real PNG.
6. Real PNG can be used for image/vision analysis.

Generic workflow:
- .github/workflows/image-to-artifact.yml
- Artifact: image-latest
- Retention: 7 days
- Do not hard-code a specific DeepSeek filename.
- Do not delete the old successful workflow/artifacts merely to simplify things.

## Operating rules
- Read this file before continuing the Vision Bridge work.
- Verify repository state before changing files.
- Preserve the old successful baseline.
- Diagnose the actual failure before changing architecture.
- Do not expose or commit API keys/secrets.
- When the user says continue, proceed from these notes without asking them to repeat the history.

## 📝 سجل التجربة — 1790001424526.jpg

**المصدر:** OneDrive  
**اسم الملف:** `1790001424526.jpg`  
**الحجم:** 111,264 بايت  
**النوع:** `image/jpeg`

**المسار الفعلي الذي حدث هذه المرة:**

**OneDrive**  
↓  
`search_drive_items` عثر على الملف  
↓  
`fetch` مع `download_raw_file=true`  
↓  
أُنشئ **File Reference** للملف  
↓  
النظام أنشأ نسخة محلية تلقائيًا في `/mnt/data/1790001424526.jpg`  
↓  
تم فتح الصورة بصريًا  
↓  
**تمكنت من رؤيتها فعليًا**

### 👁️ ما رأيته
صورة رأس حصان بني من الأمام، بلبدة طويلة متطايرة إلى اليمين، وإضاءة ذهبية/برتقالية قوية من الجهة اليمنى، مع علامة بيضاء واضحة على الجبهة وأنف فاتح اللون.

### ⚠️ الاكتشاف المهم
هذه المرة **لم تنجح كتجربة "الصورة تبقى خارج البيئة"**.

السبب واضح من نتيجة الأداة نفسها: استخدام  
`download_raw_file=true`  
حوّل الملف إلى **File Reference** ثم جرى توفيره محليًا في `/mnt/data`.

إذن أصبح لدينا الآن فرق حاسم بين المسارين:

**المسار A — الذي اختبرناه الآن:**  
OneDrive → `fetch(raw)` → File Reference → `/mnt/data` → Vision ✅ **المشاهدة مؤكدة، لكن الصورة دخلت البيئة.**

**المسار B — الذي نريد إثباته:**  
OneDrive → جلب/مرجع خارجي → Vision مباشرة **من دون `/mnt/data`**. ❓

وهذا يفسر لماذا كانت تجربتنا السابقة مهمة: **المشاهدة نفسها ممكنة، لكن علينا إعادة التجربة بدون `download_raw_file=true` حتى نعرف هل يمكن تمرير الصورة إلى Vision دون إنشاء نسخة محلية.**

سجلت هذه النتيجة كتصحيح أساسي للمسار.
