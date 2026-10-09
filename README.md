# assistant-cloud-memory

## الغرض
ذاكرة دائمة يقرأها مساعد ذكي عبر روابط raw مباشرة.

## قواعد القراءة الآلية
- الفرع: master
- الصيغة: HTML / Markdown فقط
- ممنوع: JavaScript, fetch, AJAX, <script>
- الترميز: UTF-8
- الحجم الأقصى: 100KB لكل ملف
- المستودع: Public

## الروابط الأساسية
- الفهرس: https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/master/index.html
- آخر تحديث: https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/master/latest.md
- المحادثات: https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/master/conversations/

## بروتوكول الاستخدام
- في بداية كل جلسة: يقرأ المساعد latest.md.
- ثم يقرأ index.html لمعرفة كل المحتوى.
- ثم يقرأ ما يحتاجه من مجلد conversations/.
- بعد كل جلسة: أرفع محادثة جديدة كـ chat_NNN.md وأحدّث latest.md و index.html.
