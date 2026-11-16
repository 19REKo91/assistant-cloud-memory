#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Framework 6.5.0 — Recalculation Engine
يقرأ elements_input_118.csv ويعيد حساب كل الأعمدة المشتقة.
لا يعدّل أي معادلة أو ثابت. يعزل أخطاء المصدر.
"""

import csv, math

# === ثوابت صندوق المعايرة (لا تعدّل) ===
RHO_MIN, RHO_MAX = 0.534, 22.59
VM_MIN,  VM_MAX  = 7.0923, 18.27
R_MIN,   R_MAX   = 28, 203
MP_MIN,  MP_MAX  = -272.2, 3422
C_SIDE = 3.0

def norm_rho(rho):  return (rho - RHO_MIN) / (RHO_MAX - RHO_MIN)
def norm_vm(vm):    return (vm  - VM_MIN)  / (VM_MAX  - VM_MIN)
def norm_r(r):      return (r   - R_MIN)   / (R_MAX   - R_MIN)
def norm_mp(mp):    return (mp  + 272.2)   / (MP_MAX  - MP_MIN)  # 3694.2

def angles(rho, Vm, R, mp):
    rho_n = norm_rho(rho); V_n = norm_vm(Vm)
    R_n   = norm_r(R);     mp_n = norm_mp(mp)
    th1  = 80 - 70*rho_n
    th2r = 10 + 70*V_n
    th4  = 80 - 70*R_n
    th5  = 80 - 70*mp_n
    # mod 360
    n = math.floor(th2r / 360.0)
    th2e = th2r - 360.0*n
    if th2e == 0: th2e = 360.0
    th3e = 300.0 - (th1 + th2e + th4 + th5)
    return dict(rho_n=rho_n, V_n=V_n, R_n=R_n, mp_n=mp_n,
                th1=th1, th2raw=th2r, th2end=th2e, n=n,
                th4=th4, th5=th5, th3end=th3e)

def doses(th1, th2e, th3e, th4, th5):
    return dict(S_A=90+th1/2, S_B=90+th2e/2, S_C=90+th3e/2,
                S_R=90+th4/2, S_M=90+th5/2)

def sides(th1, th2e, th3e):
    s3 = abs(math.sin(math.radians(th3e)))
    if s3 == 0:  # انهيار كروي
        return dict(a=float('inf'), b=float('inf'), ab=float('inf'),
                    collapse=True)
    a = 3.0*math.sin(math.radians(th1)) / s3
    b = 3.0*abs(math.sin(math.radians(th2e))) / s3
    ab = a/b if b != 0 else float('inf')
    return dict(a=a, b=b, ab=ab, collapse=False)

def flags(V_n, mp_n, th3e):
    f = []
    if not (0 <= V_n <= 1):  f.append("V_OUT")
    if not (0 <= mp_n <= 1): f.append("MP_OUT")
    if th3e < 0:             f.append("θ₃_NEG")
    return f

def recompute_row(row):
    M   = float(row['M']);  rho = float(row['rho'])
    R   = float(row['R']);  mp  = float(row['mp_C'])
    Vm  = M/rho
    ag  = angles(rho, Vm, R, mp)
    ds  = doses(ag['th1'], ag['th2end'], ag['th3end'], ag['th4'], ag['th5'])
    sd  = sides(ag['th1'], ag['th2end'], ag['th3end'])
    fl  = flags(ag['V_n'], ag['mp_n'], ag['th3end'])
    out = dict(row)
    out.update(ag); out.update(ds); out.update(sd)
    out['SumS'] = sum(ds.values())
    out['SumTheta'] = ag['th1']+ag['th2end']+ag['th3end']+ag['th4']+ag['th5']
    out['Flags'] = "; ".join(fl)
    return out

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python recalc_6.5.0_engine.py elements_input_118.csv")
        sys.exit(1)
    with open(sys.argv[1], encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    results = [recompute_row(r) for r in rows]
    cols = ['Sym','M','rho','R','mp_C','V_n','th1','th2raw','th2end','n',
            'th4','th5','th3end','S_A','S_B','S_C','S_R','S_M',
            'SumS','SumTheta','ab','Flags']
    w = csv.DictWriter(sys.stdout, fieldnames=cols, extrasaction='ignore')
    w.writeheader()
    for r in results: w.writerow(r)
