# Vision Bridge Android

نسخة أولى من جسر رؤية الشاشة.

- بدء التقاط الشاشة يطلب MediaProjection ويحفظ آخر Frame فقط.
- شوف الشاشة يرسل آخر Frame إلى Worker عبر POST /vision.
- لا تُرفق اللقطة بمحادثة ChatGPT.
- مفتاح Gemini يبقى على الخادم ولا يوضع داخل APK.

افتح مجلد vision-bridge/android في Android Studio ثم Build > Make Project.
