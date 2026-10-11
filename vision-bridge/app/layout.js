export const metadata = {
  title: "جسر الرؤيا وممر ردود المساعدين",
  description: "جسر الرؤيا وحفظ ردود DeepSeek في GitHub"
};

export default function RootLayout({ children }) {
  return (
    <html lang="ar" dir="rtl">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
