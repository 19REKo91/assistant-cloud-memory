# إعداد المحادثة الصفراء

هذه الصفحة تستخدم Worker الموجود `chatgpt-vision-bridge` على Cloudflare، ولا تحتاج إلى `OPENAI_API_KEY`.

## ما يلزم قبل تشغيل الردود الحقيقية

### 1. تأكد من أسرار Cloudflare
من Cloudflare Dashboard افتح **Workers & Pages** ثم Worker باسم **chatgpt-vision-bridge** ثم **Settings → Variables and Secrets**.

- يجب أن يكون `GEMINI_API_KEY` مضبوطًا كـ Secret. لا تنسخه إلى GitHub أو الصفحة.
- أضف Secret جديدًا باسم `BRIDGE_TOKEN`، وأنشئ قيمة قوية وفريدة له. لا تضعها في الكود أو في مستودع GitHub.

### 2. ضع القيمة نفسها في Vercel
افتح مشروع Vercel **assistant-cloud-memory → Settings → Environment Variables**.

- أضف `YELLOW_CHAT_ACCESS_TOKEN` مع **القيمة نفسها تمامًا** التي وضعتها في `BRIDGE_TOKEN`.
- فعّلها لبيئتي **Production** و**Preview** حسب الحاجة.
- لا تحتاج إلى `OPENAI_API_KEY` لهذه الميزة.

بعد تغيير متغيرات Vercel، أعد نشر المشروع لكي تستخدمه النسخة الجديدة. بعد إضافة أو تغيير أسرار Worker، تأكد أن إعدادات Worker محفوظة.

### 3. افتح المحادثة
افتح:
https://assistant-cloud-memory.vercel.app/yellow-chat

أدخل قيمة `YELLOW_CHAT_ACCESS_TOKEN` نفسها في خانة رمز الوصول. تتحول الحالة إلى «الإعداد موجود» عندما يؤكد فحص الجاهزية وجود الأسرار المطلوبة على الخادم وWorker.

## ملاحظات أمان
- لا ترسل `GEMINI_API_KEY` أو `BRIDGE_TOKEN` أو `YELLOW_CHAT_ACCESS_TOKEN` في هذه المحادثة أو في GitHub.
- إذا ظهر «رمز الحماية في Cloudflare لا يطابق الرمز المحفوظ في Vercel»، فتأكد أن القيمتين متطابقتان حرفيًا.
- يفحص مسار الجاهزية وجود الإعدادات فقط؛ نجاح الرد الفعلي يتطلب أن يكون مفتاح Gemini صالحًا ومسموحًا له باستخدام النموذج.
- حدود الطلبات داخل واجهة Vercel تخفيف أولي وليست نظام تحديد معدل موزعًا بالكامل.
