import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ═══════════ CONSTANTS ═══════════
const ELEMENTS = {
  ABC: { name:'النار',  icon:'🔥', hex:'#ff6b35', three:0xff6b35 },
  ABD: { name:'الهواء', icon:'💨', hex:'#a8d8ff', three:0xa8d8ff },
  ACD: { name:'الماء',  icon:'💧', hex:'#3b82f6', three:0x3b82f6 },
  BCD: { name:'التراب', icon:'🌍', hex:'#84cc16', three:0x84cc16 }
};
const FACE_VERTS = { ABC:['A','B','C'], ABD:['A','B','D'], ACD:['A','C','D'], BCD:['B','C','D'] };
const EDGE_FACES = { AB:['ABC','ABD'], AC:['ABC','ACD'], AD:['ABD','ACD'],
                     BC:['ABC','BCD'], BD:['ABD','BCD'], CD:['ACD','BCD'] };
const edgeKey = (a,b) => [a,b].sort().join('');
const TOL = 0.02;
const ANG_TOL = 0.5;

// ═══════════ STATE ═══════════
const state = {
  faces: {},
  selected: 'ABC',
  built: false,
  scene:null, camera:null, renderer:null, controls:null,
  group:null, faceMeshes:{}, incenterMeshes:{}
};
for (const f of Object.keys(FACE_VERTS)) {
  const [v1,v2,v3] = FACE_VERTS[f];
  state.faces[f] = {
    angles: { [v1]:null, [v2]:null, [v3]:null },
    sides:  { [edgeKey(v1,v2)]:null, [edgeKey(v2,v3)]:null, [edgeKey(v3,v1)]:null },
    result: null
  };
}

// ═══════════ GEOMETRY ═══════════
function solveTriangle(anglesIn, sidesIn, verts) {
  const [v1,v2,v3] = verts;
  const angles = { ...anglesIn };
  const sides = { ...sidesIn };
  const errs = [];
  const opposite = {
    [edgeKey(v1,v2)]: v3,
    [edgeKey(v2,v3)]: v1,
    [edgeKey(v3,v1)]: v2
  };
  const knownAng = Object.entries(angles).filter(([,v])=>v!=null && v>0);
  const knownSide = Object.entries(sides).filter(([,v])=>v!=null && v>0);

  if (knownAng.length === 2) {
    const sum = knownAng[0][1] + knownAng[1][1];
    if (sum >= 180 - ANG_TOL) return { errors:['مجموع الزاويتين يجب أن يكون أقل من 180°'] };
    const third = verts.find(k => k !== knownAng[0][0] && k !== knownAng[1][0]);
    angles[third] = 180 - sum;
  } else if (knownAng.length === 3) {
    const sum = verts.reduce((a,k)=>a+angles[k],0);
    if (Math.abs(sum - 180) > ANG_TOL)
      return { errors:[`مجموع الزوايا = ${sum.toFixed(1)}° (يجب أن يكون 180°)`] };
  } else if (knownSide.length === 3) {
    const [s12,s23,s31] = [edgeKey(v1,v2),edgeKey(v2,v3),edgeKey(v3,v1)];
    const a=sides[s12], b=sides[s23], c=sides[s31];
    if (a+b<=c+TOL || b+c<=a+TOL || c+a<=b+TOL)
      return { errors:['متباينة المثلث غير محققة في الأضلاع'] };
    angles[v1] = Math.acos((a*a+c*c-b*b)/(2*a*c))*180/Math.PI;
    angles[v2] = Math.acos((a*a+b*b-c*c)/(2*a*b))*180/Math.PI;
    angles[v3] = 180-angles[v1]-angles[v2];
  } else {
    return { errors:['أدخل زاويتين أو ثلاثة أضلاع'] };
  }

  const ks = knownSide.map(([side,val]) => ({
    side, k: val / Math.sin(angles[opposite[side]]*Math.PI/180)
  }));
  if (!ks.length) return { errors:['أدخل ضلعاً واحداً على الأقل لتحديد مقياس المثلث'] };
  if (ks.length >= 2) {
    const kAvg = ks.reduce((a,x)=>a+x.k,0)/ks.length;
    for (const x of ks) if (Math.abs(x.k-kAvg)/kAvg > TOL)
      return { errors:[`الضلع ${x.side} غير متوافق مع الزوايا (قانون الجيوب)`] };
  }
  const K = ks.reduce((a,x)=>a+x.k,0)/ks.length;
  for (const side of [edgeKey(v1,v2),edgeKey(v2,v3),edgeKey(v3,v1)]) {
    if (sides[side] == null || sides[side] <= 0)
      sides[side] = K * Math.sin(angles[opposite[side]]*Math.PI/180);
  }
  const [a,b,c] = [sides[edgeKey(v1,v2)],sides[edgeKey(v2,v3)],sides[edgeKey(v3,v1)]];
  if (a+b<=c+TOL || b+c<=a+TOL || c+a<=b+TOL)
    return { errors:['متباينة المثلث غير محققة'] };

  const subAngles = verts.map(v => ({
    label:'عند الرأس '+v, value:90+angles[v]/2, vertex:v
  }));
  return { angles, sides, subAngles, errors:[], valid:true };
}
function placeTetrahedron(edges) {
  const { AB, AC, AD, BC, BD, CD } = edges;
  if (![AB,AC,AD,BC,BD,CD].every(v => v>0)) return null;
  const Ax=0,Ay=0,Az=0;
  const Bx=AB,By=0,Bz=0;
  const Cx=(AC*AC+AB*AB-BC*BC)/(2*AB);
  const CySq=AC*AC-Cx*Cx;
  if (CySq <= 0) return null;
  const Cy=Math.sqrt(CySq), Cz=0;
  const Dx=(AD*AD+AB*AB-BD*BD)/(2*AB);
  const Dy=(AD*AD-CD*CD+Cx*Cx+Cy*Cy-2*Dx*Cx)/(2*Cy);
  const DzSq=AD*AD-Dx*Dx-Dy*Dy;
  if (DzSq <= TOL) return null;
  const Dz=Math.sqrt(DzSq);
  return { A:[Ax,Ay,Az], B:[Bx,By,Bz], C:[Cx,Cy,Cz], D:[Dx,Dy,Dz] };
}

function incenter3D(p1, p2, p3, sOppP1, sOppP2, sOppP3) {
  const sum = sOppP1+sOppP2+sOppP3;
  return [
    (p1[0]*sOppP1 + p2[0]*sOppP2 + p3[0]*sOppP3)/sum,
    (p1[1]*sOppP1 + p2[1]*sOppP2 + p3[1]*sOppP3)/sum,
    (p1[2]*sOppP1 + p2[2]*sOppP2 + p3[2]*sOppP3)/sum
  ];
}

// ═══════════ UI: FACE PANEL ═══════════
function renderPanel() {
  const f = state.selected;
  const data = state.faces[f];
  const el = ELEMENTS[f];
  const [v1,v2,v3] = FACE_VERTS[f];
  const panel = document.getElementById('panel');

  const angleRows = [v1,v2,v3].map(v => {
    const val = data.angles[v];
    const cls = val!=null && data.result && !data.result.valid ? 'invalid' : '';
    const computed = data.result && data.result.angles && data._computedAngles?.includes(v) ? 'computed' : '';
    return `<div class="row">
      <label>∠${v}</label>
      <input type="number" inputmode="decimal" data-kind="angle" data-key="${v}"
        value="${val??''}" placeholder="—" class="${computed}">
      <span class="unit">°</span>
    </div>`;
  }).join('');

  const sideRows = [edgeKey(v1,v2), edgeKey(v2,v3), edgeKey(v3,v1)].map(s => {
    const val = data.sides[s];
    const computed = data.result && data._computedSides?.includes(s) ? 'computed' : '';
    return `<div class="row">
      <label>${s}</label>
      <input type="number" inputmode="decimal" data-kind="side" data-key="${s}"
        value="${val??''}" placeholder="—" class="${computed}">
    </div>`;
  }).join('');

  let statusHtml = '';
  if (data.result) {
    if (data.result.valid) {
      statusHtml = `<div id="status" class="show ok">✓ الوجه صحيح</div>`;
    } else {
      statusHtml = `<div id="status" class="show err">✗ ${data.result.errors.join(' • ')}</div>`;
    }
  }

  panel.innerHTML = `
    <h3 style="color:${el.hex}">${el.icon} الوجه ${f} — ${el.name}</h3>
    <h3>الزوايا</h3>${angleRows}
    <h3>الأضلاع</h3>${sideRows}
    ${statusHtml}
  `;

  panel.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', onInput);
  });
}

function onInput(e) {
  const inp = e.target;
  const f = state.selected;
  const kind = inp.dataset.kind, key = inp.dataset.key;
  const v = inp.value === '' ? null : parseFloat(inp.value);
  if (v != null && (isNaN(v) || v <= 0)) { inp.value=''; return; }
  state.faces[f][kind === 'angle' ? 'angles' : 'sides'][key] = v;
  state.faces[f].result = null;
  state.faces[f]._computedAngles = null;
  state.faces[f]._computedSides = null;
  updateTabs();
}

// ═══════════ VALIDATE / BUILD ═══════════
function validateCurrent() {
  const f = state.selected;
  const data = state.faces[f];
  const anglesIn = data.angles;
  const sidesIn = data.sides;
  const knownA = Object.entries(anglesIn).filter(([,v])=>v!=null&&v>0);
  const knownS = Object.entries(sidesIn).filter(([,v])=>v!=null&&v>0);
  const res = solveTriangle(anglesIn, sidesIn, FACE_VERTS[f]);
  if (res.valid) {
    // Mark computed fields
    data._computedAngles = ['A','B','C'].filter(k => anglesIn[k]==null);
    data._computedSides = [edgeKey(...FACE_VERTS[f].slice(0,2)), edgeKey(...FACE_VERTS[f].slice(1,3)), edgeKey(FACE_VERTS[f][2],FACE_VERTS[f][0])].filter(k => sidesIn[k]==null);
    data.result = res;
    // Fill UI fields with computed values
    for (const k of data._computedAngles) {
      data.angles[k] = res.angles[k];
    }
    for (const k of data._computedSides) {
      data.sides[k] = res.sides[k];
    }
  } else {
    data.result = res;
  }
  renderPanel();
  updateTabs();
  return res.valid;
}

function tryBuild() {
  // validate all faces
  const allValid = Object.keys(state.faces).every(f => {
    const wasSel = state.selected;
    state.selected = f;
    const ok = validateCurrent();
    state.selected = wasSel;
    return ok;
  });

  if (!allValid) {
    showToast('بعض الأوجه غير صحيحة. صححها أولاً.');
    return;
  }

  // collect edges
  const edges = {}, warnings = [];
  for (const [edge, flist] of Object.entries(EDGE_FACES)) {
    const vals = flist.map(f => state.faces[f].result?.sides?.[edge]).filter(v => v != null);
    if (vals.length === 0) { warnings.push(`الضلع ${edge} مفقود`); continue; }
    const avg = vals.reduce((s,x)=>s+x,0)/vals.length;
    if (vals.length === 2 && Math.abs(vals[0]-vals[1])/avg > TOL) {
      warnings.push(`الضلع ${edge}: تعارض بين ${flist[0]}(${vals[0].toFixed(2)}) و ${flist[1]}(${vals[1].toFixed(2)})`);
    }
    edges[edge] = avg;
  }

  const placed = placeTetrahedron(edges);
  if (!placed) {
    showToast('لا يمكن بناء الهرم: الأبعاد لا تحقق شروط الوجود في الفضاء');
    return;
  }

  state.built = true;
  renderScene(placed, edges);
  if (warnings.length) showToast(warnings[0]);
  renderPanel();
}

// ═══════════ THREE.JS SCENE ═══════════
function initScene() {
  const wrap = document.getElementById('canvas-wrap');
  const canvas = document.getElementById('scene');
  const W = wrap.clientWidth, H = wrap.clientHeight;

  state.renderer = new THREE.WebGLRenderer({ canvas, antialias:true, alpha:true });
  state.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  state.renderer.setSize(W, H, false);

  state.scene = new THREE.Scene();
  state.camera = new THREE.PerspectiveCamera(50, W/H, 0.1, 1000);
  state.camera.position.set(6, 5, 8);

  state.controls = new OrbitControls(state.camera, canvas);
  state.controls.enableDamping = true;
  state.controls.dampingFactor = 0.08;
  state.controls.minDistance = 3;
  state.controls.maxDistance = 40;

  state.scene.add(new THREE.AmbientLight(0xffffff, 0.8));
  const dl = new THREE.DirectionalLight(0xffffff, 0.5);
  dl.position.set(5, 10, 7);
  state.scene.add(dl);

  state.group = new THREE.Group();
  state.scene.add(state.group);

  const resize = () => {
    const w = wrap.clientWidth, h = wrap.clientHeight;
    state.renderer.setSize(w, h, false);
    state.camera.aspect = w/h;
    state.camera.updateProjectionMatrix();
  };
  window.addEventListener('resize', resize);
  new ResizeObserver(resize).observe(wrap);

  function animate() {
    requestAnimationFrame(animate);
    state.controls.update();
    state.renderer.render(state.scene, state.camera);
  }
  animate();
}

function clearGroup() {
  while (state.group.children.length) {
    const c = state.group.children.pop();
    c.geometry?.dispose?.();
    c.material?.dispose?.();
  }
  state.faceMeshes = {};
  state.incenterMeshes = {};
}

function makeTriangle(p1, p2, p3, color, opacity) {
  const g = new THREE.BufferGeometry();
  const v = new Float32Array([...p1, ...p2, ...p3]);
  g.setAttribute('position', new THREE.BufferAttribute(v, 3));
  g.computeVertexNormals();
  const m = new THREE.MeshBasicMaterial({
    color, transparent:true, opacity, side:THREE.DoubleSide, depthWrite:false
  });
  return new THREE.Mesh(g, m);
}

function renderScene(verts, edges) {
  clearGroup();
  const V = verts;

  // Center the tetrahedron
  const cx = (V.A[0]+V.B[0]+V.C[0]+V.D[0])/4;
  const cy = (V.A[1]+V.B[1]+V.C[1]+V.D[1])/4;
  const cz = (V.A[2]+V.B[2]+V.C[2]+V.D[2])/4;
  const p = {};
  for (const k of ['A','B','C','D']) p[k] = [V[k][0]-cx, V[k][1]-cy, V[k][2]-cz];

  // For each face: render sub-triangles + incenter + edges
  for (const [fname, fverts] of Object.entries(FACE_VERTS)) {
    const [v1,v2,v3] = fverts;
    const res = state.faces[fname].result;
    if (!res || !res.valid) continue;
    const s = res.sides;
    const baseColor = new THREE.Color(ELEMENTS[fname].three);
    const isSelected = fname === state.selected;

    // incenter
    const s1 = s[edgeKey(v2,v3)], s2 = s[edgeKey(v3,v1)], s3 = s[edgeKey(v1,v2)];
    const I = incenter3D(p[v1], p[v2], p[v3], s1, s2, s3);

    // sub-triangle colors (3 shades)
    const shades = [
      baseColor.clone().offsetHSL(0, 0, isSelected? 0.20 : 0.10),
      baseColor.clone(),
      baseColor.clone().offsetHSL(0, 0, isSelected? -0.10 : -0.20)
    ];
    const subOpacity = isSelected ? 0.55 : 0.30;

    const subTris = [
      [p[v1], p[v2], I], // I with side v1v2
      [p[v2], p[v3], I],
      [p[v3], p[v1], I]
    ];
    subTris.forEach((tri, i) => {
      const m = makeTriangle(tri[0], tri[1], tri[2], shades[i], subOpacity);
      state.group.add(m);
    });

    // outer face fill (very subtle)
    const outerFill = makeTriangle(p[v1], p[v2], p[v3], baseColor, isSelected ? 0.10 : 0.04);
    state.group.add(outerFill);

    // edges of this face
    const edgePts = [
      ...p[v1], ...p[v2],
      ...p[v2], ...p[v3],
      ...p[v3], ...p[v1]
    ];
    const eg = new THREE.BufferGeometry();
    eg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(edgePts), 3));
    const em = new THREE.LineBasicMaterial({ color:baseColor, transparent:true, opacity: isSelected?1:0.6 });
    state.group.add(new THREE.LineSegments(eg, em));

    // incenter sphere
    const sphereG = new THREE.SphereGeometry(0.06, 12, 12);
    const sphereM = new THREE.MeshBasicMaterial({ color:0xffffff });
    const sphere = new THREE.Mesh(sphereG, sphereM);
    sphere.position.set(I[0], I[1], I[2]);
    state.group.add(sphere);

    state.faceMeshes[fname] = outerFill;
    state.incenterMeshes[fname] = I;
  }

  // Frame camera nicely
  const maxR = Math.max(
    ...['A','B','C','D'].map(k => Math.hypot(p[k][0], p[k][1], p[k][2]))
  );
  state.camera.position.set(maxR*1.4, maxR*1.2, maxR*1.6);
  state.controls.target.set(0, 0, 0);
}

// ═══════════ TABS / TOAST / INFO ═══════════
function updateTabs() {
  document.querySelectorAll('.tab').forEach(t => {
    const f = t.dataset.face;
    t.classList.toggle('active', f === state.selected);
    t.classList.remove('ok','err');
    const r = state.faces[f].result;
    if (r) t.classList.add(r.valid ? 'ok' : 'err');
  });
}

function showToast(msg) {
  const t = document.getElementById('error-toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 4000);
}

function showInfo() {
  const f = state.selected;
  const data = state.faces[f];
  const res = data.result;
  const el = ELEMENTS[f];
  const body = document.getElementById('info-body');

  if (!res || !res.valid) {
    body.innerHTML = `<p style="color:var(--err)">${res?.errors?.join('<br>') || 'لم يُحسب الوجه بعد'}</p>`;
    document.getElementById('info-page').classList.add('open');
    return;
  }

  const baseColor = new THREE.Color(el.three);
  const shades = [
    '#'+baseColor.clone().offsetHSL(0,0,0.15).getHexString(),
    '#'+baseColor.clone().getHexString(),
    '#'+baseColor.clone().offsetHSL(0,0,-0.15).getHexString()
  ];
  const [v1,v2,v3] = FACE_VERTS[f];
  const subData = [
    { color: shades[0], label: `بين ${v1} و ${v2}`, value: 90 + res.angles[v3]/2 },
    { color: shades[1], label: `بين ${v2} و ${v3}`, value: 90 + res.angles[v1]/2 },
    { color: shades[2], label: `بين ${v3} و ${v1}`, value: 90 + res.angles[v2]/2 }
  ];
  const total = subData.reduce((s,x)=>s+x.value,0);

  body.innerHTML = `
    <div class="face-title" style="color:${el.hex}">${el.icon} ${f} — ${el.name}</div>
    <div class="data-grid">
      <div class="data-cell"><div class="k">∠A</div>${res.angles.A.toFixed(2)}°</div>
      <div class="data-cell"><div class="k">∠B</div>${res.angles.B.toFixed(2)}°</div>
      <div class="data-cell"><div class="k">∠C</div>${res.angles.C.toFixed(2)}°</div>
      <div class="data-cell"><div class="k">${v1}${v2}</div>${res.sides[edgeKey(v1,v2)].toFixed(3)}</div>
      <div class="data-cell"><div class="k">${v2}${v3}</div>${res.sides[edgeKey(v2,v3)].toFixed(3)}</div>
      <div class="data-cell"><div class="k">${v3}${v1}</div>${res.sides[edgeKey(v3,v1)].toFixed(3)}</div>
    </div>
    <div class="sub-angles">
      <div class="sub-title">الزوايا حول نقطة المنصفات</div>
      ${subData.map(s => `
        <div class="sub-row">
          <div class="sub-swatch" style="background:${s.color}"></div>
          <div class="sub-label">${s.label}</div>
          <div class="sub-value" style="color:${s.color}">${s.value.toFixed(1)}°</div>
        </div>`).join('')}
      <div class="sub-total"><span>المجموع</span><span>${total.toFixed(1)}°</span></div>
    </div>
  `;
  document.getElementById('info-page').classList.add('open');
}

// ═══════════ SAVE / LOAD ═══════════
function exportData() {
  const data = { version:1, faces:{} };
  for (const [f, d] of Object.entries(state.faces)) {
    data.faces[f] = { angles:{...d.angles}, sides:{...d.sides} };
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type:'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `elemental-lab-${Date.now()}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function importData(file) {
  const r = new FileReader();
  r.onload = e => {
    try {
      const data = JSON.parse(e.target.result);
      if (!data.faces) throw 0;
      for (const [f, d] of Object.entries(data.faces)) {
        if (!state.faces[f]) continue;
        state.faces[f].angles = { ...d.angles };
        state.faces[f].sides = { ...d.sides };
        state.faces[f].result = null;
      }
      state.built = false;
      renderPanel();
      updateTabs();
      clearGroup();
      showToast('تم الاستيراد بنجاح');
    } catch { showToast('ملف غير صالح'); }
  };
  r.readAsText(file);
}

// ═══════════ INIT ═══════════
function init() {
  initScene();
  renderPanel();
  updateTabs();

  document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => {
      state.selected = t.dataset.face;
      renderPanel();
      updateTabs();
      if (state.built) {
        // re-render to update brightness
        // (we keep last verts in state)
        if (state._lastVerts) renderScene(state._lastVerts.verts, state._lastVerts.edges);
      }
    });
  });

  document.getElementById('btn-validate').onclick = () => {
    const ok = validateCurrent();
    showToast(ok ? '✓ الوجه صحيح' : '✗ يوجد خطأ، راجع الرسالة');
  };
  document.getElementById('btn-build').onclick = tryBuild;
  document.getElementById('btn-info').onclick = showInfo;
  document.getElementById('btn-save').onclick = exportData;
  document.getElementById('btn-load').onclick = () => document.getElementById('file-input').click();
  document.getElementById('file-input').onchange = e => {
    if (e.target.files[0]) importData(e.target.files[0]);
    e.target.value = '';
  };
  document.getElementById('info-back').onclick = () =>
    document.getElementById('info-page').classList.remove('open');

  // PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(()=>{});
  }
}

// Track last built verts for re-render on tab switch
const _origRenderScene = renderScene;
renderScene = function(v, e) {
  state._lastVerts = { verts:v, edges:e };
  _origRenderScene(v, e);
};

init();