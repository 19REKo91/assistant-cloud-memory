import hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "PROJECTS/C-G-Z-Test-v1.0/data/C_G_Z_unified_accountant_input_118.csv"
OUT = ROOT / "PROJECTS/C-G-Z-Test-v1.0/reports"
RHO_MIN, RHO_MAX = 1.74, 22.59
VM_MIN, VM_MAX = 7.10, 18.27
TOL = 1e-8

def corr(x, y, method):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 3 or np.unique(x).size < 2 or np.unique(y).size < 2:
        return {"n": int(len(x)), "statistic": None, "p_value": None}
    r = stats.spearmanr(x, y) if method == "spearman" else stats.pearsonr(x, y)
    return {"n": int(len(x)), "statistic": float(r.statistic), "p_value": float(r.pvalue)}

def correlations(frame, subset):
    rows = []
    for col in ["C_calc", "rho", "Vm_calc", "Z", "M"]:
        for method in ["spearman", "pearson"]:
            rows.append({"subset": subset, "predictor": col, "method": method,
                         **corr(frame[col], frame["G_active_GPa"], method)})
    return rows

def loocv(frame, subset):
    specs = [("C", ["C_calc"]), ("rho", ["rho"]), ("Vm", ["Vm_calc"]),
             ("Z", ["Z"]), ("rho+M", ["rho", "M"]),
             ("rho+M+C_exploratory", ["rho", "M", "C_calc"])]
    output, preds = [], []
    y = frame["G_active_GPa"].to_numpy(float)
    for name, cols in specs:
        X = frame[cols].to_numpy(float)
        errors = []
        for tr, te in LeaveOneOut().split(X):
            model = make_pipeline(StandardScaler(), LinearRegression())
            model.fit(X[tr], y[tr])
            pred = float(model.predict(X[te])[0])
            actual = float(y[te[0]])
            errors.append(pred - actual)
            preds.append({"subset": subset, "model": name, "Z": int(frame.iloc[te[0]].Z),
                          "Sym": frame.iloc[te[0]].Sym, "actual_GPa": actual,
                          "predicted_GPa": pred, "error_GPa": pred-actual})
        e = np.asarray(errors)
        output.append({"subset": subset, "model": name, "n": len(y),
                       "RMSE_GPa": float(np.sqrt(np.mean(e**2))),
                       "MAE_GPa": float(np.mean(np.abs(e)))})
    return output, preds

def main():
    if not DATA.exists(): raise FileNotFoundError(DATA)
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    df = pd.read_csv(DATA, na_values=["NA", "N/A", ""])
    needed = ["Z","Sym","M","rho","G_active_GPa","Vm_cm3_mol","rho_n","V_n","C_deg"]
    missing = [c for c in needed if c not in df.columns]
    if missing: raise ValueError(f"Missing columns: {missing}")
    if len(df) != 118 or set(pd.to_numeric(df.Z).astype(int)) != set(range(1,119)):
        raise ValueError("Input must contain exactly one row for each Z=1..118")
    if "G_legacy_input_GPa" not in df.columns:
        raise ValueError("Legacy/active G separation not found")
    for c in ["Z","M","rho","G_active_GPa","Vm_cm3_mol","rho_n","V_n","C_deg"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    valid = df.M.notna() & df.rho.notna() & (df.rho != 0)
    df["Vm_calc"] = np.nan
    df["rho_n_calc"] = np.nan
    df["V_n_calc"] = np.nan
    df["C_calc"] = np.nan
    df.loc[valid,"Vm_calc"] = df.loc[valid,"M"] / df.loc[valid,"rho"]
    df.loc[valid,"rho_n_calc"] = (df.loc[valid,"rho"]-RHO_MIN)/(RHO_MAX-RHO_MIN)
    df.loc[valid,"V_n_calc"] = (df.loc[valid,"Vm_calc"]-VM_MIN)/(VM_MAX-VM_MIN)
    df.loc[valid,"C_calc"] = 90+70*(df.loc[valid,"rho_n_calc"]-df.loc[valid,"V_n_calc"])
    checks = {}
    for calc, source in [("Vm_calc","Vm_cm3_mol"),("rho_n_calc","rho_n"),
                         ("V_n_calc","V_n"),("C_calc","C_deg")]:
        m = df[calc].notna() & df[source].notna()
        delta = (df.loc[m,calc]-df.loc[m,source]).abs()
        checks[calc] = {"n":int(m.sum()), "max_abs_difference":float(delta.max()) if len(delta) else None,
                        "pass":bool((delta <= TOL).all())}
        if not checks[calc]["pass"]: raise AssertionError(f"Mismatch: {calc}")
    df["rho_range_recomputed"] = np.where(df.rho.isna(),"MISSING",
        np.where(df.rho.between(RHO_MIN,RHO_MAX),"IN_CALIBRATION_RANGE","OUT_OF_CALIBRATION_RANGE"))
    df["Vm_range_recomputed"] = np.where(df.Vm_calc.isna(),"MISSING",
        np.where(df.Vm_calc.between(VM_MIN,VM_MAX),"IN_CALIBRATION_RANGE","OUT_OF_CALIBRATION_RANGE"))
    g = df[df.G_active_GPa.notna() & valid].sort_values("Z").reset_index(drop=True)
    inside = g[(g.rho_range_recomputed=="IN_CALIBRATION_RANGE") &
               (g.Vm_range_recomputed=="IN_CALIBRATION_RANGE")].reset_index(drop=True)
    corr_rows = correlations(g,"all_G_active")
    if len(inside)>=3: corr_rows += correlations(inside,"both_ranges_in_calibration")
    cv, predictions = loocv(g,"all_G_active")
    if len(inside)>=5:
        cv2,p2 = loocv(inside,"both_ranges_in_calibration")
        cv += cv2; predictions += p2
    X = g[["rho","M"]].to_numpy(float); y = g.G_active_GPa.to_numpy(float)
    ols = LinearRegression().fit(X,y)
    r2 = ols.score(X,y)
    r2_rho = LinearRegression().fit(g[["M"]],g.rho).score(g[["M"]],g.rho)
    r2_m = LinearRegression().fit(g[["rho"]],g.M).score(g[["rho"]],g.M)
    vif = {"rho": float(1/(1-r2_rho)) if r2_rho<1 else None,
           "M": float(1/(1-r2_m)) if r2_m<1 else None}
    OUT.mkdir(parents=True,exist_ok=True)
    df.to_csv(OUT/"element_level_recalculation_118.csv",index=False)
    pd.DataFrame(corr_rows).to_csv(OUT/"correlations.csv",index=False)
    pd.DataFrame(cv).to_csv(OUT/"loocv_metrics.csv",index=False)
    pd.DataFrame(predictions).to_csv(OUT/"loocv_predictions.csv",index=False)
    summary = {
      "test":"C-G-Z Test v1.0","input_sha256":digest,"rows":len(df),
      "rows_recalculated":int(valid.sum()),"rows_not_recalculable":int((~valid).sum()),
      "G_active_listed":int(df.G_active_GPa.notna().sum()),
      "G_active_missing":int(df.G_active_GPa.isna().sum()),"G_legacy_used":False,
      "rho_out_of_range":int((df.rho_range_recomputed=="OUT_OF_CALIBRATION_RANGE").sum()),
      "Vm_out_of_range":int((df.Vm_range_recomputed=="OUT_OF_CALIBRATION_RANGE").sum()),
      "both_in_range_total":int(((df.rho_range_recomputed=="IN_CALIBRATION_RANGE") &
                                 (df.Vm_range_recomputed=="IN_CALIBRATION_RANGE")).sum()),
      "active_G_both_in_range":len(inside),"calculation_checks":checks,
      "OLS_G_from_rho_M":{"n":len(g),"intercept":float(ols.intercept_),
        "coef_rho":float(ols.coef_[0]),"coef_M":float(ols.coef_[1]),
        "R2_in_sample":float(r2),"VIF":vif},
      "correlations":corr_rows,"LOOCV":cv,
      "notes":["Only G_active_GPa used; G_legacy_input_GPa excluded.",
       "No imputation or clipping.","C is deterministic from rho and M via Vm.",
       "LOOCV scaling fitted only on each training fold.",
       "LOOCV is internal validation, not external validation.",
       "Correlation does not establish causation; G metadata are not harmonized."]
    }
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    lines=["C-G-Z TEST v1.0 — GITHUB ACTIONS RUN",f"Input SHA-256: {digest}",
      f"Rows: {len(df)} | recalculable: {int(valid.sum())} | active G: {len(g)} | G missing: {int(df.G_active_GPa.isna().sum())}",
      f"Active G within both calibration ranges: {len(inside)}","","CALCULATION CHECKS"]
    for k,v in checks.items(): lines.append(f"{k}: n={v['n']} max_abs_difference={v['max_abs_difference']} PASS={v['pass']}")
    lines += ["","CORRELATIONS"]
    for r in corr_rows: lines.append(f"{r['subset']} | {r['predictor']} | {r['method']} | n={r['n']} | stat={r['statistic']} | p={r['p_value']}")
    lines += ["","LOOCV"]
    for r in cv: lines.append(f"{r['subset']} | {r['model']} | n={r['n']} | RMSE={r['RMSE_GPa']:.6f} GPa | MAE={r['MAE_GPa']:.6f} GPa")
    lines += ["","OLS G ~ rho + M",f"R2={r2:.8f}; VIF={vif}",
      "CAUTIONS: C is derived from rho and M; associations are not independent evidence.",
      "G metadata are not condition-harmonized; missing G may cause selection bias.",
      "LOOCV is internal validation only. No causal inference.",
      "STATUS: COMPLETED"]
    (OUT/"report.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))
    print(f"REPORTS={OUT}")

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"FATAL: {type(e).__name__}: {e}",file=sys.stderr)
        raise
