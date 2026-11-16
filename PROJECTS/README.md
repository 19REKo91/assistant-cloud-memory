# فهرس المشاريع — assistant-cloud-memory

هذا الملف هو نقطة الدخول إلى المشاريع الموجودة تحت `PROJECTS/`. لا يعني وجود ملف أو إصدار هنا أنه معتمد علمياً أو نشط تنفيذياً؛ راجع وثيقة التسليم الخاصة بكل مسار.

## 1. إطار المثلث الكوني

المسار: [`PROJECTS/triangle-framework/`](./triangle-framework/)

يحتوي على:
- الإصدارات المنفصلة: 6.5.0 و6.5.1 و6.5.2 و7.0 و8.0 و9.0 و10.0، مع الاحتفاظ بكل إصدار في مساره.
- التسليمات والتعليمات: [handover](./triangle-framework/handover/).
- تدقيقات الإصدارات: [version-audits](./triangle-framework/version-audits/).
- قواعد الاختبار والتعافي والمواد التاريخية: [recovery](./triangle-framework/recovery/)، [rules](./triangle-framework/rules/)، [tests](./triangle-framework/tests/).
- الصور والمواد المفاهيمية: [images](./triangle-framework/images/)، [conceptual-notes](./triangle-framework/conceptual-notes/).

**تنبيه الإصدارات:** لا تدمج قوانين أو بيانات أو نتائج إصدار في آخر. اقرأ وثيقة الإصدار المقصود وسجل مصدر كل قيمة. بعض الملفات تاريخية أو تجريبية.

التسليم الأحدث المسجل في الشجرة:
[`10.0/handover-2026-11-16/FOUNDATIONAL_CONSTITUTION_9.0_TO_10.0.md`](./triangle-framework/10.0/handover-2026-11-16/FOUNDATIONAL_CONSTITUTION_9.0_TO_10.0.md).

## 2. قاعدة Cosmic Triangle v1.0

المسار: [`PROJECTS/cosmic-triangle-framework/v1.0/`](./cosmic-triangle-framework/v1.0/)

تسليم 2026-11-16:
- [HANDOVER_README.md](./cosmic-triangle-framework/v1.0/handover-2026-11-16/HANDOVER_README.md)
- [OPEN_ISSUES.md](./cosmic-triangle-framework/v1.0/handover-2026-11-16/OPEN_ISSUES.md)
- [SUCCESSION_INSTRUCTIONS.md](./cosmic-triangle-framework/v1.0/handover-2026-11-16/SUCCESSION_INSTRUCTIONS.md)
- [elements_118.csv](./cosmic-triangle-framework/v1.0/handover-2026-11-16/elements_118.csv)
- [elements_118_recovered_from_csv.json](./cosmic-triangle-framework/v1.0/handover-2026-11-16/elements_118_recovered_from_csv.json)
- [excluded_elements.csv](./cosmic-triangle-framework/v1.0/handover-2026-11-16/excluded_elements.csv)

**تمييز مهم:** ملف JSON المسمى recovered_from_csv إعادة بناء من CSV، وليس استعادة للنص الأصلي المفقود. يوضح الملف ذلك في بياناته الوصفية.

## 3. مضاعفة الكتلة وهندسة العناصر

المسار: [`PROJECTS/element-mass-doubling/`](./element-mass-doubling/)

يضم تقارير التدقيق، بيانات الهندسة المشتقة، ملفات SVG/HTML، خريطة العناصر، وأطلس المثلثات. تقرير المهمة الأحدث:
[REPORT_TASK_Y_MASS_DOUBLING_AND_SC_2026-11-16.md](./element-mass-doubling/task-y/REPORT_TASK_Y_MASS_DOUBLING_AND_SC_2026-11-16.md).

**الحالة:** محفوظ للأرشفة. لا يُستأنف التحليل أو التنفيذ الهندسي إلا بأمر صريح جديد.

## 4. محرك Prism

المسار: [`PROJECTS/prism-engine/`](./prism-engine/).

الإصدارات المحفوظة منفصلة: 6.3.0-beta و6.4.0-alpha وv5 وv6، مع مجلد مستقل للتشغيلات السابقة. توجد أيضاً نسخة تشغيل حديثة في جذر المستودع:
- [main.py](../main.py)
- [Run Prism Engine workflow](../.github/workflows/run.yml)

سير العمل مضبوط للتشغيل اليدوي؛ وجوده لا يعني أنه نُفّذ. لا تُسجّل نجاحاً أو مخرجات إلا من سجل GitHub Actions الفعلي.

## 5. فرضية رائق

المسار: [`PROJECTS/raiq/`](./raiq/).

ابدأ من [README.md](./raiq/README.md)، ثم overview وchangelog وsource-index. الأرشيف الخام والنسخ المشتقة للقراءة موجودة في مجلداتها. لا تستبدل الأصول بالنسخ المجمعة أو المجزأة.

## 6. أنظمة وأعمال أخرى في المستودع

- [Vision Bridge](../vision-bridge/README.md) و[`vision-bridge-android/`](../vision-bridge-android/) — التطبيق والجسر وملفات البناء.
- [CHRONO CROSS GPT](../CHRONO_CROSS_GPT_NOTEBOOK.md) — سجل المشروع ومتابعاته في ملفات الجذر، وسير العمل في `.github/workflows/`.
- [ARCHIVES](../ARCHIVES/) — مواد أرشيفية، ومنها مجموعة TAKKA_W_NOSS.

## 7. قاعدة تنظيم المستودع

1. لا تحذف أي أصل أو تستبدله لمجرد تشابه الاسم أو الحجم.
2. لا تدمج الإصدارات المختلفة ولا تنقل ملفات إصدار إلى مجلد إصدار آخر.
3. الملفات الكبيرة والمحادثات الخام تبقى محفوظة؛ أنشئ فهارس وروابط بدلاً من إعادة كتابة محتواها.
4. قبل أي نقل مادي، افحص الروابط الداخلية وسير العمل والبرامج التي تشير إلى المسار القديم.
5. الملفات غير المصنفة في جذر المستودع تبقى في مكانها مؤقتاً إلى أن يُحسم تصنيفها. هذا الفهرس يوضحها ولا يغيّر محتواها.
6. [INDEX.md](../INDEX.md) هو الفهرس العام، و[MANIFEST.json](../MANIFEST.json) هو جرد المسارات والأحجام ومعرّفات Git.
