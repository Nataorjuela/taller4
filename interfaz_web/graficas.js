/* =====================================================================
   Mini-librería de gráficas en SVG (sin dependencias externas).
   Funciones: G.lineas, G.cajas, G.ruta, G.barrasH
   ===================================================================== */
const G = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const tip = () => document.getElementById("tooltip");

  function el(tag, attrs = {}, padre) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === undefined || v === null) continue;
      // Las variables CSS (var(--x)) solo funcionan como estilo, no como atributo SVG
      if (typeof v === "string" && v.includes("var(")) e.style.setProperty(k, v);
      else e.setAttribute(k, v);
    }
    if (padre) padre.appendChild(e);
    return e;
  }
  const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v)) ? "–"
    : Math.abs(v) >= 1e4 ? Math.round(v).toLocaleString("es-CO")
    : v.toLocaleString("es-CO", { maximumFractionDigits: d, minimumFractionDigits: 0 });

  // ---- transformaciones de eje ----
  const T = {
    lin: v => v,
    log: v => Math.log10(Math.max(v, 1e-12)),
    symlog: v => Math.sign(v) * Math.log10(1 + Math.abs(v)),
  };
  function escala(tipo, d0, d1, r0, r1) {
    const f = T[tipo] || T.lin, a = f(d0), b = f(d1);
    const s = v => r0 + (f(v) - a) / ((b - a) || 1) * (r1 - r0);
    s.inv = p => {
      const t = a + (p - r0) / ((r1 - r0) || 1) * (b - a);
      if (tipo === "log") return Math.pow(10, t);
      if (tipo === "symlog") return Math.sign(t) * (Math.pow(10, Math.abs(t)) - 1);
      return t;
    };
    return s;
  }
  function marcas(tipo, d0, d1, cuantas = 6) {
    if (tipo === "log") {
      const out = [];
      for (let e = Math.floor(Math.log10(d0)); e <= Math.ceil(Math.log10(d1)); e++) {
        for (const m of [1, 2, 5]) { const v = m * 10 ** e; if (v >= d0 * 0.999 && v <= d1 * 1.001) out.push(v); }
      }
      return out.length > 9 ? out.filter(v => Math.abs(Math.log10(v) % 1) < 1e-9) : out;
    }
    if (tipo === "symlog") {
      const out = [0];
      for (let v = 1; v <= d1 * 1.001; v *= 10) out.push(v);
      if (out.length < 4) { out.splice(1, 0, 0.5); out.push(2, 5); }
      return out.filter(v => v >= d0 && v <= d1 * 1.001).sort((a, b) => a - b);
    }
    const paso0 = (d1 - d0) / cuantas, mag = 10 ** Math.floor(Math.log10(paso0 || 1));
    const paso = [1, 2, 2.5, 5, 10].map(m => m * mag).find(p => p >= paso0) || mag;
    const out = [];
    for (let v = Math.ceil(d0 / paso) * paso; v <= d1 + 1e-9; v += paso) out.push(+v.toFixed(10));
    return out;
  }
  // Ancho real del contenedor: así el texto de la gráfica siempre se ve de 11-12 px
  const ancho = cont => Math.max(320, Math.round(cont.getBoundingClientRect().width || 760));
  const textoMarca = v => Math.abs(v) >= 1000 ? (v / 1000).toLocaleString("es-CO") + "k" : fmt(v, 3);

  function mostrarTip(ev, html) {
    const t = tip(); t.innerHTML = html; t.hidden = false;
    const w = t.offsetWidth, h = t.offsetHeight;
    let x = ev.clientX + 16, y = ev.clientY + 14;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - 16;
    if (y + h > window.innerHeight - 8) y = ev.clientY - h - 14;
    t.style.left = x + "px"; t.style.top = y + "px";
  }
  const ocultarTip = () => { tip().hidden = true; };

  function ejes(svg, sx, sy, o, W, H, m) {
    const g = el("g", { class: "eje" }, svg);
    for (const v of marcas(o.yTipo || "lin", o.yMin, o.yMax)) {
      const y = sy(v);
      el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, class: "linea-rejilla" }, g);
      const t = el("text", { x: m.l - 7, y: y + 4, "text-anchor": "end" }, g); t.textContent = textoMarca(v);
    }
    const xs = o.xMarcas || marcas(o.xTipo || "lin", o.xMin, o.xMax);
    for (const v of xs) {
      const x = sx(v);
      el("line", { x1: x, x2: x, y1: m.t, y2: H - m.b, class: "linea-rejilla" }, g);
      const t = el("text", { x, y: H - m.b + 16, "text-anchor": "middle" }, g); t.textContent = textoMarca(v);
    }
    el("line", { x1: m.l, x2: W - m.r, y1: H - m.b, y2: H - m.b, class: "linea-eje" }, g);
    if (o.xEtiqueta) { const t = el("text", { x: (m.l + W - m.r) / 2, y: H - 6, "text-anchor": "middle", class: "titulo-eje" }, g); t.textContent = o.xEtiqueta; }
    if (o.yEtiqueta) { const t = el("text", { x: -(m.t + H - m.b) / 2, y: 14, transform: "rotate(-90)", "text-anchor": "middle", class: "titulo-eje" }, g); t.textContent = o.yEtiqueta; }
  }

  /* ------------------------------------------------------------------
     G.lineas(contenedor, {series:[{nombre,color,x,y,lo,hi,escalon,puntos,grosor}],
       xTipo, yTipo, xEtiqueta, yEtiqueta, refs:[{y,texto}], alto, marcaX, unidadY})
     ------------------------------------------------------------------ */
  function lineas(cont, o) {
    cont.innerHTML = ""; cont.classList.add("grafica");
    const W = ancho(cont), H = o.alto || 380, m = { l: 62, r: o.margenDer || 22, t: 16, b: 48 };
    const series = o.series.filter(s => s.x && s.x.length);
    if (!series.length) { cont.innerHTML = '<div class="vacio">Sin datos para mostrar</div>'; return; }
    const todasX = series.flatMap(s => s.x), todasY = series.flatMap(s => [...s.y, ...(s.lo || []), ...(s.hi || [])]).filter(v => v !== null && !Number.isNaN(v));
    (o.refs || []).forEach(r => todasY.push(r.y));
    o.xMin = o.xMin ?? Math.min(...todasX); o.xMax = o.xMax ?? Math.max(...todasX);
    let yMin = o.yMin ?? Math.min(...todasY), yMax = o.yMax ?? Math.max(...todasY);
    if (o.yTipo === "symlog") yMin = Math.min(0, yMin);
    if (o.yTipo === "log") yMin = Math.max(yMin / 1.5, 1e-6);
    if (o.yTipo !== "log" && o.yTipo !== "symlog") { const pad = (yMax - yMin) * 0.06 || 1; yMin = o.yMin ?? (yMin - pad); yMax += pad; }
    else yMax *= 1.15;
    o.yMin = yMin; o.yMax = yMax;
    const sx = escala(o.xTipo || "lin", o.xMin, o.xMax, m.l, W - m.r);
    const sy = escala(o.yTipo || "lin", yMin, yMax, H - m.b, m.t);
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" }, cont);
    ejes(svg, sx, sy, o, W, H, m);
    for (const r of o.refs || []) {
      el("line", { x1: m.l, x2: W - m.r, y1: sy(r.y), y2: sy(r.y), class: "ref" }, svg);
      if (r.texto) { const t = el("text", { x: W - m.r - 4, y: sy(r.y) - 5, "text-anchor": "end" }, svg); t.textContent = r.texto; }
    }
    const clip = "c" + Math.random().toString(36).slice(2);
    const cp = el("clipPath", { id: clip }, el("defs", {}, svg));
    el("rect", { x: m.l, y: m.t - 2, width: W - m.l - m.r, height: H - m.t - m.b + 4 }, cp);
    const capa = el("g", { "clip-path": `url(#${clip})` }, svg);
    for (const s of series) {
      if (s.lo && s.hi) {
        let d = s.x.map((x, i) => `${i ? "L" : "M"}${sx(x)},${sy(s.hi[i])}`).join("");
        d += s.x.slice().reverse().map((x, i) => `L${sx(x)},${sy(s.lo[s.x.length - 1 - i])}`).join("") + "Z";
        el("path", { d, fill: s.color, opacity: 0.14 }, capa);
      }
      let d = "";
      s.x.forEach((x, i) => {
        const X = sx(x), Y = sy(s.y[i]);
        if (i === 0) d = `M${X},${Y}`;
        else if (s.escalon) d += `H${X}V${Y}`;
        else d += `L${X},${Y}`;
      });
      if (s.escalon && s.xFin) d += `H${sx(s.xFin)}`;
      el("path", { d, fill: "none", stroke: s.color, "stroke-width": s.grosor || 2.2, "stroke-linejoin": "round", "stroke-dasharray": s.guiones || null }, capa);
      if (s.puntos) s.x.forEach((x, i) => el("circle", { cx: sx(x), cy: sy(s.y[i]), r: 5, fill: s.color, stroke: "var(--panel)", "stroke-width": 2 }, svg));
    }
    // Etiquetas al final de cada línea, separadas para que no se monten
    const finales = series.filter(s => s.etiquetaFinal).map(s => ({ s, y: sy(s.y[s.y.length - 1]) })).sort((a, b) => a.y - b.y);
    for (let i = 1; i < finales.length; i++) if (finales[i].y - finales[i - 1].y < 13) finales[i].y = finales[i - 1].y + 13;
    finales.forEach(({ s, y }) => { const t = el("text", { x: sx(s.x[s.x.length - 1]) + 9, y: y + 4, "font-weight": 600 }, svg); t.textContent = s.nombre; });
    // marcador externo (animación)
    const marca = el("g", { visibility: "hidden" }, svg);
    const ml = el("line", { y1: m.t, y2: H - m.b, stroke: "var(--tinta)", "stroke-width": 1.2, "stroke-dasharray": "3 3" }, marca);
    const mc = el("circle", { r: 6, fill: "var(--panel)", stroke: "var(--tinta)", "stroke-width": 2.5 }, marca);
    cont._marcar = (x, y) => {
      if (x === null) { marca.setAttribute("visibility", "hidden"); return; }
      marca.setAttribute("visibility", "visible");
      ml.setAttribute("x1", sx(x)); ml.setAttribute("x2", sx(x)); mc.setAttribute("cx", sx(x)); mc.setAttribute("cy", sy(y));
    };
    // interacción: cruz + tooltip
    const cruz = el("line", { y1: m.t, y2: H - m.b, stroke: "var(--tinta-3)", "stroke-width": 1, visibility: "hidden" }, svg);
    const puntosHover = series.map(s => el("circle", { r: 4.5, fill: s.color, stroke: "var(--panel)", "stroke-width": 2, visibility: "hidden" }, svg));
    const zona = el("rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" }, svg);
    zona.addEventListener("mousemove", ev => {
      const r = svg.getBoundingClientRect();
      const px = (ev.clientX - r.left) * W / r.width;
      const xv = sx.inv(px);
      let filasTip = [], xMostrar = null;
      series.forEach((s, k) => {
        let i = 0;
        if (s.escalon) { while (i + 1 < s.x.length && s.x[i + 1] <= xv) i++; }
        else { let best = Infinity; s.x.forEach((x, j) => { const dd = Math.abs(sx(x) - px); if (dd < best) { best = dd; i = j; } }); }
        const xx = s.escalon ? Math.min(Math.max(xv, s.x[0]), s.xFin || s.x[s.x.length - 1]) : s.x[i];
        xMostrar = xMostrar ?? xx;
        puntosHover[k].setAttribute("cx", sx(xx)); puntosHover[k].setAttribute("cy", sy(s.y[i]));
        puntosHover[k].setAttribute("visibility", "visible");
        filasTip.push({ n: s.nombre, c: s.color, v: s.y[i] });
      });
      cruz.setAttribute("x1", sx(xMostrar)); cruz.setAttribute("x2", sx(xMostrar)); cruz.setAttribute("visibility", "visible");
      filasTip.sort((a, b) => a.v - b.v);
      mostrarTip(ev, `<div style="margin-bottom:4px;color:var(--tinta-2)">${o.xEtiquetaCorta || o.xEtiqueta || "x"}: <b>${fmt(xMostrar, 1)}</b></div>` +
        filasTip.map(f => `<div class="fila-t"><span><i class="punto" style="--c:${f.c}"></i>${f.n}</span><b>${fmt(f.v, 2)}${o.unidadY || ""}</b></div>`).join(""));
    });
    zona.addEventListener("mouseleave", () => { ocultarTip(); cruz.setAttribute("visibility", "hidden"); puntosHover.forEach(p => p.setAttribute("visibility", "hidden")); });
  }

  /* ------------------------------------------------------------------
     G.cajas(contenedor, {grupos:[{nombre,color,min,q1,mediana,q3,max,atipicos,media}], yTipo, yEtiqueta, refs})
     ------------------------------------------------------------------ */
  function cajas(cont, o) {
    cont.innerHTML = ""; cont.classList.add("grafica");
    const W = ancho(cont), H = o.alto || 380, m = { l: 62, r: 16, t: 16, b: 40 };
    const gr = o.grupos;
    if (!gr.length) { cont.innerHTML = '<div class="vacio">Sin datos</div>'; return; }
    const vals = gr.flatMap(g => [g.min, g.max, ...(g.atipicos || [])]);
    (o.refs || []).forEach(r => vals.push(r.y));
    o.yMin = o.yTipo === "symlog" ? 0 : Math.min(...vals); o.yMax = Math.max(...vals) * 1.15;
    const banda = (W - m.l - m.r) / gr.length;
    o.xMin = 0; o.xMax = gr.length; o.xMarcas = [];
    const sx = i => m.l + banda * (i + 0.5);
    const sy = escala(o.yTipo || "lin", o.yMin, o.yMax, H - m.b, m.t);
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}` }, cont);
    ejes(svg, escala("lin", 0, 1, m.l, W - m.r), sy, o, W, H, m);
    for (const r of o.refs || []) {
      el("line", { x1: m.l, x2: W - m.r, y1: sy(r.y), y2: sy(r.y), class: "ref" }, svg);
      if (r.texto) { const t = el("text", { x: W - m.r - 4, y: sy(r.y) - 5, "text-anchor": "end" }, svg); t.textContent = r.texto; }
    }
    gr.forEach((g, i) => {
      const x = sx(i), w = Math.min(64, banda * 0.5);
      const grp = el("g", {}, svg);
      el("line", { x1: x, x2: x, y1: sy(g.min), y2: sy(g.q1), stroke: "var(--tinta-2)", "stroke-width": 1.5 }, grp);
      el("line", { x1: x, x2: x, y1: sy(g.q3), y2: sy(g.max), stroke: "var(--tinta-2)", "stroke-width": 1.5 }, grp);
      for (const v of [g.min, g.max]) el("line", { x1: x - w / 4, x2: x + w / 4, y1: sy(v), y2: sy(v), stroke: "var(--tinta-2)", "stroke-width": 1.5 }, grp);
      const alto = Math.max(2, sy(g.q1) - sy(g.q3));
      el("rect", { x: x - w / 2, y: sy(g.q3), width: w, height: alto, rx: 4, fill: g.color, "fill-opacity": 0.78, stroke: g.color, "stroke-width": 1.5 }, grp);
      el("line", { x1: x - w / 2, x2: x + w / 2, y1: sy(g.mediana), y2: sy(g.mediana), stroke: "var(--tinta)", "stroke-width": 2.5 }, grp);
      (g.atipicos || []).forEach(v => el("circle", { cx: x, cy: sy(v), r: 2.8, fill: "none", stroke: "var(--tinta-2)" }, grp));
      const t = el("text", { x, y: H - m.b + 18, "text-anchor": "middle", "font-weight": 700 }, svg); t.textContent = g.nombre;
      const z = el("rect", { x: x - banda / 2, y: m.t, width: banda, height: H - m.t - m.b, fill: "transparent" }, svg);
      z.addEventListener("mousemove", ev => mostrarTip(ev,
        `<b><i class="punto" style="--c:${g.color}"></i>${g.nombre}</b><br>máximo*: ${fmt(g.max)}${o.unidadY || ""}<br>Q3: ${fmt(g.q3)}<br><b>mediana: ${fmt(g.mediana)}</b><br>Q1: ${fmt(g.q1)}<br>mínimo*: ${fmt(g.min)}<br>media: ${fmt(g.media)}<br><span style="color:var(--tinta-3)">*sin atípicos (1,5·RIC)</span>`));
      z.addEventListener("mouseleave", ocultarTip);
    });
  }

  /* ------------------------------------------------------------------
     G.ruta(contenedor, {ciudades:[[x,y]], ruta:[...], color, alto, etiquetas})
     Devuelve una función actualizar(ruta) para animar.
     ------------------------------------------------------------------ */
  function ruta(cont, o) {
    cont.innerHTML = ""; cont.classList.add("grafica");
    const S = o.tam || 420, pad = 16;
    const xs = o.ciudades.map(c => c[0]), ys = o.ciudades.map(c => c[1]);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const k = (S - 2 * pad) / Math.max(x1 - x0, y1 - y0, 1e-9);
    const X = x => pad + (x - x0) * k, Y = y => S - pad - (y - y0) * k;
    const svg = el("svg", { viewBox: `0 0 ${S} ${S}` }, cont);
    el("rect", { x: 0, y: 0, width: S, height: S, rx: 12, fill: "var(--panel-2)" }, svg);
    const camino = el("path", { fill: "none", stroke: o.color, "stroke-width": o.grosor || 2.4, "stroke-linejoin": "round" }, svg);
    const inicio = el("circle", { r: 7, class: "inicio", visibility: "hidden" }, svg);
    o.ciudades.forEach((c, i) => {
      const p = el("circle", { cx: X(c[0]), cy: Y(c[1]), r: o.radio || 4.2, class: "ciudad" }, svg);
      p.addEventListener("mousemove", ev => mostrarTip(ev, `Ciudad <b>${i}</b><br>(${fmt(c[0], 1)}, ${fmt(c[1], 1)})`));
      p.addEventListener("mouseleave", ocultarTip);
    });
    const actualizar = r => {
      if (!r || !r.length) return;
      const d = r.map((c, i) => `${i ? "L" : "M"}${X(o.ciudades[c][0])},${Y(o.ciudades[c][1])}`).join("") + "Z";
      camino.setAttribute("d", d);
      inicio.setAttribute("cx", X(o.ciudades[r[0]][0])); inicio.setAttribute("cy", Y(o.ciudades[r[0]][1]));
      inicio.setAttribute("visibility", "visible");
    };
    actualizar(o.ruta);
    return actualizar;
  }

  /* ------------------------------------------------------------------
     G.barrasH(contenedor, {items:[{nombre,color,valor,texto}], max, unidad})
     ------------------------------------------------------------------ */
  function barrasH(cont, o) {
    cont.innerHTML = ""; cont.classList.add("grafica");
    const W = ancho(cont), fila = 34, m = { l: 90, r: 70, t: 8 }, H = m.t * 2 + fila * o.items.length;
    const max = o.max || Math.max(...o.items.map(i => i.valor));
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}` }, cont);
    o.items.forEach((it, i) => {
      const y = m.t + i * fila, w = (W - m.l - m.r) * it.valor / max;
      const t = el("text", { x: m.l - 10, y: y + fila / 2 + 4, "text-anchor": "end", "font-weight": 700 }, svg); t.textContent = it.nombre;
      el("rect", { x: m.l, y: y + 7, width: Math.max(2, w), height: fila - 14, rx: 5, fill: it.color }, svg);
      const v = el("text", { x: m.l + w + 8, y: y + fila / 2 + 4 }, svg); v.textContent = it.texto ?? fmt(it.valor);
    });
  }

  return { lineas, cajas, ruta, barrasH, fmt };
})();
