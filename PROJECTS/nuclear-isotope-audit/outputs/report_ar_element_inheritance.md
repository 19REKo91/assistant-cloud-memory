# اختبارات الوراثة التراكمية بين العناصر — H إلى Og

## الفصل المنهجي
- اختبار فاقد الصندوق مستقل عن اختبار عيب الكتلة النووي.
- الرصيد الموروث عند Z هو مجموع الإضافات المرصودة للعناصر السابقة، ثم تضاف إضافة Z.
- لا تُستخدم فروق عنصرين متجاورين بديلاً عن الرصيد الموروث.

## اختبار فاقد الصندوق
- عدد العناصر: 118 (Z=1..118).
- مصدر الكتل: PROJECTS/triangle-framework/6.5.0/elements_input_118.csv؛ حُفظ مصدر الكتلة وجودة البيانات لكل عنصر.
- الثابت 0.016 u؛ n=floor(log2(M/0.016))، L=0.016×2^n، U=2L، d_box=U−M.
- التراكم: R_box(Z)=R_box(Z−1)+d_box(Z).
- مجموع الفاقد التراكمي عند Og: 8228.601737000012 u.

## عيب الكتلة النووي — جميع النظائر
- عدد سجلات النظائر المطابقة: 3557؛ عدد العناصر الممثلة: 118.
- عيب كل نظير محفوظ منفرداً؛ لا تُجمع نظائر العنصر الواحد في قيمة واحدة.
- عيب الكتلة مشتق من طاقة الربط المنشورة في AME2020، وليس قياساً مستقلاً عنها.

## المسارات التمثيلية الثلاثة
- most_abundant_natural: اختيار موثق لـ 84 عنصراً، وNA لـ 34؛ الرصيد الجزئي عند Og 77.408118137165 u. القاعدة: largest NUBASE2020 IS= natural abundance where published.
- most_stable: اختيار موثق لـ 80 عنصراً، وNA لـ 38؛ الرصيد الجزئي عند Og 69.409006268671 u. القاعدة: stable nuclide with highest AME2020 BE/A; abundance then lower A as tie-break.
- longest_lived_radioactive: اختيار موثق لـ 118 عنصراً، وNA لـ 0؛ الرصيد الجزئي عند Og 144.787364419608 u. القاعدة: radioactive ground-state nuclide with greatest finite NUBASE2020 half-life.

## قيد قراءة التراكم
- عند غياب نظير مؤهل لا تُخترع قيمة ولا يُستعاض عن قاعدة المسار بقاعدة أخرى؛ يحمل الرصيد الجزئي السابق ويُعلّم العنصر بأنه بلا اختيار.
- لذلك cumulative_observed_sum هو مجموع جزئي للعناصر ذات الاختيار، وليس مجموعاً كاملاً لـ118 إضافة إلا إذا كانت كلها ممثلة.
- ازدياد مجموع إضافات موجبة نتيجة حسابية للجمع؛ المهم أيضاً دراسة الإضافة الجديدة ومعدل تغيرها.
- النتائج لا تثبت قانوناً فيزيائياً عاماً أو علاقة سببية.

## الملفات الناتجة
- element_inheritance_box_loss_118.csv
- element_inheritance_nuclear_all_isotopes.csv
- element_inheritance_nuclear_track_most_abundant_natural.csv
- element_inheritance_nuclear_track_most_stable.csv
- element_inheritance_nuclear_track_longest_lived_radioactive.csv
- element_inheritance_nuclear_track_summary.csv
- report_ar_element_inheritance.md
