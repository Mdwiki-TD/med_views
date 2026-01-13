# خطة تنفيذ نظام عرض جميع السنوات (2015-2025)
# Implementation Plan for All Years Views System (2015-2025)

## نظرة عامة / Overview
هذه الخطة لإنشاء نظام موازي للنظام الحالي يعمل على جمع وتخزين مشاهدات المقالات لجميع السنوات من 2015 إلى 2025 بدلاً من سنة واحدة فقط.

This plan creates a parallel system to the existing one that collects and stores article views for all years from 2015 to 2025 instead of just one year.

## الملفات المطلوب إنشاؤها / Files to Create

### 1. src/views_utils/views_helps.py
**التعديل / Modification:**
- إضافة دالة جديدة: `article_views_all_years(site, articles)`
- تجمع المشاهدات من 2015-01-01 إلى 2025-12-31
- تعيد البيانات بنفس تنسيق `article_views` لكن مع كل السنوات

**Add new function:**
- `article_views_all_years(site, articles)`
- Collects views from 2015-01-01 to 2025-12-31
- Returns data in same format as `article_views` but with all years

### 2. src/views_all_years.py
**نسخة من / Copy of:** `src/views.py`
**التغييرات / Changes:**
- استخدام `article_views_all_years` بدلاً من `article_views`
- تعديل `get_one_lang_views_by_titles` لاستخدام الدالة الجديدة
- لا حاجة لمعامل `year` في بعض الدوال

**Use `article_views_all_years` instead of `article_views`**
- Modify `get_one_lang_views_by_titles` to use new function
- Remove `year` parameter where not needed

### 3. start_views_all_years.py
**نسخة من / Copy of:** `start_views.py`
**التغييرات / Changes:**
- استيراد من `src.views_all_years` بدلاً من `src.views`
- تخزين البيانات في مجلد `views_by_year_path` لكل سنة على حدة
- معالجة البيانات لكل سنة وحفظها في المجلد المناسب

**Import from `src.views_all_years` instead of `src.views`**
- Store data in `views_by_year_path` for each year separately
- Process data for each year and save in appropriate folder

### 4. src/stats_bot_all_years.py
**نسخة من / Copy of:** `src/stats_bot.py`
**التغييرات / Changes:**
- إنشاء نسخة تتعامل مع البيانات متعددة السنوات
- حفظ الإحصائيات في:
  - `all_years_summary.json`
  - `all_years_stats_all.json`
- معالجة البيانات التي تحتوي على قاموس من السنوات بدلاً من قيمة واحدة

**Create version that handles multi-year data**
- Save statistics to:
  - `all_years_summary.json`
  - `all_years_stats_all.json`
- Process data containing dictionary of years instead of single value

## خطوات التنفيذ / Implementation Steps

### الخطوة 1: إضافة دالة article_views_all_years
- [ ] إضافة الدالة الجديدة في `src/views_utils/views_helps.py`
- [ ] التأكد من أن الدالة تستخدم نفس المنطق مع تواريخ 2015-2025
- [ ] إضافة الدالة إلى `__all__` للتصدير

**Step 1: Add article_views_all_years function**
- [ ] Add new function to `src/views_utils/views_helps.py`
- [ ] Ensure function uses same logic with 2015-2025 dates
- [ ] Add function to `__all__` for export

### الخطوة 2: إنشاء src/views_all_years.py
- [ ] نسخ `src/views.py` إلى `src/views_all_years.py`
- [ ] استبدال استيراد `article_views` بـ `article_views_all_years`
- [ ] تعديل دالة `get_one_lang_views_by_titles` لإزالة معامل `year` وتمريره إلى الدالة الجديدة
- [ ] تعديل دالة `load_one_lang_views` إذا لزم الأمر
- [ ] تعديل دالة `get_one_lang_views` لإزالة معامل `year` حيث لا يحتاج

**Step 2: Create src/views_all_years.py**
- [ ] Copy `src/views.py` to `src/views_all_years.py`
- [ ] Replace `article_views` import with `article_views_all_years`
- [ ] Modify `get_one_lang_views_by_titles` to remove `year` parameter
- [ ] Modify `load_one_lang_views` if needed
- [ ] Modify `get_one_lang_views` to remove `year` parameter where not needed

### الخطوة 3: إنشاء src/stats_bot_all_years.py
- [ ] نسخ `src/stats_bot.py` إلى `src/stats_bot_all_years.py`
- [ ] تعديل دالة `dump_stats` للتعامل مع بيانات متعددة السنوات
- [ ] تعديل دالة `dump_stats_all` لحفظ البيانات في:
  - `all_years_summary.json`
  - `all_years_stats_all.json`
- [ ] التأكد من حساب المجاميع بشكل صحيح للبيانات متعددة السنوات

**Step 3: Create src/stats_bot_all_years.py**
- [ ] Copy `src/stats_bot.py` to `src/stats_bot_all_years.py`
- [ ] Modify `dump_stats` to handle multi-year data
- [ ] Modify `dump_stats_all` to save data to:
  - `all_years_summary.json`
  - `all_years_stats_all.json`
- [ ] Ensure totals are calculated correctly for multi-year data

### الخطوة 4: إنشاء start_views_all_years.py
- [ ] نسخ `start_views.py` إلى `start_views_all_years.py`
- [ ] استبدال استيراد من `src.views` إلى `src.views_all_years`
- [ ] استبدال استيراد من `src.stats_bot` إلى `src.stats_bot_all_years`
- [ ] تعديل دالة `dump_one_lang_files` لمعالجة البيانات متعددة السنوات
- [ ] تعديل دالة `dump_one_lang_files` لحفظ كل سنة في المجلد المناسب
- [ ] تعديل دالة `process_language_views` لإزالة معامل `year` عند استدعاء الدوال الجديدة
- [ ] إزالة معامل `year` من دالة `make_views` وتعديل استدعاءاتها
- [ ] تعديل دالة `start` لإزالة معامل `year`

**Step 4: Create start_views_all_years.py**
- [ ] Copy `start_views.py` to `start_views_all_years.py`
- [ ] Replace import from `src.views` to `src.views_all_years`
- [ ] Replace import from `src.stats_bot` to `src.stats_bot_all_years`
- [ ] Modify `dump_one_lang_files` to process multi-year data
- [ ] Modify `dump_one_lang_files` to save each year in appropriate folder
- [ ] Modify `process_language_views` to remove `year` parameter
- [ ] Remove `year` parameter from `make_views` and modify calls
- [ ] Modify `start` to remove `year` parameter

### الخطوة 5: الاختبار والتحقق
- [ ] التحقق من أن جميع الملفات تم إنشاؤها بشكل صحيح
- [ ] التحقق من أن الاستيرادات تعمل بشكل صحيح
- [ ] اختبار البرنامج مع عينة صغيرة من البيانات
- [ ] التحقق من حفظ الملفات في المجلدات الصحيحة

**Step 5: Testing and Verification**
- [ ] Verify all files are created correctly
- [ ] Verify imports work correctly
- [ ] Test program with small sample of data
- [ ] Verify files are saved in correct folders

## ملاحظات مهمة / Important Notes

1. **الفرق الرئيسي / Main Difference:**
   - النظام الحالي: يعمل على سنة واحدة فقط (2024 أو 2025)
   - النظام الجديد: يعمل على جميع السنوات (2015-2025)

2. **هيكل البيانات / Data Structure:**
   - النظام الحالي: `{title: views_count}`
   - النظام الجديد: `{title: {2015: count, 2016: count, ...}}`

3. **التخزين / Storage:**
   - يجب تخزين كل سنة في مجلد منفصل داخل `views_by_year_path`
   - مثل النظام الحالي الذي يخزن سنة 2025

4. **الإحصائيات / Statistics:**
   - يجب حساب مجموع المشاهدات عبر جميع السنوات
   - حفظ الإحصائيات في ملفات منفصلة لتجنب الخلط مع إحصائيات السنة الواحدة

## التبعيات / Dependencies
- لا حاجة لتثبيت مكتبات جديدة
- يستخدم نفس التبعيات الموجودة في المشروع
