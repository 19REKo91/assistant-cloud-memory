"use client";

import { useEffect, useRef, useState } from "react";

const STARTER = {
  role: "assistant",
  content: "أهلًا بك 👋\nهذه مساحة المحادثة الصفراء. اكتب رسالتك، وسنحافظ على هذا المظهر الداكن والنص الأصفر الواضح.\n\nملاحظة: قبل أن يجيب النموذج الحقيقي، يلزم إعداد رمز الوصول ومفتاح الخدمة على الخادم."
};

const SUGGESTIONS = [
  "حلّل فكرة خطوة بخطوة",
  "راجع استنتاجًا نقديًا",
  "ساعدني في كتابة كود"
];

const styles = {
  page: {
    minHeight: "100dvh",
    background: "radial-gradient(ellipse at 50% -15%, #292309 0%, #111114 38%, #09090c 78%)",
    color: "#f6f2df",
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    padding: "20px 14px 24px",
    boxSizing: "border-box"
  },
  shell: { width: "100%", maxWidth: 850, margin: "0 auto" },
  topbar: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    gap: 14, padding: "10px 2px 22px", borderBottom: "1px solid #ffffff12"
  },
  brand: { display: "flex", alignItems: "center", gap: 11, minWidth: 0 },
  mark: {
    width: 40, height: 40, flexShrink: 0, display: "grid", placeItems: "center",
    borderRadius: 14, background: "linear-gradient(145deg, #ffe77b, #d5a900)",
    color: "#191400", fontSize: 22, fontWeight: 900,
    boxShadow: "0 0 28px #ffd62925"
  },
  eyebrow: { color: "#ffd629", letterSpacing: "0.15em", fontSize: 10, fontWeight: 800 },
  brandTitle: { color: "#fff7d4", fontSize: 17, fontWeight: 750, lineHeight: 1.2 },
  status: {
    display: "inline-flex", alignItems: "center", gap: 7, border: "1px solid #ffd62935",
    borderRadius: 999, padding: "7px 10px", color: "#e6d58e", fontSize: 11,
    background: "#ffd6290a", whiteSpace: "nowrap"
  },
  dot: { width: 6, height: 6, borderRadius: 99, background: "#ffd629", boxShadow: "0 0 9px #ffd62980" },
  heading: { padding: "27px 2px 19px" },
  title: { margin: "0 0 9px", fontSize: "clamp(26px, 6vw, 39px)", fontWeight: 850, lineHeight: 1.25, color: "#ffdc36", letterSpacing: "-0.04em" },
  subtitle: { margin: 0, color: "#9d9a8e", fontSize: 14, lineHeight: 1.8 },
  panel: {
    border: "1px solid #ffffff12", borderRadius: 22, overflow: "hidden",
    background: "linear-gradient(180deg, #151518ed, #101013f7)",
    boxShadow: "0 24px 80px #00000045"
  },
  messages: { padding: "18px 14px 20px", display: "flex", flexDirection: "column", gap: 17, minHeight: 280 },
  row: { display: "flex", alignItems: "flex-start", gap: 10, width: "100%" },
  avatar: {
    flexShrink: 0, width: 30, height: 30, borderRadius: 11, display: "grid",
    placeItems: "center", fontSize: 12, fontWeight: 900
  },
  bubble: { maxWidth: "min(100%, 650px)", padding: "13px 15px", borderRadius: 17, lineHeight: 1.85, fontSize: 14, whiteSpace: "pre-wrap", overflowWrap: "anywhere" },
  assistantBubble: { background: "#1c1a12", border: "1px solid #ffd62920", color: "#ffdf45", borderTopRightRadius: 5 },
  userRow: { flexDirection: "row-reverse" },
  userAvatar: { background: "#34343a", color: "#f5f5f5" },
  userBubble: { background: "#2a2a30", border: "1px solid #ffffff0b", color: "#efedf3", borderTopLeftRadius: 5 },
  assistantAvatar: { background: "#ffd629", color: "#211900", boxShadow: "0 0 18px #ffd62918" },
  roleLabel: { display: "block", marginBottom: 5, fontSize: 10, color: "#a8a18b", letterSpacing: ".03em" },
  busy: { fontSize: 12, color: "#ffd629", paddingInlineStart: 41 },
  composerWrap: { borderTop: "1px solid #ffffff12", padding: "14px", background: "#0c0c0f" },
  accessRow: { display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8, marginBottom: 11 },
  accessLabel: { color: "#85828a", fontSize: 11, flexShrink: 0 },
  accessInput: {
    flex: "1 1 160px", minWidth: 0, background: "#151519", border: "1px solid #34333a",
    color: "#efedf3", borderRadius: 10, padding: "9px 11px", outline: "none", fontSize: 12
  },
  composer: { display: "flex", alignItems: "flex-end", gap: 9 },
  textarea: {
    width: "100%", resize: "vertical", minHeight: 54, maxHeight: 150, boxSizing: "border-box",
    background: "#18181d", color: "#fffbe9", border: "1px solid #36343b",
    borderRadius: 15, padding: "14px 14px", font: "inherit", fontSize: 14, lineHeight: 1.6, outline: "none"
  },
  send: {
    height: 54, minWidth: 54, border: 0, borderRadius: 15, background: "#ffd629",
    color: "#171200", fontWeight: 900, fontSize: 22, cursor: "pointer",
    boxShadow: "0 5px 22px #ffd62928", display: "grid", placeItems: "center"
  },
  disabled: { opacity: 0.45, cursor: "not-allowed", boxShadow: "none" },
  footer: { display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, padding: "11px 4px 0", color: "#77747c", fontSize: 11, lineHeight: 1.7 },
  clear: { background: "transparent", border: "1px solid #ffffff20", color: "#b8b4bd", borderRadius: 10, padding: "7px 10px", fontSize: 11, cursor: "pointer" },
  notice: { marginTop: 12, padding: "10px 12px", borderRadius: 12, background: "#ffd6290b", border: "1px solid #ffd62922", color: "#d9c77b", fontSize: 12, lineHeight: 1.7 },
  suggestion: { background: "#18181c", border: "1px solid #ffffff17", color: "#d2cba7", borderRadius: 999, padding: "8px 11px", fontSize: 11, cursor: "pointer" }
};

export default function YellowChatPage() {
  const [messages, setMessages] = useState([STARTER]);
  const [text, setText] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [statusType, setStatusType] = useState("info");
  const [configured, setConfigured] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/chat", { cache: "no-store" })
      .then(response => response.json())
      .then(data => { if (!cancelled) setConfigured(data.configured === true); })
      .catch(() => { if (!cancelled) setConfigured(false); })
      .finally(() => { if (!cancelled) setCheckingSetup(false); });
    return () => { cancelled = true; };
  }, []);

  async function sendMessage(event) {
    event?.preventDefault?.();
    const content = text.trim();
    if (!content || busy) return;

    const userMessage = { role: "user", content };
    const history = [...messages, userMessage];
    setMessages(history);
    setText("");
    setStatus("");
    setBusy(true);

    try {
      const headers = { "Content-Type": "application/json" };
      if (accessToken.trim()) headers["x-yellow-chat-token"] = accessToken.trim();
      const response = await fetch("/api/chat", {
        method: "POST",
        headers,
        cache: "no-store",
        body: JSON.stringify({ messages: history.filter(m => m.role === "user" || m.role === "assistant").slice(-16) })
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data.ok) {
        const messagesByError = {
          chat_not_configured: "الاتصال الحقيقي لم يُفعّل بعد. يلزم إضافة OPENAI_API_KEY وYELLOW_CHAT_ACCESS_TOKEN في إعدادات Vercel.",
          unauthorized: "رمز الوصول غير صحيح. تأكد أنه يطابق YELLOW_CHAT_ACCESS_TOKEN في إعدادات الخادم.",
          rate_limited: "توقفنا لحظيًا لتقليل الطلبات. انتظر دقيقة ثم حاول مجددًا.",
          invalid_messages: "تعذّر قبول الرسائل. قصّر الرسالة وحاول ثانية.",
          provider_error: "وصلنا إلى خدمة الذكاء الاصطناعي لكن تعذّر إكمال الطلب. تحقق من مفتاح الخدمة ورصيد واجهة API."
        };
        throw new Error(messagesByError[data.error] || data.message || data.error || "تعذّر الاتصال.");
      }

      setMessages(current => [...current, { role: "assistant", content: data.text || "لم يصل رد نصي." }]);
      setStatus("");
      setStatusType("info");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "حدث خطأ غير متوقع.");
      setStatusType("error");
      setMessages(current => [...current, { role: "assistant", content: "لم أستطع إكمال هذه الرسالة. راجع التنبيه أسفل المحادثة؛ لم يُحذف نصّك من سجل الشاشة." }]);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  }

  function clearChat() {
    setMessages([STARTER]);
    setStatus("");
    setText("");
  }

  return (
    <main dir="rtl" style={styles.page}>
      <div style={styles.shell}>
        <header style={styles.topbar}>
          <div style={styles.brand}>
            <div style={styles.mark} aria-hidden="true">✦</div>
            <div>
              <div style={styles.eyebrow}>YELLOW / CHAT</div>
              <div style={styles.brandTitle}>المحادثة الصفراء</div>
            </div>
          </div>
          <div style={styles.status} aria-live="polite"><span style={styles.dot} /> {checkingSetup ? "جارٍ فحص الإعداد" : configured ? "الإعداد موجود" : "اتصال ينتظر الإعداد"}</div>
        </header>

        <section style={styles.heading}>
          <h1 style={styles.title}>فكّر بحرية. بلونك.</h1>
          <p style={styles.subtitle}>واجهة هادئة، خلفية داكنة، وكلمات المساعد باللون الأصفر.</p>
        </section>

        <section style={styles.panel} aria-label="منطقة المحادثة">
          <div style={styles.messages} aria-live="polite">
            {messages.map((message, index) => {
              const isUser = message.role === "user";
              return (
                <div key={index + "-" + message.role} style={{ ...styles.row, ...(isUser ? styles.userRow : {}) }}>
                  <div style={{ ...styles.avatar, ...(isUser ? styles.userAvatar : styles.assistantAvatar) }} aria-hidden="true">
                    {isUser ? "أنت" : "✦"}
                  </div>
                  <div style={{ ...styles.bubble, ...(isUser ? styles.userBubble : styles.assistantBubble) }}>
                    <span style={{ ...styles.roleLabel, color: isUser ? "#a8a6b0" : "#c1ab42" }}>
                      {isUser ? "رسالتك" : "المساعد"}
                    </span>
                    {message.content}
                  </div>
                </div>
              );
            })}
            {busy && <div style={styles.busy}>يكتب الرد الآن…</div>}
            <div ref={endRef} />
          </div>

          <div style={styles.composerWrap}>
            <div style={styles.accessRow}>
              <label htmlFor="access-token" style={styles.accessLabel}>رمز الوصول</label>
              <input
                id="access-token"
                type="password"
                value={accessToken}
                onChange={(event) => setAccessToken(event.target.value)}
                autoComplete="off"
                placeholder="أدخل رمز الحماية الذي أعددته للخادم"
                style={styles.accessInput}
              />
            </div>

            <form onSubmit={sendMessage} style={styles.composer}>
              <textarea
                ref={inputRef}
                value={text}
                onChange={(event) => setText(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage(event);
                  }
                }}
                placeholder="اكتب رسالتك هنا… (Enter للإرسال، Shift+Enter لسطر جديد)"
                aria-label="اكتب رسالتك"
                maxLength={4000}
                rows={2}
                style={styles.textarea}
              />
              <button type="submit" disabled={busy || !text.trim()} aria-label="إرسال الرسالة" style={{ ...styles.send, ...(busy || !text.trim() ? styles.disabled : {}) }}>
                {busy ? "…" : "➤"}
              </button>
            </form>

            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 7, marginTop: 12 }}>
              {SUGGESTIONS.map((suggestion) => (
                <button key={suggestion} type="button" onClick={() => { setText(suggestion); inputRef.current?.focus(); }} style={styles.suggestion}>
                  {suggestion}
                </button>
              ))}
            </div>

            {status && (
              <div role="alert" style={{ ...styles.notice, background: statusType === "error" ? "#351a17" : "#ffd6290b", borderColor: statusType === "error" ? "#9c453a" : "#ffd62922", color: statusType === "error" ? "#ffc0b6" : "#d9c77b" }}>
                {status}
              </div>
            )}
          </div>
        </section>

        <footer style={styles.footer}>
          <span>الواجهة تحفظ الرسائل في هذه الصفحة فقط؛ لا تُحفظ على خادمنا.</span>
          <button type="button" onClick={clearChat} style={styles.clear}>مسح المحادثة</button>
        </footer>

        <div style={styles.notice}>
          الخصوصية والأمان: مفتاح OpenAI لا يُرسل إلى المتصفح. اتصال الخدمة لا يعمل إلا بعد إعداد <code>OPENAI_API_KEY</code> ورمز الخادم <code>YELLOW_CHAT_ACCESS_TOKEN</code> في Vercel.
        </div>
      </div>
    </main>
  );
}
