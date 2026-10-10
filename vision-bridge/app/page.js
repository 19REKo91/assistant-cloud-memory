"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("جارٍ التحقق من آخر صورة...");
  const [prompt, setPrompt] = useState(
    "صف ما يظهر على الشاشة بدقة، واقرأ النص الظاهر إن أمكن. أعد وصفًا نصيًا موجزًا فقط."
  );
  const [analysis, setAnalysis] = useState("");
  const [busy, setBusy] = useState(false);

  function refreshLatest() {
    setUrl("/api/latest?ts=" + Date.now());
    setStatus("جارٍ تحميل آخر صورة...");
  }

  async function upload() {
    if (!file || busy) return;
    setBusy(true);
    setStatus("جارٍ رفع الصورة...");
    setAnalysis("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/api/upload", {
        method: "POST",
        body: form,
        cache: "no-store"
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "تعذّر رفع الصورة");
      setStatus("تم رفع الصورة بنجاح.");
      setUrl("/api/latest?ts=" + Date.now());
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "فشل رفع الصورة.");
    } finally {
      setBusy(false);
    }
  }

  async function analyzeLatest() {
    if (busy) return;
    setBusy(true);
    setStatus("جارٍ تحليل آخر صورة عبر جسر الرؤيا...");
    setAnalysis("");
    try {
      const res = await fetch("/api/vision", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ prompt })
      });
      const data = await res.json();
      if (!res.ok || data.error) {
        const messages = {
          no_frame_yet: "لا توجد صورة محفوظة بعد. ارفع صورة أو التقطها أولًا.",
          GEMINI_API_KEY_not_configured: "مفتاح Gemini غير مضبوط على Worker.",
          unauthorized: "رفض Worker الطلب بسبب التحقق من الصلاحية.",
          image_fetch_failed: "تعذّر على Worker جلب الصورة المحفوظة.",
          gemini_error: "أعاد Gemini خطأ أثناء التحليل."
        };
        throw new Error(messages[data.error] || data.detail || data.error || "فشل تحليل الصورة.");
      }
      setAnalysis(data.text || "لم يُرجع نموذج الرؤية وصفًا نصيًا.");
      setStatus("اكتمل تحليل الصورة.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "تعذّر تحليل الصورة.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    refreshLatest();
  }, []);

  return (
    <main dir="rtl" style={{ padding: 24, fontFamily: "system-ui, sans-serif", maxWidth: 760, margin: "0 auto", lineHeight: 1.8 }}>
      <h1>جسر الرؤيا</h1>
      <p>رفع صورة الشاشة أو عرض آخر صورة محفوظة، ثم طلب وصف نصي منها.</p>

      <section style={{ border: "1px solid #8886", borderRadius: 12, padding: 16, marginTop: 16 }}>
        <label htmlFor="frame-file">اختر صورة من الجهاز</label>
        <input
          id="frame-file"
          type="file"
          accept="image/*"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
          style={{ display: "block", margin: "10px 0", maxWidth: "100%" }}
        />
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          <button onClick={upload} disabled={!file || busy}>رفع الصورة</button>
          <button onClick={refreshLatest} disabled={busy}>تحديث آخر صورة</button>
        </div>
      </section>

      <section style={{ border: "1px solid #8886", borderRadius: 12, padding: 16, marginTop: 16 }}>
        <h2 style={{ fontSize: 20 }}>تحليل الصورة</h2>
        <label htmlFor="vision-prompt">ما الذي تريد من النموذج فحصه؟</label>
        <textarea
          id="vision-prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          rows={3}
          style={{ display: "block", width: "100%", boxSizing: "border-box", padding: 10, margin: "8px 0 12px", font: "inherit" }}
        />
        <button onClick={analyzeLatest} disabled={busy}>
          {busy ? "جارٍ العمل..." : "حلّل آخر صورة"}
        </button>
        <p role="status" aria-live="polite">{status}</p>
        {analysis && (
          <div style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", borderTop: "1px solid #8886", paddingTop: 12 }}>
            <strong>نتيجة التحليل</strong>
            <p>{analysis}</p>
          </div>
        )}
      </section>

      <section style={{ marginTop: 20 }}>
        <h2 style={{ fontSize: 20 }}>آخر صورة</h2>
        {url ? (
          <img
            src={url}
            alt="آخر صورة محفوظة"
            onLoad={() => setStatus((current) => current === "جارٍ تحميل آخر صورة..." ? "تم تحميل آخر صورة." : current)}
            onError={() => {
              setUrl("");
              setStatus("لا توجد صورة محفوظة بعد. ارفع صورة أولًا.");
            }}
            style={{ display: "block", maxWidth: "100%", height: "auto", borderRadius: 10 }}
          />
        ) : (
          <p>لا توجد صورة معروضة حاليًا.</p>
        )}
      </section>
    </main>
  );
}
