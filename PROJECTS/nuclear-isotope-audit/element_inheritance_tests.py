#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent cumulative inheritance tests: binary-box loss and nuclear mass defect."""
from __future__ import annotations
import math
import re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "outputs"
BRICK_U = 0.016
BOX_SOURCE = REPO / "PROJECTS/triangle-framework/6.5.0/elements_input_118.csv"
ISOTOPE_SOURCE = OUT / "isotope_cumulative_steps_all.csv"
NUBASE_SOURCE = OUT / "nubase2020_parsed.csv"

def require_file(path):
    if not path.exists():
        raise FileNotFoundError(f"Required source file missing: {path}")

def run_box_loss_test():
    require_file(BOX_SOURCE)
    f = pd.read_csv(BOX_SOURCE, dtype={"Sym":"string","M_source":"string","Data_Quality":"string"})
    needed = {"Z","Sym","M","M_source","Data_Quality"}
    if needed - set(f.columns):
        raise ValueError(f"Box source missing columns: {sorted(needed-set(f.columns))}")
    f["Z"] = pd.to_numeric(f["Z"], errors="raise").astype(int)
    f["M"] = pd.to_numeric(f["M"], errors="coerce")
    f = f.sort_values("Z").reset_index(drop=True)
    if len(f) != 118 or f["Z"].tolist() != list(range(1,119)):
        raise AssertionError("Box source must contain exactly one record for each Z=1..118.")
    if f["M"].isna().any() or (f["M"] <= 0).any():
        raise AssertionError("Missing or nonpositive representative element mass.")
    ns=[]; ls=[]; us=[]; ps=[]; ds=[]
    for mass in f["M"].astype(float):
        n=math.floor(math.log2(mass/BRICK_U))
        lo=BRICK_U*(2**n); hi=2.0*lo
        ns.append(n); ls.append(lo); us.append(hi)
        ps.append(100.0*(mass-lo)/lo); ds.append(hi-mass)
    f["box_n"]=ns; f["L_u"]=ls; f["U_u"]=us
    f["mass_position_pct"]=ps; f["new_box_loss_u"]=ds
    f["box_loss_fraction_of_U_pct"]=[100*d/u for d,u in zip(ds,us)]
    f["inherited_box_loss_u"]=pd.Series(ds).cumsum().shift(1,fill_value=0.0)
    f["cumulative_box_loss_u"]=pd.Series(ds).cumsum()
    f["mass_source"]=f["M_source"]; f["mass_quality_flag"]=f["Data_Quality"]
    if not ((f["inherited_box_loss_u"]+f["new_box_loss_u"]-f["cumulative_box_loss_u"]).abs()<1e-10).all():
        raise AssertionError("Box cumulative inheritance recurrence failed.")
    f.to_csv(OUT/"element_inheritance_box_loss_118.csv",index=False,na_rep="NA",encoding="utf-8-sig")
    return f

def half_life_seconds(value_text, unit_text):
    t=str(value_text or "").strip(); u=str(unit_text or "").strip().lower()
    if t.lower() in {"stbl","stable"}: return math.inf
    m=re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?",t,re.I)
    if not m: return math.nan
    try: value=float(m.group(0))
    except ValueError: return math.nan
    factors={"as":1e-18,"fs":1e-15,"ps":1e-12,"ns":1e-9,"us":1e-6,"µs":1e-6,"μs":1e-6,
             "ms":1e-3,"s":1.0,"sec":1.0,"m":60.0,"min":60.0,"h":3600.0,"d":86400.0,
             "y":365.25*86400.0,"yr":365.25*86400.0,"ky":1e3*365.25*86400.0,
             "my":1e6*365.25*86400.0,"gy":1e9*365.25*86400.0}
    factor=factors.get(u)
    return value*factor if factor is not None and value>=0 else math.nan

def natural_abundance(decay_modes):
    m=re.search(r"(?:^|\s)IS\s*=\s*([0-9]+(?:\.[0-9]+)?)",str(decay_modes or ""))
    return float(m.group(1)) if m else math.nan

def load_isotope_table():
    require_file(ISOTOPE_SOURCE); require_file(NUBASE_SOURCE)
    ame=pd.read_csv(ISOTOPE_SOURCE,low_memory=False)
    nub=pd.read_csv(NUBASE_SOURCE,low_memory=False)
    need_a={"Z","N","A","Symbol","AME_mass_defect_u_from_binding","Binding_energy_per_A_keV","AME_estimated_or_flagged"}
    need_n={"Z","A","Half_life_text","Half_life_unit","Decay_modes"}
    if need_a-set(ame.columns): raise ValueError(f"Isotope source missing: {sorted(need_a-set(ame.columns))}")
    if need_n-set(nub.columns): raise ValueError(f"NUBASE source missing: {sorted(need_n-set(nub.columns))}")
    if "Ground_state_candidate" in nub.columns:
        nub = nub[nub["Ground_state_candidate"].astype("string").str.lower().isin(["true", "1", "yes"])].copy()
    nub=nub[["Z","A","Half_life_text","Half_life_unit","Decay_modes"]].copy()
    f=ame.merge(nub,on=["Z","A"],how="left",validate="one_to_one")
    f["natural_abundance_pct"]=f["Decay_modes"].map(natural_abundance)
    f["half_life_seconds"]=[half_life_seconds(t,u) for t,u in zip(f["Half_life_text"],f["Half_life_unit"])]
    f["is_stable"]=f["Half_life_text"].astype("string").str.strip().str.lower().isin(["stbl","stable"])
    f["defect_u"]=pd.to_numeric(f["AME_mass_defect_u_from_binding"],errors="coerce")
    f["binding_energy_per_nucleon_MeV"]=pd.to_numeric(f["Binding_energy_per_A_keV"],errors="coerce")/1000.0
    f["source"]="AME2020 binding energy; NUBASE2020 isotope status/abundance"
    f["quality_flag"]=f["AME_estimated_or_flagged"]
    f=f.sort_values(["Z","A"]).reset_index(drop=True)
    if f.duplicated(["Z","A"]).any(): raise AssertionError("Duplicate isotope keys after AME/NUBASE join.")
    return f

def write_track(name, table, selector):
    rows=[]; running=0.0; selected=0
    for z in range(1,119):
        c=table[table["Z"]==z].copy()
        chosen=selector(c) if not c.empty else None
        inherited=running
        if chosen is None:
            rows.append({"Z":z,"Symbol":c["Symbol"].iloc[0] if not c.empty else pd.NA,
                         "selected_A":pd.NA,"selected_N":pd.NA,"selection_value":pd.NA,
                         "binding_energy_per_nucleon_MeV":pd.NA,"new_defect_u":pd.NA,
                         "inherited_observed_sum_u":inherited,"cumulative_observed_sum_u":running,
                         "status":"NO_ELIGIBLE_ISOTOPE","cumulative_scope":"PARTIAL_SUM_ONLY; missing Z adds no invented value",
                         "source":"AME2020 + NUBASE2020"})
            continue
        defect=float(chosen["defect_u"])
        if not math.isfinite(defect):
            rows.append({"Z":z,"Symbol":chosen["Symbol"],"selected_A":int(chosen["A"]),
                         "selected_N":int(chosen["N"]),"selection_value":pd.NA,
                         "binding_energy_per_nucleon_MeV":chosen["binding_energy_per_nucleon_MeV"],
                         "new_defect_u":pd.NA,"inherited_observed_sum_u":inherited,
                         "cumulative_observed_sum_u":running,"status":"DEFECT_MISSING",
                         "cumulative_scope":"PARTIAL_SUM_ONLY; missing Z adds no invented value",
                         "source":"AME2020 + NUBASE2020"})
            continue
        running+=defect; selected+=1
        if name=="most_abundant_natural": value=chosen["natural_abundance_pct"]
        elif name=="most_stable": value=chosen["binding_energy_per_nucleon_MeV"]
        else: value=chosen["half_life_seconds"]
        rows.append({"Z":z,"Symbol":chosen["Symbol"],"selected_A":int(chosen["A"]),
                     "selected_N":int(chosen["N"]),"selection_value":value,
                     "binding_energy_per_nucleon_MeV":chosen["binding_energy_per_nucleon_MeV"],
                     "new_defect_u":defect,"inherited_observed_sum_u":inherited,
                     "cumulative_observed_sum_u":running,"status":"SELECTED",
                     "cumulative_scope":"PARTIAL_SUM_ONLY; inspect status and missing Z",
                     "source":"AME2020 + NUBASE2020"})
    out=pd.DataFrame(rows)
    exp=out["inherited_observed_sum_u"]+out["new_defect_u"].fillna(0.0)
    if not (exp.sub(out["cumulative_observed_sum_u"]).abs()<1e-10).all():
        raise AssertionError(f"Cumulative recurrence failed for {name}.")
    out.to_csv(OUT/f"element_inheritance_nuclear_track_{name}.csv",index=False,na_rep="NA",encoding="utf-8-sig")
    return out,selected

def choose_most_abundant(c):
    c=c[c["natural_abundance_pct"].notna()].copy()
    if c.empty: return None
    return c.sort_values(["natural_abundance_pct","binding_energy_per_nucleon_MeV","A"],
                         ascending=[False,False,True],kind="mergesort").iloc[0]

def choose_most_stable(c):
    c=c[c["is_stable"]].copy()
    if c.empty: return None
    # Operational tie-break among stable nuclides: highest BE/A, then abundance, then lower A.
    return c.sort_values(["binding_energy_per_nucleon_MeV","natural_abundance_pct","A"],
                         ascending=[False,False,True],kind="mergesort").iloc[0]

def choose_longest_lived_radioactive(c):
    c=c[(~c["is_stable"]) & c["half_life_seconds"].notna() &
        c["half_life_seconds"].gt(0) & c["half_life_seconds"].lt(math.inf)].copy()
    if c.empty: return None
    return c.sort_values(["half_life_seconds","binding_energy_per_nucleon_MeV","A"],
                         ascending=[False,False,True],kind="mergesort").iloc[0]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    box=run_box_loss_test()
    isotopes=load_isotope_table()
    isotopes.to_csv(OUT/"element_inheritance_nuclear_all_isotopes.csv",index=False,na_rep="NA",encoding="utf-8-sig")
    selectors={"most_abundant_natural":choose_most_abundant,
               "most_stable":choose_most_stable,
               "longest_lived_radioactive":choose_longest_lived_radioactive}
    summaries=[]
    meanings={"most_abundant_natural":"largest NUBASE2020 IS= natural abundance where published",
              "most_stable":"stable nuclide with highest AME2020 BE/A; abundance then lower A as tie-break",
              "longest_lived_radioactive":"radioactive ground-state nuclide with greatest finite NUBASE2020 half-life"}
    for name,selector in selectors.items():
        result,count=write_track(name,isotopes,selector)
        summaries.append({"track":name,"elements_with_selected_isotope":count,
                          "elements_without_selection":118-count,
                          "final_partial_cumulative_defect_u":float(result["cumulative_observed_sum_u"].iloc[-1]),
                          "meaning":meanings[name]})
    pd.DataFrame(summaries).to_csv(OUT/"element_inheritance_nuclear_track_summary.csv",index=False,na_rep="NA",encoding="utf-8-sig")
    report=["# اختبارات الوراثة التراكمية بين العناصر — H إلى Og","",
      "## الفصل المنهجي",
      "- اختبار فاقد الصندوق مستقل عن اختبار عيب الكتلة النووي.",
      "- الرصيد الموروث عند Z هو مجموع الإضافات المرصودة للعناصر السابقة، ثم تضاف إضافة Z.",
      "- لا تُستخدم فروق عنصرين متجاورين بديلاً عن الرصيد الموروث.","",
      "## اختبار فاقد الصندوق",
      f"- عدد العناصر: {len(box)} (Z=1..118).",
      "- مصدر الكتل: PROJECTS/triangle-framework/6.5.0/elements_input_118.csv؛ حُفظ مصدر الكتلة وجودة البيانات لكل عنصر.",
      "- الثابت 0.016 u؛ n=floor(log2(M/0.016))، L=0.016×2^n، U=2L، d_box=U−M.",
      "- التراكم: R_box(Z)=R_box(Z−1)+d_box(Z).",
      f"- مجموع الفاقد التراكمي عند Og: {float(box['cumulative_box_loss_u'].iloc[-1]):.12f} u.","",
      "## عيب الكتلة النووي — جميع النظائر",
      f"- عدد سجلات النظائر المطابقة: {len(isotopes)}؛ عدد العناصر الممثلة: {isotopes['Z'].nunique()}.",
      "- عيب كل نظير محفوظ منفرداً؛ لا تُجمع نظائر العنصر الواحد في قيمة واحدة.",
      "- عيب الكتلة مشتق من طاقة الربط المنشورة في AME2020، وليس قياساً مستقلاً عنها.","",
      "## المسارات التمثيلية الثلاثة"]
    for x in summaries:
        report.append(f"- {x['track']}: اختيار موثق لـ {x['elements_with_selected_isotope']} عنصراً، وNA لـ {x['elements_without_selection']}؛ الرصيد الجزئي عند Og {x['final_partial_cumulative_defect_u']:.12f} u. القاعدة: {x['meaning']}.")
    report += ["","## قيد قراءة التراكم",
      "- عند غياب نظير مؤهل لا تُخترع قيمة ولا يُستعاض عن قاعدة المسار بقاعدة أخرى؛ يحمل الرصيد الجزئي السابق ويُعلّم العنصر بأنه بلا اختيار.",
      "- لذلك cumulative_observed_sum هو مجموع جزئي للعناصر ذات الاختيار، وليس مجموعاً كاملاً لـ118 إضافة إلا إذا كانت كلها ممثلة.",
      "- ازدياد مجموع إضافات موجبة نتيجة حسابية للجمع؛ المهم أيضاً دراسة الإضافة الجديدة ومعدل تغيرها.",
      "- النتائج لا تثبت قانوناً فيزيائياً عاماً أو علاقة سببية.","",
      "## الملفات الناتجة",
      "- element_inheritance_box_loss_118.csv",
      "- element_inheritance_nuclear_all_isotopes.csv",
      "- element_inheritance_nuclear_track_most_abundant_natural.csv",
      "- element_inheritance_nuclear_track_most_stable.csv",
      "- element_inheritance_nuclear_track_longest_lived_radioactive.csv",
      "- element_inheritance_nuclear_track_summary.csv",
      "- report_ar_element_inheritance.md"]
    (OUT/"report_ar_element_inheritance.md").write_text("\\n".join(report)+"\\n",encoding="utf-8")
    print("\\n".join(report))
    print("ELEMENT INHERITANCE TESTS PASSED")

if __name__=="__main__":
    main()
