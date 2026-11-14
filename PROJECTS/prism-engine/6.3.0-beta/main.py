"""
الإطار 6.3.0-β – الكود المصحح الرسمي
التصحيح الجوهري: قاعدة 60 تطرح 60n من θ₂ (وفق دستور 6.2.2-R الأصلي)
"""
import pandas as pd
import math
from pathlib import Path

# ============================================================
# 1) صندوق المعايرة (نطاق مختار)
# ============================================================
RHO_MIN, RHO_MAX = 1.74, 22.59
VM_MIN,  VM_MAX  = 7.10, 18.27
R_MIN,   R_MAX   = 28,   203

# ============================================================
# 2) البيانات
# ============================================================
data = [
    ("H", 0.00009, 1.008, 31), ("He", 0.00018, 4.002, 28),
    ("Li", 0.534, 6.94, 128),   ("Be", 1.85, 9.012, 96),
    ("B", 2.34, 10.81, 84),     ("C", 3.51, 12.011, 76),
    ("N", 0.00125, 14.007, 71), ("O", 0.00143, 15.999, 66),
    ("F", 0.0017, 18.998, 57),  ("Ne", 0.0009, 20.180, 58),
    ("Na", 0.968, 22.990, 166), ("Mg", 1.738, 24.305, 141),
    ("Al", 2.70, 26.982, 121),  ("Si", 2.33, 28.085, 111),
    ("P", 1.82, 30.974, 107),   ("S", 2.07, 32.06, 105),
    ("Cl", 0.0032, 35.45, 102), ("Ar", 0.00178, 39.948, 106),
    ("K", 0.862, 39.098, 203),  ("Ca", 1.55, 40.078, 176),
    ("Sc", 2.985, 44.956, 170), ("Ti", 4.506, 47.867, 160),
    ("V", 6.11, 50.942, 153),   ("Cr", 7.19, 51.996, 139),
    ("Mn", 7.43, 54.938, 139),  ("Fe", 7.874, 55.845, 132),
    ("Os", 22.59, 190.23, 128), ("Hg", 13.534, 200.59, 132),
]

# ============================================================
# 3) التطبيع
# ============================================================
def norm_rho(r): return (r - RHO_MIN) / (RHO_MAX - RHO_MIN)
def norm_Vm(v):  return (v - VM_MIN)  / (VM_MAX  - VM_MIN)
def norm_R(R):   return (R - R_MIN)   / (R_MAX   - R_MIN)

# ============================================================
# 4) قاعدة 60 (المصححة: اطرح 60n من θ₂)
# ============================================================
def rule_60(th3_raw):
    if th3_raw >= 0:
        return th3_raw, 0
    n = math.ceil(-th3_raw / 60)
    return th3_raw + 60 * n, n

# ============================================================
# 5) تصنيف حالة المادة
# ============================================================
def classify(Vn):
    if Vn <= 0.25:  return "صلبة صلدة"
    if Vn <= 11.0:  return "سائلة/طرية"
    if Vn > 986:    return "غازية"
    return "فجوة زمكانية"

# ============================================================
# 6) التحليل الكامل
# ============================================================
def analyze(sym, rho, M, R):
    V_m = M / rho
    rho_n = norm_rho(rho)
    V_n = norm_Vm(V_m)
    R_n = norm_R(R)

    th1 = 80 - 70 * rho_n
    th2 = 10 + 70 * V_n
    th4 = 80 - 70 * R_n
    th3_raw = 240 - th1 - th2 - th4

    th3_eff, n = rule_60(th3_raw)
    th2_eff = th2 - 60 * n   # ← الإصلاح الجوهري

    S_A = 90 + th1 / 2
    S_B = 90 + th2_eff / 2
    S_C = 90 + th3_eff / 2
    S_R = 90 + th4 / 2

    dominant = max(
        [("A", S_A), ("B", S_B), ("C", S_C), ("R", S_R)],
        key=lambda x: x[1]
    )[0]

    s3 = math.sin(math.radians(th3_eff))
    if abs(s3) > 1e-12:
        a = 3 * math.sin(math.radians(th1)) / s3
        b = 3 * abs(math.sin(math.radians(th2_eff))) / s3
        a_over_b = a / b if b else float('inf')
    else:
        a_over_b = float('nan')

    flags = []
    if rho_n < 0 or rho_n > 1: flags.append("ρ")
    if V_n < 0 or V_n > 1:     flags.append("V")
    if R_n < 0 or R_n > 1:     flags.append("R")

    return [
        sym, round(rho_n, 3), round(V_n, 2),
        round(th1, 1), round(th2_eff, 1), round(th4, 1),
        round(th3_eff, 1), n,
        round(S_A, 1), round(S_B, 1), round(S_C, 1), round(S_R, 1),
        round(S_A + S_B + S_C + S_R, 2),
        round(a_over_b, 2) if not math.isnan(a_over_b) else "-",
        dominant, classify(V_n),
        "+".join(flags) if flags else "-"
    ]

# ============================================================
# 7) التشغيل
# ============================================================
results = [analyze(*row) for row in data]

df = pd.DataFrame(results, columns=[
    "Sym", "ρ_n", "V_n", "θ₁", "θ₂eff", "θ₄", "θ₃eff", "n",
    "S_A", "S_B", "S_C", "S_R", "ΣS", "a/b", "Dom", "State", "Flags"
])

print("=" * 100)
print("الإطار 6.3.0-β — الجدول الكامل")
print("=" * 100)
print(df.to_string(index=False))

# ============================================================
# 7A) تصدير CSV للأرشيف
# ============================================================
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)
csv_path = output_dir / "element-table-6.3.0-beta.csv"
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"\nCSV_SAVED: {csv_path}")
print(f"ROWS_EXPORTED: {len(df)}")

# ============================================================
# 8) التحقق الصارم
# ============================================================
print("\n" + "=" * 100)
print("التحقق: ΣS يجب أن يكون 480.00 لكل عنصر")
print("=" * 100)
bad = df[abs(df["ΣS"] - 480.0) > 0.01]
if bad.empty:
    print("✅ جميع العناصر: ΣS = 480.00")
else:
    print("❌ مخالفات:")
    print(bad[["Sym", "ΣS"]].to_string(index=False))

print("\n" + "=" * 100)
print("التحقق: Fe vs Cr (التمييز بالرأس الرابع)")
print("=" * 100)
for nm in ["Fe", "Cr"]:
    r = df[df["Sym"] == nm].iloc[0]
    print(f"{nm}: θ₁={r['θ₁']}, θ₂eff={r['θ₂eff']}, θ₄={r['θ₄']}, "
          f"S_R={r['S_R']}, a/b={r['a/b']}")

print("\n" + "=" * 100)
print("توزيع حالات المادة")
print("=" * 100)
print(df["State"].value_counts().to_string())

print("\n" + "=" * 100)
print("العناصر التي تجاوزت صندوق المعايرة")
print("=" * 100)
out = df[df["Flags"] != "-"][["Sym", "Flags", "ρ_n", "V_n"]]
print(out.to_string(index=False) if not out.empty else "لا يوجد")
