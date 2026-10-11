"use client";

import { useEffect, useState } from "react";

const OUTGOING_MESSAGE =
  "https://raw.githubusercontent.com/19REKo91/assistant-cloud-memory/main/SYNC/CHATGPT_TO_DEEPSEEK.md";

export default function RelayPage() {
  const [configured, setConfigured] = useState(null);
  const [reply, setReply] = useState("");
  const [writeKey, setWriteKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("جارٍ فحص إعدادات الحفظ...");
  const [savedUrl, setSavedUrl] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetch("/api/sync", { cache: "no-store" })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok || data.error) throw new Error(data.error || "تعذّر فحص الإعدادات.");
        if (!cancelled) {
          setConfigured(data.configured === true);
          setStatus(
            data.configured
              ? "مسار الحفظ مُعدّ. أدخل مفتاح الكتابة والصق رد DeepSeek."
              : "الحفظ غير مفعّل بعد؛ يلزم ضبط سرّي GITHUB_SYNC_TOKEN وSYNC_WRITE_KEY في Vercel."
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          setConfigured(false);
          setStatus("تعذّر الاتصال بخدمة الحفظ. أعد تحميل الصفحة لاحقًا.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function saveReply(event) {
    event.preventDefault();
    if (busy || configured !== true || !reply.trim() || !writeKey) return;

    setBusy(true);
    setStatus("جارٍ حفظ الرد في المستودع...");
    setSavedUrl("");

    try {
      const response = await fetch("/api/sync", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-sync-write-key": writeKey
        },
        body: JSON.stringify({ content: reply })
      });

      const data = await response.json();
      if (!response.ok || !data.ok) {
        const messages = {
          unauthorized: "مفتاح الكتابة غير صحيح.",
          sync_not_configured: "إعدادات الحفظ غير مكتملة في Vercel.",
          content_too_large: "الرد أطول من الحد المسموح."
        };
        throw new Error(messages[data.error] || data.error || "فشل الحفظ.");
      }

      setSavedUrl(data.url);
      setStatus("تم حفظ الرد والتحقق من نجاح GitHub API.");
      setReply("");
      setWriteKey("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "تعذّر حفظ الرد.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main
      dir="rtl"
      style={{
        padding: 24,
        fontFamily: "system-ui, sans-serif",
        maxWidth: 760,
        margin: "0 auto",
        lineHeight: 1.8
      }}
    >
      <h1>ممر ردود المساعدين</h1>
      <p>
        هذه صفحة وسيطة لحفظ رد DeepSeek في ملف محدد داخل GitHub. لا تجعل جلسة
        DeepSeek تستدعي الصفحة تلقائيًا؛ في الوضع الحالي تنسخ الرد من محادثته
        وتلصقه هنا.
      </p>

      <section style={{ border: "1px solid #8886", borderRadius: 12, padding: 16, marginTop: 16 }}>
        <h2 style={{ fontSize: 20, marginTop: 0 }}>الرسالة المرسلة إلى DeepSeek</h2>
        <p>افتح الرابط التالي داخل محادثة DeepSeek ليقرأ آخر رسالة من ChatGPT:</p>
        <a href={OUTGOING_MESSAGE} target="_blank" rel="noreferrer">
          قراءة رسالة ChatGPT عبر Raw
        </a>
      </section>

      <section style={{ border: "1px solid #8886", borderRadius: 12, padding: 16, marginTop: 16 }}>
        <h2 style={{ fontSize: 20, marginTop: 0 }}>حفظ رد DeepSeek</h2>
        <p role="status" aria-live="polite">{status}</p>

        <form onSubmit={saveReply}>
          <label htmlFor="deepseek-reply">الصق الرد الكامل هنا</label>
          <textarea
            id="deepseek-reply"
            value={reply}
            onChange={(event) => setReply(event.target.value)}
            rows={10}
            maxLength={100000}
            required
            style={{
              display: "block",
              width: "100%",
              boxSizing: "border-box",
              padding: 10,
              margin: "8px 0 14px",
              font: "inherit"
            }}
          />

          <label htmlFor="sync-write-key">مفتاح الكتابة الخاص بهذه الصفحة</label>
          <input
            id="sync-write-key"
            type="password"
            value={writeKey}
            onChange={(event) => setWriteKey(event.target.value)}
            autoComplete="off"
            required
            style={{
              display: "block",
              width: "100%",
              boxSizing: "border-box",
              padding: 10,
              margin: "8px 0 14px",
              font: "inherit"
            }}
          />

          <button type="submit" disabled={busy || configured !== true || !reply.trim() || !writeKey}>
            {busy ? "جارٍ الحفظ..." : "حفظ الرد في GitHub"}
          </button>
        </form>

        {savedUrl && (
          <p>
            <a href={savedUrl} target="_blank" rel="noreferrer">
              فتح ملف الرد المحفوظ
            </a>
          </p>
        )}
      </section>

      <p style={{ marginTop: 20, fontSize: 14 }}>
        تنبيه: المستودع وملف الرد قابلان للقراءة العامة. لا تلصق كلمات مرور أو
        رموز وصول أو بيانات خاصة. مفتاح هذه الصفحة منفصل عن رمز GitHub ولا يُرسل
        إلى محادثة DeepSeek.
      </p>
    </main>
  );
}
