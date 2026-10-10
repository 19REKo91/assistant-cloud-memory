# فرضية رائق — دليل الملفات وترتيب القراءة

## أولوية القراءة

**إذا كان الوقت محدودًا، اقرأ أول أربعة عناصر فقط:**
1. [نظرة عامة — Raw](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/PROJECTS/raiq/overview.md)
2. [سجل التغييرات — Raw](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/PROJECTS/raiq/changelog.md)
3. [فهرس المصادر — Raw](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/PROJECTS/raiq/source-index.md)
4. [قواعد التشغيل — Raw](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/CORE/operating-rules.md)

ثم ارجع إلى [الفهرس الرئيسي INDEX.md](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/INDEX.md) و[الجرد MANIFEST.json](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/MANIFEST.json) للتحقق من المسارات والأحجام وحالة الملفات.

## ترتيب القراءة الكامل

1. [نظرة عامة](./overview.md) — الهدف وقواعد البناء.
2. [سجل التغييرات](./changelog.md) — ما تغير ومتى.
3. [فهرس المصادر](./source-index.md) — خريطة المصادر.
4. [تدقيق المصدر 01](./source-audit-01.md) ثم [تدقيق المصدر 02](./source-audit-02.md).
5. `source-audit-complete.md` — **لم يُعثر عليه في شجرة المستودع المفحوصة بتاريخ 2026-10-11**؛ لا تعتمد عليه قبل العثور على نسخة موثوقة.
6. [إعادة ضبط الاشتقاق 01](./derivation-reset-01.md) — اقرأ على دفعات.
7. [RAEQ_MASTER.md](../../RAEQ_MASTER.md) و[RAEQ_MASTER_NEW.md](../../RAEQ_MASTER_NEW.md) — وثائق تركيبية، وليستا بديلًا عن الأصول.
8. [RAEQ_EQUATIONS_MERGED.md](../../RAEQ_EQUATIONS_MERGED.md) — مراجعة الاشتقاقات والمعادلات على دفعات.
9. [RAEQ_RAW_ARCHIVE.md](../../RAEQ_RAW_ARCHIVE.md) — الأرشيف الخام الأصلي، محفوظ كما هو؛ لا يُفترض إمكان قراءته دفعة واحدة.
10. ملفات المحادثات والمصادر الأخرى: راجع [INDEX.md](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/INDEX.md) و[MANIFEST.json](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/MANIFEST.json) بدل افتراض أن هذه القائمة شاملة.

## أحجام الملفات الكبيرة

الأحجام التالية مأخوذة من Git Trees API، وليست تقديرات بصرية. عدد الدفعات تقريبي باستخدام 100,000 بايت لكل دفعة.

| الملف | الحجم بالبايت | دفعات تقريبية |
|---|---:|---:|
| `RAEQ_RAW_ARCHIVE.md` | 1585930 | 16 |
| `derivation-reset-01.md` | 299459 | 3 |
| `RAEQ_EQUATIONS_MERGED.md` | 291950 | 3 |
| `RAEQ_MASTER.md` | 101713 | 2 |

## أين تُسجّل الملاحظات؟

استخدم [notes/DEEPSEEK_READER_NOTES.md](https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/deepseek-index-priority1-2026-10-11/notes/DEEPSEEK_READER_NOTES.md) لتسجيل ما قُرئ كاملًا أو جزئيًا، وروابط فشلت، وأرقام الأجزاء أو الأسطر، والأسئلة التي تحتاج متابعة. لا تضع استنتاجات غير مؤكدة في خانة النتائج المثبتة.

## حالة الملفات

| الملف | الحالة المسجلة | ملاحظة |
|---|---|---|
| `overview.md` | موجود | مرجعي تنظيمي |
| `changelog.md` | موجود | سجل تغييرات |
| `source-index.md` | موجود | فهرس المصادر |
| `source-audit-01.md` | موجود | وجوده لا يعني أن مضمونه نهائي |
| `source-audit-02.md` | موجود | وجوده لا يعني أن مضمونه نهائي |
| `source-audit-complete.md` | مفقود في المسار المتوقع | مسجل في MANIFEST بوصفه missing |
| `derivation-reset-01.md` | عمل قيد المراجعة | اقرأ على أجزاء؛ لا تعمم نتيجة دون فحص كامل |
| `RAEQ_MASTER.md` | وثيقة تركيبية | لا تستبدل الأرشيف الخام |
| `RAEQ_MASTER_NEW.md` | وثيقة تركيبية | قارن محتواها وسجلها قبل اعتماد أي نتيجة |
| `RAEQ_EQUATIONS_MERGED.md` | تجميع معادلات | يلزم تدقيق كل اشتقاق على حدة |
| `RAEQ_RAW_ARCHIVE.md` | أصل محفوظ | لا يُحذف ولا يُستبدل |

## قواعد علمية للعمل

- افصل الافتراضات الداخلية عن المقارنة بالفيزياء الخارجية.
- لكل نتيجة: اعرض التعريفات، الاشتقاق، مراجعة فورية، ثم اعتماد أو تصحيح.
- لا تخلط صحة المعادلة مع كفاية الافتراضات اللازمة لتفسيرها.
- عند تعذر الوصول إلى ملف، سجّل التعذر ولا تستنتج محتواه من عنوانه.
- هذا الجدول مبدئي، وليس إثباتًا أن جميع ملفات المشروع قد حُصرت.
