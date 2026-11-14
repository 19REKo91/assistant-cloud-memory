"""
الإطار 6.4.0-α – إضافة المحور الخامس (mp)
المجموع الجديد: 600° = 5 × 120°
"""
import pandas as pd
import math
from scipy.stats import spearmanr

# ============================================================
# 1) صناديق المعايرة
# ============================================================
RHO_MIN, RHO_MAX = 1.74, 22.59
VM_MIN,  VM_MAX  = 7.10, 18.27
R_MIN,   R_MAX   = 28,   203
MP_MIN,  MP_MAX  = -272.2, 3422.0

# ============================================================
# 2) البيانات (28 عنصراً + mp)
# ============================================================
# (Sym, rho, M, R_cov, mp_C, note)
data = [
    ("H", 0.00009, 1.008, 31, -259.16, ""),
    ("He", 0.00018, 4.002, 28, -272.2, "ضغط 2.5MPa"),
    ("Li", 0.534, 6.94, 128, 180.54, ""),
    ("Be", 1.85, 9.012, 96, 1287.0, ""),
    ("B", 2.34, 10.81, 84, 2076.0, ""),
    ("C", 3.51, 12.011, 76, 3550.0, "تسامي"),
    ("N", 0.00125, 14.007, 71, -210.0, ""),
    ("O", 0.00143, 15.999, 66, -218.79, ""),
    ("F", 0.0017, 18.998, 57, -219.67, ""),
    ("Ne", 0.0009, 20.180, 58, -248.59, ""),
    ("Na", 0.968, 22.990, 166, 97.79, ""),
    ("Mg", 1.738, 24.305, 141, 650.0, ""),
    ("Al", 2.70, 26.982, 121, 660.32, ""),
    ("Si", 2.33, 28.085, 111, 1414.0, ""),
    ("P", 1.82, 30.974, 107, 44.15, ""),
    ("S", 2.07, 32.06, 105, 115.21, ""),
    ("Cl", 0.0032, 35.45, 102, -101.5, ""),
    ("Ar", 0.00178, 39.948, 106, -189.34, ""),
    ("K", 0.862, 39.098, 203, 63.5, ""),
    ("Ca", 1.55, 40.078, 176, 842.0, ""),
    ("Sc", 2.985, 44.956, 170, 1541.0, ""),
    ("Ti", 4.506, 47.867, 160, 1668.0, ""),
    ("V", 6.11, 50.942, 153, 1910.0, ""),
    ("Cr", 7.19, 51.996, 139, 1907.0, ""),
    ("Mn", 7.43, 54.938, 139, 1246.0, ""),
    ("Fe", 7.874, 55.845, 132, 1538.0, ""),
    ("Os", 22.59, 190.23, 128, 3033.0, ""),
    ("Hg", 13.534, 200.59, 132, -38.83, ""),
]

# ============================================================
# 3) التطبيع
# ============================================================
def n_rho(r): return (r - RHO_MIN) / (RHO_MAX - RHO_MIN)
def n_Vm(v):  return (v - VM_MIN)  / (VM_MAX  - VM_MIN)
def n_R(R):   return (R - R_MIN)   / (R_MAX   - R_MIN)
def n_mp(m):  return (m - MP_MIN)  / (MP_MAX  - MP_MIN)

# ============================================================
# 4) قاعدة 60
# ============================================================
def rule_60(th3):
    if th3 >= 0:
        return th3, 0
    n = math.ceil(-th3 / 60)
    return th3 + 60 * n, n

# ============================================================
# 5) التحليل الكامل
# ============================================================
def analyze(sym, rho, M, R, mp, note):
    V_m = M / rho
    rho_n, V_n, R_n, mp_n = n_rho(rho), n_Vm(V_m), n_R(R), n_mp(mp)

    th1 = 80 - 70 * rho_n
    th2 = 10 + 70 * V_n
    th4 = 80 - 70 * R_n
    th5 = 80 - 70 * mp_n
    th3_raw = 300 - th1 - th2 - th4 - th5

    th3_eff, n = rule_60(th3_raw)
    th2_eff = th2 - 60 * n

    S_A = 90 + th1 / 2
    S_B = 90 + th2_eff / 2
    S_C = 90 + th3_eff / 2
    S_R = 90 + th4 / 2
    S_M = 90 + th5 / 2
    total = S_A + S_B + S_C + S_R + S_M

    dominant = max(
        [("A", S_A), ("B", S_B), ("C", S_C), ("R", S_R), ("M", S_M)],
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
    if mp_n < 0 or mp_n > 1:   flags.append("mp")

    return [
        sym, round(rho_n, 3), round(V_n, 2), round(mp_n, 3),
        round(th1, 1), round(th2_eff, 1), round(th4, 1), round(th5, 1),
        round(th3_eff, 1), n,
        round(S_A, 1), round(S_B, 1), round(S_C, 1), round(S_R, 1), round(S_M, 1),
        round(total, 2),
        round(a_over_b, 2) if not math.isnan(a_over_b) else "-",
        dominant, "+".join(flags) if flags else "-", note
    ]

results = [analyze(*row) for row in data]

df = pd.DataFrame(results, columns=[
    "Sym", "ρ_n", "V_n", "mp_n",
    "θ₁", "θ₂eff", "θ₄", "θ₅", "θ₃eff", "n",
    "S_A", "S_B", "S_C", "S_R", "S_M", "ΣS",
    "a/b", "Dom", "Flags", "Note"
])

# حفظ CSV كملف ناتج للتنزيل من GitHub Actions
df.to_csv("output/element-table-6.4.0-alpha.csv", index=False, encoding="utf-8-sig")

# ============================================================
# 6) الطباعة
# ============================================================
print("=" * 130)
print("الإطار 6.4.0-α – الجدول الكامل (5 محاور، مجموع 600°)")
print("=" * 130)
print(df.to_string(index=False))

# ============================================================
# 7) التحقق الصارم
# ============================================================
print("\n" + "=" * 130)
print("التحقق 1: ΣS يجب أن يكون 600.00 لكل عنصر")
print("=" * 130)
bad = df[abs(df["ΣS"] - 600.0) > 0.01]
if bad.empty:
    print("✅ جميع العناصر: ΣS = 600.00")
else:
    print("❌ مخالفات:")
    print(bad[["Sym", "ΣS"]].to_string(index=False))

print("\n" + "=" * 130)
print("التحقق 2: ارتباط S_M مع mp (يجب أن يكون سالباً قوياً)")
print("=" * 130)
mp_vals = [row[4] for row in data]
sm_vals = df["S_M"].tolist()
rho_sp, p_val = spearmanr(mp_vals, sm_vals)
print(f"معامل سبيرمان: ρ = {rho_sp:.4f}  (p = {p_val:.2e})")
if rho_sp < -0.85:
    print("✅ ارتباط سالب قوي: S_M يعكس mp بنجاح")
else:
    print("⚠️ الارتباط أضعف من المتوقع")

# ============================================================
# 8) المقارنات الحاسمة
# ============================================================
print("\n" + "=" * 130)
print("المقارنة 1: Pb (غير موجود في الجدول، نحسبه يدوياً)")
print("=" * 130)
pb_rho, pb_M, pb_R, pb_mp = 11.34, 207.2, 146, 327.0
pb = analyze("Pb", pb_rho, pb_M, pb_R, pb_mp, "")
print(f"Pb: θ₁={pb[4]}, θ₂eff={pb[5]}, θ₄={pb[6]}, θ₅={pb[7]}, "
      f"S_M={pb[14]}, ΣS={pb[15]}, a/b={pb[16]}")

print("\nالمقارنة 2: Pb vs Os (الفارق الحاسم)")
print("=" * 130)
os_row = df[df["Sym"] == "Os"].iloc[0]
print(f"Pb: S_M = {pb[14]:.2f}, θ₅ = {pb[7]:.2f}")
print(f"Os: S_M = {os_row['S_M']:.2f}, θ₅ = {os_row['θ₅']:.2f}")
print(f"ΔS_M = {abs(pb[14] - os_row['S_M']):.2f}°  ← الفارق الذي لم يكن موجوداً قبل θ₅")

print("\n" + "=" * 130)
print("المقارنة 3: Na vs Fe (كلاهما a/b > 1)")
print("=" * 130)
for nm in ["Na", "Fe", "K", "Cr"]:
    r = df[df["Sym"] == nm].iloc[0]
    print(f"{nm}: mp_n={r['mp_n']:.3f}, S_M={r['S_M']:.2f}, a/b={r['a/b']}")

print("\n" + "=" * 130)
print("المقارنة 4: Hg vs Li (سائل vs صلب)")
print("=" * 130)
for nm in ["Hg", "Li", "Pb"]:
    if nm == "Pb":
        print(f"Pb: mp_n={pb[3]:.3f}, S_M={pb[14]:.2f}")
    else:
        r = df[df["Sym"] == nm].iloc[0]
        print(f"{nm}: mp_n={r['mp_n']:.3f}, S_M={r['S_M']:.2f}")

print("\n" + "=" * 130)
print("توزيع الصفة المهيمنة (5 محاور)")
print("=" * 130)
print(df["Dom"].value_counts().to_string())
