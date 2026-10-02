/* =====================================================================
   Interfaz gráfica del Taller 4 (frontend).
   Habla con el servidor Python (interfaz_grafica.py) por medio de /api/...
   ===================================================================== */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const f = G.fmt;
const ESTADO = {
  config: null, res: null, tab: "ejecutar",
  ej: { n: 50, inst: 0, otroN: 40, semAleatoria: 3, semilla: 7, presupuesto: null, memoria: true, alg: "SA", params: {} },
  ultimo: null, comparacion: null, corriendo: false,
  visibles: new Set(ORDEN), n4: 50, inst4: 0, n5: 100, nH: 100,
};
const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const color = a => cssVar(a === "ACO+2opt" ? "--c-ACO2" : "--c-" + a) || INFO[a].hex;
const varColor = a => a === "ACO+2opt" ? "var(--c-ACO2)" : `var(--c-${a})`;
const ptoAlg = a => `<i class="punto" style="--c:${varColor(a)}"></i>`;
const limpiarTextoRoto = raiz => {
  const pares = [
    ["Â·", "-"], ["â€¦", "..."], ["â€“", "-"], ["â€”", "-"], ["â€º", ">"],
    ["Ã¡", "a"], ["Ã©", "e"], ["Ã­", "i"], ["Ã³", "o"], ["Ãº", "u"], ["Ã±", "n"],
    ["Ã", "A"], ["Ã‰", "E"], ["Ã", "I"], ["Ã“", "O"], ["Ãš", "U"], ["Ã‘", "N"],
    ["Â¿", "¿"], ["Â¡", "¡"], ["Âº", "o"], ["Ï‡", "chi"], ["Ï€", "pi"],
    ["Î£", "sum"], ["Î”", "Delta"], ["Î±", "alpha"], ["â‰¤", "<="], ["â‰ˆ", "~"],
    ["âˆ’", "-"], ["â†’", "->"], ["â€œ", "\""], ["â€", "\""], ["â€™", "'"],
    ["â—", "inicio"], ["âœ“", "OK"], ["âœ—", "X"], ["â–¶", "Ejecutar"], ["âš–", "Comparar"],
    ["âšâš", "Pausa"], ["Ã—", "x"]
  ];
  const walker = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
  const nodos = [];
  while (walker.nextNode()) nodos.push(walker.currentNode);
  nodos.forEach(n => {
    let t = n.nodeValue;
    pares.forEach(([a, b]) => { t = t.split(a).join(b); });
    if (t !== n.nodeValue) n.nodeValue = t;
  });
};
const observarTexto = () => {
  const obs = new MutationObserver(muts => {
    if (muts.some(m => m.addedNodes.length || m.type === "characterData")) limpiarTextoRoto(document.body);
  });
  obs.observe(document.body, { childList: true, subtree: true, characterData: true });
  limpiarTextoRoto(document.body);
};
const pct = v => v === null || v === undefined ? "–" : f(v, 2) + " %";

const ganadorCalidad = n => {
  const filas = (ESTADO.res.rendimiento || []).filter(r => r.n === n);
  return filas.length ? filas.sort((a, b) => a["error_mediana_%"] - b["error_mediana_%"])[0].algoritmo : "ACO";
};
const ganadorRapidez = n => {
  const filas = (ESTADO.res.eficiencia || []).filter(r => r.n === n);
  return filas.length ? filas.sort((a, b) => a.tiempo_medio_s - b.tiempo_medio_s)[0].algoritmo : "HC";
};
const resumenAlgoritmo = a => `<p>${INFO[a].idea}</p><p class="respuesta">${INFO[a].simple}</p><p class="sub">${INFO[a].como}</p>`;

async function api(url, cuerpo) {
  const r = await fetch(url, cuerpo ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) } : {});
  const d = await r.json();
  if (!r.ok && d && d.error) throw new Error(d.error);
  return d;
}

/* ------------------------- navegación ------------------------- */
function irA(tab) {
  ESTADO.tab = tab;
  $$("#pestanas button").forEach(b => b.classList.toggle("activa", b.dataset.tab === tab));
  const pintar = { ejecutar: pintarEjecutar, diseno: pintarDiseno, eficiencia: pintarEficiencia,
    rendimiento: pintarRendimiento, conclusiones: pintarConclusiones, hibrido: pintarHibrido, teoria: pintarTeoria }[tab];
  window.scrollTo({ top: 0 });
  pintar();
  limpiarTextoRoto($("#contenido"));
}
$$("#pestanas button").forEach(b => b.addEventListener("click", () => irA(b.dataset.tab)));

function segmentado(valores, actual, alCambiar, etiqueta = v => v) {
  const d = document.createElement("div"); d.className = "segmentado";
  valores.forEach(v => {
    const b = document.createElement("button"); b.textContent = etiqueta(v);
    if (String(v) === String(actual)) b.classList.add("activo");
    b.onclick = () => alCambiar(v);
    d.appendChild(b);
  });
  return d;
}
function chips(cont, lista, alCambiar) {
  cont.innerHTML = ""; cont.className = "chips";
  lista.forEach(a => {
    const b = document.createElement("button");
    b.className = "chip" + (ESTADO.visibles.has(a) ? "" : " apagado");
    b.style.setProperty("--c", varColor(a));
    b.innerHTML = `<i></i>${a}`;
    b.onclick = () => { ESTADO.visibles.has(a) ? ESTADO.visibles.delete(a) : ESTADO.visibles.add(a); if (!ESTADO.visibles.size) ESTADO.visibles.add(a); alCambiar(); };
    cont.appendChild(b);
  });
}
const sinResultados = () => `<div class="tarjeta vacio">Todavía no hay resultados del experimento en la carpeta <code>resultados/</code>.<br>
  Ejecute <code>python ejecutar_experimentos.py</code> y luego <code>python experimentos/analizar_resultados.py</code>.</div>`;

/* =====================================================================
   PESTAÑA 1: EJECUTAR (interfaz común)
   ===================================================================== */
function presupuestoPorDefecto(n) {
  return ESTADO.config.config.presupuestos[String(n)] || Math.round(600 * n);
}
function nActual() { return ESTADO.ej.n === "otro" ? Number(ESTADO.ej.otroN) : Number(ESTADO.ej.n); }

function mejorarTextosEjecutar(algs, activo) {
  const intro = $(".intro");
  if (intro) {
    intro.classList.add("hero-app");
    intro.innerHTML = `<h2>Encuentra una ruta corta para visitar todas las ciudades</h2>
      <p>Elige el mapa, escoge un algoritmo y ejecutalo. Veras la ruta, cuanto tardo y que tan buena fue. Todo corre con el codigo real del taller.</p>
      <div class="pasos-rapidos"><span>1. Mapa</span><span>2. Algoritmo</span><span>3. Ejecutar</span><span>4. Comparar</span></div>`;
  }
  const tarjetas = $$("aside .tarjeta");
  if (tarjetas[0]) {
    tarjetas[0].classList.add("panel-control");
    tarjetas[0].querySelector("h3").textContent = "1. Mapa de ciudades";
    tarjetas[0].insertAdjacentHTML("afterbegin", `<p class="ayuda">Mas ciudades significa un reto mas dificil.</p>`);
  }
  const etiquetaN = $("#seg-n")?.previousElementSibling;
  if (etiquetaN) etiquetaN.textContent = "Numero de ciudades";
  const semilla = $("#in-semilla")?.previousElementSibling;
  if (semilla) semilla.textContent = "Semilla";
  const pres = $("#in-pres")?.previousElementSibling;
  if (pres) pres.textContent = "Intentos permitidos";
  const mem = $("#in-mem")?.closest("label");
  if (mem) mem.lastChild.textContent = " Medir memoria";
  if (tarjetas[1]) {
    tarjetas[1].classList.add("panel-control");
    tarjetas[1].querySelector("h3").textContent = "2. Algoritmo";
    tarjetas[1].insertAdjacentHTML("afterbegin", `<p class="ayuda">Selecciona una estrategia. La tarjeta marcada es la que se ejecutara.</p>`);
  }
  $$(".alg").forEach(b => {
    const a = b.dataset.alg;
    b.innerHTML = `<b>${a}</b><span>${INFO[a].nombre}</span><small>${INFO[a].familia}</small>${a === "ACO+2opt" ? '<span class="tag">opcional</span>' : ""}`;
  });
  if (tarjetas[2]) {
    tarjetas[2].classList.add("panel-control");
    tarjetas[2].querySelector("h3").textContent = `3. Opciones de ${activo}`;
  }
  const comparar = $("#btn-comparar");
  if (comparar) comparar.textContent = "Comparar los 5 algoritmos";
  $$("[id='btn-ejecutar']").slice(1).forEach(b => b.remove());
  $$("[id='btn-comparar']").slice(1).forEach(b => b.remove());
}

function mejorarTextosResultado() {
  const titulos = $$(".kpi .t");
  const detalles = $$(".kpi .d");
  [["Distancia final", "menor es mejor"], ["Cerca de la mejor", "contra la mejor conocida"], ["Cuanto mejoro", "frente a su primera ruta"], ["Mejor intento", "intentos usados"]]
    .forEach(([t, d], i) => {
      if (titulos[i]) titulos[i].textContent = t;
      if (detalles[i]) detalles[i].textContent = d;
    });
  const tarjetas = $$("#resultado .tarjeta");
  tarjetas.forEach(card => {
    const h3 = card.querySelector("h3");
    if (!h3) return;
    if (h3.textContent.includes("Curva")) h3.textContent = "Como fue mejorando";
    if (h3.textContent.includes("Verificaciones")) h3.textContent = "Comprobaciones automaticas";
  });
  const leyenda = $("#g-conv")?.nextElementSibling;
  if (leyenda) leyenda.textContent = "La linea baja cuando el algoritmo encuentra una ruta mejor. Si se queda plana, paso un rato sin mejorar.";
  const sum = $("details.json summary");
  if (sum) sum.textContent = "Ver datos tecnicos";
}

function pintarEjecutar() {
  const e = ESTADO.ej, cfg = ESTADO.config.config;
  if (!e.presupuesto) e.presupuesto = presupuestoPorDefecto(nActual());
  const algs = [...ORDEN, ...ESTADO.config.extra];
  $("#contenido").innerHTML = `
  <div class="intro"><h2>Punto 1 · Interfaz común: elija un algoritmo y ejecútelo</h2>
    <p>Todos los algoritmos se llaman igual: <code>optimizar(distancias, presupuesto, semilla, parámetros)</code> y devuelven la mejor ruta,
    su costo, el historial, las evaluaciones, el tiempo y la memoria. Aquí se ejecuta el código real de <code>src/</code>.</p></div>
  <div class="rejilla-lateral">
    <aside>
      <div class="tarjeta"><h3>1 · Instancia (mapa de ciudades)</h3>
        <label class="campo">Número de ciudades n</label><div id="seg-n"></div>
        <div id="campos-inst"></div>
        <div class="fila">
          <div><label class="campo">Semilla de la corrida</label><input type="number" id="in-semilla" value="${e.semilla}"></div>
          <div><label class="campo">Presupuesto (evaluaciones)</label><input type="number" id="in-pres" value="${e.presupuesto}" step="1000" min="100"></div>
        </div>
        <label class="check"><input type="checkbox" id="in-mem" ${e.memoria ? "checked" : ""}> Medir memoria con tracemalloc (un poco más lento)</label>
      </div>
      <div class="tarjeta"><h3>2 · Algoritmo</h3>
        <div class="algoritmos">${algs.map(a => `
          <button class="alg ${a === e.alg ? "activo" : ""}" data-alg="${a}" style="--c:${varColor(a)}">
            <b>${a}</b><span>${INFO[a].nombre}</span>${a === "ACO+2opt" ? '<span class="tag">opcional</span>' : ""}</button>`).join("")}</div>
        <div class="accion-ejecutar">
          <button class="boton boton-ejecutar" id="btn-ejecutar">Ejecutar ${e.alg}</button>
          <button class="boton secundario" id="btn-comparar">Comparar los 5 algoritmos</button>
        </div>
      </div>
      <div class="tarjeta"><h3>3 · Parámetros de ${e.alg}</h3><div id="params"></div>
        <button class="boton" id="btn-ejecutar">▶ Ejecutar ${e.alg}</button>
        <button class="boton secundario" id="btn-comparar">⚖ Comparar los 5 algoritmos en esta instancia</button>
      </div>
    </aside>
    <section id="resultado"></section>
  </div>`;

  mejorarTextosEjecutar(algs, e.alg);

  // n
  const selectorN = segmentado([...cfg.tamanos, "otro"], e.n, v => {
    e.n = v; e.presupuesto = presupuestoPorDefecto(nActual()); ESTADO.ultimo = null; ESTADO.comparacion = null; pintarEjecutar();
  }, v => v === "otro" ? "Otro" : v);
  selectorN.classList.add("selector-n");
  $("#seg-n").appendChild(selectorN);
  if (e.n === "otro") {
    $("#campos-inst").innerHTML = `<div class="fila">
      <div><label class="campo">n (5 a 300)</label><input type="number" id="in-otron" min="5" max="300" value="${e.otroN}"></div>
      <div><label class="campo">Semilla del mapa</label><input type="number" id="in-semmapa" value="${e.semAleatoria}"></div></div>`;
    $("#in-otron").onchange = ev => { e.otroN = Math.max(5, Math.min(300, +ev.target.value)); e.presupuesto = presupuestoPorDefecto(nActual()); $("#in-pres").value = e.presupuesto; };
    $("#in-semmapa").onchange = ev => { e.semAleatoria = +ev.target.value; };
  } else {
    $("#campos-inst").innerHTML = `<label class="campo">Instancia oficial (semilla pública)</label>
      <select id="in-inst">${cfg.semillas_publicas_instancias.map((s, i) => `<option value="${i}" ${i == e.inst ? "selected" : ""}>Instancia ${i} · semilla ${s}</option>`).join("")}</select>`;
    $("#in-inst").onchange = ev => { e.inst = +ev.target.value; ESTADO.ultimo = null; ESTADO.comparacion = null; mostrarVistaPrevia(); };
  }
  $("#in-semilla").onchange = ev => { e.semilla = +ev.target.value; };
  $("#in-pres").onchange = ev => { e.presupuesto = Math.max(100, +ev.target.value); };
  $("#in-mem").onchange = ev => { e.memoria = ev.target.checked; };
  $$(".alg").forEach(b => b.onclick = () => { e.alg = b.dataset.alg; e.params = {}; pintarEjecutar(); });

  // parámetros
  const base = cfg.parametros[e.alg] || {};
  $("#params").innerHTML = Object.entries(base).map(([k, v]) => `
    <label class="campo" title="${INFO[e.alg].params[k] || k}">${k} <span class="sub" style="font-weight:400">· ${INFO[e.alg].params[k] || ""}</span></label>
    <input type="number" step="any" data-p="${k}" value="${e.params[k] ?? (v ?? "")}" placeholder="${v === null ? "n (automático)" : ""}">`).join("")
    + `<p class="leyenda-rap">Valores por defecto = los elegidos en la fase piloto (configuracion.json).</p>`;
  $$("#params input").forEach(i => i.onchange = () => { e.params[i.dataset.p] = i.value === "" ? null : Number(i.value); });

  $("#btn-ejecutar").onclick = ejecutarUno;
  $("#btn-comparar").onclick = compararTodos;

  if (ESTADO.comparacion && ESTADO.comparacion.clave === claveInstancia()) pintarComparacion();
  else if (ESTADO.ultimo && ESTADO.ultimo.algoritmo === e.alg && ESTADO.ultimo.n === nActual()) pintarResultado(ESTADO.ultimo);
  else mostrarVistaPrevia();
}
const claveInstancia = () => `${nActual()}_${ESTADO.ej.n === "otro" ? "r" + ESTADO.ej.semAleatoria : ESTADO.ej.inst}_${ESTADO.ej.semilla}_${ESTADO.ej.presupuesto}`;

async function mostrarVistaPrevia() {
  const e = ESTADO.ej, a = e.alg, info = INFO[a];
  const r = $("#resultado");
  r.innerHTML = `
    <div class="tarjeta"><div class="cabeza"><h3>${ptoAlg(a)}${a} · ${info.nombre}</h3><span class="etiqueta">${info.familia}</span></div>
      <div class="explica" style="--c:${varColor(a)}"><h4>Como funciona</h4>${resumenAlgoritmo(a)}</div>
    </div>
    <div class="tarjeta"><div class="cabeza"><h3>Mapa de la instancia</h3><span class="sub" id="desc-inst"></span></div>
      <div style="max-width:520px;margin:auto" id="mapa-previo"><div class="vacio">…</div></div>
      <p class="sub" style="text-align:center">Pulse <b>▶ Ejecutar</b> para ver la ruta que encuentra ${a}, cómo mejora paso a paso y su curva de convergencia.</p>
    </div>`;
  if (e.n === "otro") { $("#mapa-previo").innerHTML = '<div class="vacio">Mapa aleatorio: se genera al ejecutar.</div>'; return; }
  const d = await api(`/api/instancia?n=${e.n}&instancia=${e.inst}`);
  $("#desc-inst").textContent = `n = ${e.n} · ${d.descripcion}` + (d.f_estrella ? ` · mejor ruta conocida f* = ${f(d.f_estrella)}` : "");
  G.ruta($("#mapa-previo"), { ciudades: d.ciudades, ruta: [], color: "transparent" });
}

function peticion(alg, params) {
  const e = ESTADO.ej;
  return { algoritmo: alg, n: nActual(), instancia: e.inst, usar_aleatoria: e.n === "otro", semilla_aleatoria: e.semAleatoria,
    semilla: e.semilla, presupuesto: e.presupuesto, medir_memoria: e.memoria, parametros: params || {} };
}

async function ejecutarUno() {
  if (ESTADO.corriendo) return;
  const e = ESTADO.ej, b = $("#btn-ejecutar");
  ESTADO.corriendo = true; b.disabled = true; b.innerHTML = `<span class="spinner"></span> Ejecutando ${e.alg}…`;
  try {
    const params = Object.fromEntries(Object.entries(e.params).filter(([, v]) => v !== undefined));
    const d = await api("/api/ejecutar", peticion(e.alg, params));
    ESTADO.ultimo = d; ESTADO.comparacion = null;
    pintarResultado(d);
  } catch (err) { alert("Error: " + err.message); }
  finally { ESTADO.corriendo = false; b.disabled = false; b.innerHTML = `▶ Ejecutar ${e.alg}`; }
}

let temporizador = null;
function pintarResultado(d) {
  const a = d.algoritmo, info = INFO[a], v = d.verificaciones;
  const mejora = d.costo_inicial ? 100 * (d.costo_inicial - d.mejor_costo) / d.costo_inicial : null;
  $("#resultado").innerHTML = `
    <div class="tarjeta" style="padding:14px 18px"><div class="cabeza" style="margin:0">
      <h3>${ptoAlg(a)}Resultado de ${a} · ${info.nombre}</h3>
      <span class="sub">n = ${d.n} · ${d.descripcion_instancia} · semilla ${d.semilla}</span></div></div>
    <div class="kpis">
      <div class="kpi"><div class="t">Mejor costo</div><div class="v">${f(d.mejor_costo)}</div><div class="d">longitud de la ruta</div></div>
      <div class="kpi"><div class="t">Error vs f*</div><div class="v">${d.error_pct === null ? "–" : pct(d.error_pct)}</div><div class="d">${d.f_estrella ? "f* = " + f(d.f_estrella) : "instancia sin referencia"}</div></div>
      <div class="kpi"><div class="t">Mejora</div><div class="v">${pct(mejora)}</div><div class="d">vs. primera ruta (${f(d.costo_inicial)})</div></div>
      <div class="kpi"><div class="t">Mejor hallada en</div><div class="v">${f(d.fe_mejor)}</div><div class="d">de ${f(d.evaluaciones)} evaluaciones</div></div>
      <div class="kpi"><div class="t">Tiempo</div><div class="v">${d.tiempo_s < 1 ? f(d.tiempo_s * 1000, 1) + " ms" : f(d.tiempo_s, 2) + " s"}</div><div class="d">sin tracemalloc</div></div>
      <div class="kpi"><div class="t">Memoria pico</div><div class="v">${d.memoria_mb === null ? "–" : f(d.memoria_mb, 3)}</div><div class="d">MB (tracemalloc)</div></div>
    </div>
    <div class="rejilla-2">
      <div class="tarjeta"><div class="cabeza"><h3>Ruta encontrada</h3><span class="sub">● = ciudad inicial</span></div>
        <div id="g-ruta" style="max-width:470px;margin:auto"></div>
        <div class="reproductor"><button id="btn-play" title="Reproducir">▶</button>
          <input type="range" id="rango" min="0" max="${d.fotos.length - 1}" value="${d.fotos.length - 1}"></div>
        <div class="estado-anim" id="estado-anim"></div>
      </div>
      <div class="tarjeta"><div class="cabeza"><h3>Curva de convergencia</h3><span class="sub">${d.mejoras} mejoras registradas</span></div>
        <div id="g-conv"></div>
        <p class="leyenda-rap">Mejor costo histórico frente a las evaluaciones (eje x logarítmico). La curva nunca sube: es la mejor ruta vista hasta ese momento.
        ${d.f_estrella ? "La línea discontinua es f*, la mejor ruta conocida de esta instancia en todo el experimento." : ""}</p>
      </div>
    </div>
    <div class="rejilla-2">
      <div class="tarjeta"><h3>Verificaciones del punto 1</h3>
        <ul class="verifs">
          ${[["ruta_valida", "La ruta visita cada ciudad una sola vez"], ["costo_coincide", "Costo reportado = costo recalculado"],
             ["presupuesto_exacto", "Gastó exactamente el presupuesto"], ["historial_no_empeora", "El historial nunca empeora"]]
            .map(([k, t]) => `<li><span class="${v[k] ? "ok" : "mal"}">${v[k] ? "✓" : "✗"}</span>${t}</li>`).join("")}
        </ul>
        <details class="json" style="margin-top:12px"><summary>Ver el diccionario que devolvió <code>optimizar()</code></summary><pre>${jsonCorto(d)}</pre></details>
      </div>
      <div class="tarjeta"><h3>¿Qué hizo ${a}?</h3>
        <div class="explica" style="--c:${varColor(a)}">${resumenAlgoritmo(a)}</div>
        <p class="sub">Parámetros usados: ${Object.entries(d.parametros).map(([k, x]) => `<code>${k}=${x ?? "n"}</code>`).join(" · ")}</p>
      </div>
    </div>`;

  mejorarTextosResultado();
  const actualizarRuta = G.ruta($("#g-ruta"), { ciudades: d.ciudades, ruta: d.mejor_ruta, color: color(a) });
  const xs = d.historial.map(h => h[0]), ys = d.historial.map(h => h[1]);
  G.lineas($("#g-conv"), {
    series: [{ nombre: a, color: color(a), x: xs, y: ys, escalon: true, xFin: d.evaluaciones }],
    xTipo: "log", xMin: 1, xMax: d.evaluaciones, xEtiqueta: "Evaluaciones de la función objetivo (FEs)", xEtiquetaCorta: "FEs",
    yEtiqueta: "Mejor costo histórico", refs: d.f_estrella ? [{ y: d.f_estrella, texto: "f* " + f(d.f_estrella) }] : [], alto: 400,
  });
  const conv = $("#g-conv"), rango = $("#rango"), est = $("#estado-anim");
  const mostrarFoto = i => {
    const [fe, c, r] = d.fotos[i];
    actualizarRuta(r); conv._marcar(Math.max(fe, 1), c);
    est.innerHTML = `Mejora <b>${i + 1}</b> de ${d.fotos.length} · evaluación <b>${f(fe)}</b> · costo <b>${f(c)}</b>` + (i === d.fotos.length - 1 ? " · <span class='ok'>ruta final</span>" : "");
  };
  rango.oninput = () => { detener(); mostrarFoto(+rango.value); };
  const detener = () => { clearInterval(temporizador); temporizador = null; $("#btn-play").textContent = "▶"; };
  $("#btn-play").onclick = () => {
    if (temporizador) return detener();
    if (+rango.value >= d.fotos.length - 1) rango.value = 0;
    $("#btn-play").textContent = "❚❚";
    temporizador = setInterval(() => {
      const i = +rango.value + 1;
      if (i >= d.fotos.length) return detener();
      rango.value = i; mostrarFoto(i);
    }, Math.max(40, 3500 / d.fotos.length));
  };
  mostrarFoto(d.fotos.length - 1);
}
function jsonCorto(d) {
  const h = d.historial;
  const txt = `{
  "mejor_ruta":   [${d.mejor_ruta.join(", ")}],
  "mejor_costo":  ${d.mejor_costo},
  "historial":    [${h.slice(0, 3).map(p => `(${p[0]}, ${f(p[1])})`).join(", ")}, … ${d.mejoras} pares (FEs, mejor_costo)],
  "evaluaciones": ${d.evaluaciones},
  "tiempo_s":     ${d.tiempo_s},
  "memoria_mb":   ${d.memoria_mb}
}`;
  return txt.replace(/</g, "&lt;");
}

/* ------------------------ comparar los cinco ------------------------ */
async function compararTodos() {
  if (ESTADO.corriendo) return;
  ESTADO.corriendo = true;
  const b = $("#btn-comparar"); b.disabled = true;
  const res = {};
  $("#resultado").innerHTML = `<div class="tarjeta"><h3>Ejecutando los 5 algoritmos con la misma instancia, semilla y presupuesto…</h3>
     <div class="progreso" style="margin:14px 0"><div id="barra-prog"></div></div><div id="estado-prog" class="sub"></div></div>`;
  try {
    for (let i = 0; i < ORDEN.length; i++) {
      const a = ORDEN[i];
      const estadoProg = $("#estado-prog");
      if (estadoProg) estadoProg.textContent = `Ejecutando ${a} (${INFO[a].nombre})… ${i}/${ORDEN.length}`;
      res[a] = await api("/api/ejecutar", peticion(a, {}));
      const barraProg = $("#barra-prog");
      if (barraProg) barraProg.style.width = `${100 * (i + 1) / ORDEN.length}%`;
    }
    ESTADO.comparacion = { clave: claveInstancia(), res };
    pintarComparacion();
  } catch (err) { alert("Error: " + err.message); }
  finally { ESTADO.corriendo = false; b.disabled = false; }
}

function pintarComparacion() {
  const res = ESTADO.comparacion.res, uno = res[ORDEN[0]];
  const fRef = uno.f_estrella || Math.min(...ORDEN.map(a => res[a].mejor_costo));
  const orden = [...ORDEN].sort((a, b) => res[a].mejor_costo - res[b].mejor_costo);
  const rapido = [...ORDEN].sort((a, b) => res[a].tiempo_s - res[b].tiempo_s)[0];
  const maxCosto = Math.max(...ORDEN.map(a => res[a].mejor_costo));
  $("#resultado").innerHTML = `
    <div class="tarjeta"><div class="cabeza"><h3>Comparación en la misma instancia (n = ${uno.n}, semilla ${uno.semilla}, ${f(uno.presupuesto)} evaluaciones)</h3></div>
      <p>🏆 La ruta más corta la encontró <b>${ptoAlg(orden[0])}${orden[0]}</b> (${f(res[orden[0]].mejor_costo)}); el más rápido fue <b>${ptoAlg(rapido)}${rapido}</b>
      (${f(res[rapido].tiempo_s * 1000, 1)} ms). Recuerde: una sola corrida no prueba nada; la conclusión seria está en las pestañas 4 y 5 (150 corridas por tamaño).</p>
      <div class="tabla-cont"><table>
        <tr><th>Algoritmo</th><th>Mejor costo</th><th>Error vs ${uno.f_estrella ? "f*" : "mejor de los 5"}</th><th>Mejor hallada en (FE)</th><th>Tiempo</th><th>Memoria (MB)</th></tr>
        ${orden.map((a, i) => { const r = res[a]; return `<tr class="${i === 0 ? "destacado" : ""}">
          <td>${ptoAlg(a)}${a} · ${INFO[a].nombre}</td>
          <td><div class="barra-celda" style="--c:${varColor(a)}"><div class="b" style="width:${90 * r.mejor_costo / maxCosto}px"></div>${f(r.mejor_costo)}</div></td>
          <td>${pct(100 * (r.mejor_costo - fRef) / fRef)}</td><td>${f(r.fe_mejor)}</td>
          <td>${r.tiempo_s < 1 ? f(r.tiempo_s * 1000, 1) + " ms" : f(r.tiempo_s, 2) + " s"}</td><td>${r.memoria_mb === null ? "–" : f(r.memoria_mb, 3)}</td></tr>`; }).join("")}
      </table></div></div>
    <div class="tarjeta"><div class="cabeza"><h3>Curvas de convergencia superpuestas</h3><div id="chips-comp"></div></div>
      <div id="g-comp"></div>
      <p class="leyenda-rap">Error del mejor histórico (%) frente a las evaluaciones. Pase el mouse para comparar los valores en un mismo momento.</p></div>
    <div class="tarjeta"><h3>Rutas finales</h3><div class="mini-rutas" id="mini"></div></div>`;
  const dibujar = () => {
    chips($("#chips-comp"), ORDEN, dibujar);
    G.lineas($("#g-comp"), {
      series: ORDEN.filter(a => ESTADO.visibles.has(a)).map(a => ({ nombre: a, color: color(a), escalon: true, xFin: res[a].evaluaciones,
        x: res[a].historial.map(h => h[0]), y: res[a].historial.map(h => 100 * (h[1] - fRef) / fRef) })),
      xTipo: "log", yTipo: "symlog", xMin: 1, xMax: uno.presupuesto, xEtiqueta: "Evaluaciones (FEs)", xEtiquetaCorta: "FEs",
      yEtiqueta: "Error del mejor histórico (%)", unidadY: " %", refs: [{ y: 1, texto: "1 %" }], alto: 380 });
  };
  dibujar();
  $("#mini").innerHTML = ORDEN.map(a => `<div class="item"><h4>${ptoAlg(a)}${a}</h4><div class="sub">${f(res[a].mejor_costo)} · ${pct(100 * (res[a].mejor_costo - fRef) / fRef)}</div><div id="mr-${a}"></div></div>`).join("");
  ORDEN.forEach(a => G.ruta($("#mr-" + a), { ciudades: res[a].ciudades, ruta: res[a].mejor_ruta, color: color(a), tam: 260, radio: 3.2, grosor: 1.8 }));
}

/* =====================================================================
   PESTAÑA 2: DISEÑO EXPERIMENTAL
   ===================================================================== */
async function pintarDiseno() {
  const c = ESTADO.config.config, R = ESTADO.res;
  $("#contenido").innerHTML = `
  <div class="intro"><h2>Punto 2 · Diseño experimental y reproducibilidad</h2>
    <p>Para que la comparación sea justa se controlan tres cosas: el <b>problema</b> (mismas instancias), el <b>presupuesto</b> (mismas evaluaciones) y el <b>azar</b> (mismas semillas).</p></div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>¿Por qué contar evaluaciones (FEs) y no iteraciones?</h3>
      <p>Una “iteración” no es el mismo esfuerzo en todos los algoritmos. Contar evaluaciones es como darle a cada carro <b>el mismo tanque de gasolina</b>.</p>
      <table><tr><th>Algoritmo</th><th>1 iteración =</th><th>Iteraciones con n = 100</th></tr>
        <tr><td>${ptoAlg("GA")}GA</td><td>${c.parametros.GA.poblacion - c.parametros.GA.elite} hijos = ${c.parametros.GA.poblacion - c.parametros.GA.elite} FEs</td><td>≈ ${f(c.presupuestos["100"] / (c.parametros.GA.poblacion - c.parametros.GA.elite), 0)}</td></tr>
        <tr><td>${ptoAlg("ACO")}ACO</td><td>n hormigas = 100 FEs</td><td>≈ ${f(c.presupuestos["100"] / 100, 0)}</td></tr>
        <tr><td>${ptoAlg("PSO")}PSO</td><td>${c.parametros.PSO.particulas} partículas = ${c.parametros.PSO.particulas} FEs</td><td>≈ ${f(c.presupuestos["100"] / c.parametros.PSO.particulas, 0)}</td></tr>
        <tr><td>${ptoAlg("HC")}HC</td><td>1 vecino = 1 FE</td><td>${f(c.presupuestos["100"])}</td></tr>
        <tr><td>${ptoAlg("SA")}SA</td><td>1 vecino = 1 FE</td><td>${f(c.presupuestos["100"])}</td></tr></table>
    </div>
    <div class="tarjeta"><h3>Protocolo aplicado</h3>
      <table>
        <tr><td class="izq">Tamaños</td><td>${c.tamanos.join(", ")} ciudades</td></tr>
        <tr><td class="izq">Instancias por tamaño</td><td>${c.semillas_publicas_instancias.length} (semillas públicas ${c.semillas_publicas_instancias.join(", ")})</td></tr>
        <tr><td class="izq">Presupuesto</td><td>${Object.entries(c.presupuestos).map(([n, b]) => `${f(b)} (n=${n})`).join(" · ")}</td></tr>
        <tr><td class="izq">Repeticiones</td><td>${c.repeticiones} por algoritmo × tamaño × instancia</td></tr>
        <tr><td class="izq">Total de corridas</td><td>${f(ESTADO.config.total_corridas)}</td></tr>
        <tr><td class="izq">Puntos de control</td><td>${c.fracciones_control.map(x => x * 100 + "%").join(", ")}</td></tr>
        <tr><td class="izq">Umbral de éxito ε</td><td>${c.epsilon * 100} %</td></tr>
        <tr><td class="izq">Tiempo</td><td>perf_counter, sin generar ciudades ni gráficas</td></tr>
        <tr><td class="izq">Memoria</td><td>tracemalloc en una 2.ª pasada (misma semilla)</td></tr>
      </table></div>
  </div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>Semillas (la misma para los 5 algoritmos)</h3>
      <p class="sub">Semilla de corrida = SeedSequence([${c.semilla_maestra}, n, instancia, repetición]). Así las corridas quedan <b>emparejadas</b>.</p>
      <div class="tabla-cont" style="max-height:340px"><table><tr><th>n</th><th>Inst.</th><th>Pública</th><th>Semilla instancia</th><th>Semillas rep. 0, 1, 2</th></tr>
      ${ESTADO.config.semillas.map(s => `<tr><td>${s.n}</td><td>${s.instancia}</td><td>${s.semilla_publica}</td><td class="mono">${s.semilla_instancia}</td><td class="mono">${s.semillas_rep_0_a_2.join(", ")}</td></tr>`).join("")}
      </table></div></div>
    <div class="tarjeta"><h3>Fase piloto (parámetros elegidos antes del experimento)</h3>
      <p class="sub">Instancias distintas (901–903, n = 50). La primera fila de cada algoritmo fue la elegida.</p>
      <div class="tabla-cont" style="max-height:340px"><table><tr><th>Alg.</th><th class="izq">Configuración</th><th>Error medio</th><th>Desv.</th></tr>
      ${(R.piloto || []).map((p, i, arr) => `<tr class="${i === 0 || arr[i - 1].algoritmo !== p.algoritmo ? "destacado" : ""}"><td>${ptoAlg(p.algoritmo)}${p.algoritmo}</td><td class="izq mono">${p.config}</td><td>${pct(p.mean)}</td><td>${f(p.std)}</td></tr>`).join("")}
      </table></div></div>
  </div>
  <div class="tarjeta"><div class="cabeza"><h3>Explorador del CSV de resultados (resultados/ejecuciones.csv)</h3>
    <a class="boton-sec" href="/descargas/ejecuciones.csv">⬇ Descargar CSV completo</a></div>
    <div class="fila" style="max-width:640px">
      <div><label class="campo">Algoritmo</label><select id="f-alg"><option value="todos">Todos</option>${[...ORDEN, ...ESTADO.config.extra].map(a => `<option>${a}</option>`).join("")}</select></div>
      <div><label class="campo">n</label><select id="f-n"><option value="todos">Todos</option>${c.tamanos.map(n => `<option>${n}</option>`).join("")}</select></div>
      <div><label class="campo">Instancia</label><select id="f-inst"><option value="todos">Todas</option>${c.semillas_publicas_instancias.map((_, i) => `<option>${i}</option>`).join("")}</select></div>
    </div>
    <p class="sub" id="csv-total" style="margin-top:10px"></p>
    <div class="tabla-cont" style="max-height:420px" id="csv-tabla"></div></div>`;
  if (!R.disponible) return;
  const cargar = async () => {
    const q = `algoritmo=${$("#f-alg").value}&n=${$("#f-n").value}&instancia=${$("#f-inst").value}`;
    const d = await api("/api/csv?" + q);
    $("#csv-total").textContent = `${f(d.total)} corridas con este filtro (se muestran las primeras ${d.filas.length}).`;
    const cols = ["algoritmo", "n", "instancia", "repeticion", "semilla", "costo", "error", "tiempo", "memoria", "FEs_mejor"];
    $("#csv-tabla").innerHTML = `<table><tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>${d.filas.map(r => `<tr>${cols.map(c =>
      `<td class="${c === "semilla" ? "mono" : ""}">${c === "algoritmo" ? ptoAlg(r[c]) + r[c] : typeof r[c] === "number" ? (c === "semilla" || c === "n" || c === "instancia" || c === "repeticion" ? r[c] : f(r[c], 3)) : (r[c] ?? "–")}</td>`).join("")}</tr>`).join("")}</table>`;
  };
  ["#f-alg", "#f-n", "#f-inst"].forEach(s => $(s).onchange = cargar);
  cargar();
}

/* =====================================================================
   PESTAÑA 3: EFICIENCIA Y ESCALABILIDAD
   ===================================================================== */
function pintarEficiencia() {
  const R = ESTADO.res;
  if (!R.disponible) { $("#contenido").innerHTML = sinResultados(); return; }
  const NS = ESTADO.config.config.tamanos;
  const ef = R.eficiencia, rend = R.rendimiento;
  const val = (tabla, a, n, k) => (tabla.find(r => r.algoritmo === a && r.n === n) || {})[k];
  const at100 = k => [...ORDEN].sort((a, b) => val(ef, a, 100, k) - val(ef, b, 100, k));
  $("#contenido").innerHTML = `
  <div class="intro"><h2>Punto 3 · Eficiencia computacional y escalabilidad</h2>
    <p>¿Cuánto <b>tiempo</b> y <b>memoria</b> gasta cada algoritmo y cómo crece eso al pasar de 20 a 50 y 100 ciudades?</p></div>
  <div class="tarjeta" style="padding:12px 18px"><div class="cabeza" style="margin:0"><div id="chips3"></div></div></div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>(a) Tiempo promedio por corrida</h3><div id="g31"></div></div>
    <div class="tarjeta"><h3>(b) Memoria pico promedio (tracemalloc)</h3><div id="g32"></div></div>
    <div class="tarjeta"><h3>Costo por cada 1000 evaluaciones</h3><div id="g33"></div><p class="leyenda-rap">Si la línea es plana, el costo de evaluar no crece con n (HC y SA usan la fórmula Δ en O(1)).</p></div>
    <div class="tarjeta"><h3>Calidad: error mediano final</h3><div id="g34"></div><p class="leyenda-rap">Escala: lineal entre 0 y 1 %, logarítmica arriba.</p></div>
  </div>
  <div class="tarjeta"><h3>(c) Tasa de éxito y evaluaciones necesarias para error ≤ 1 %</h3>
    <div class="tabla-cont"><table><tr><th>n</th><th>Algoritmo</th><th>Tiempo medio</th><th>ms / 1000 FEs</th><th>Memoria (MB)</th><th>Éxito (≤ 1 %)</th><th>FEs para llegar al 1 % (mediana)</th></tr>
    ${ef.map(r => `<tr><td>${r.n}</td><td class="izq">${ptoAlg(r.algoritmo)}${r.algoritmo}</td><td>${f(r.tiempo_medio_s, 3)} s</td><td>${f(r.tiempo_por_1000FEs_ms, 1)}</td>
      <td>${f(r.memoria_media_MB, 3)}</td><td><div class="barra-celda" style="--c:${varColor(r.algoritmo)}"><div class="b" style="width:${0.8 * r.exito_pct}px"></div>${f(r.exito_pct, 1)} %</div></td>
      <td>${r.FEs_umbral_mediana === null ? "nunca llegó" : f(r.FEs_umbral_mediana, 0)}</td></tr>`).join("")}</table></div></div>
  <div class="tarjeta"><h3>(d) ¿Quién escala mejor y por qué?</h3>
    <div class="rejilla-2">
      <div class="explica"><h4>En costo computacional: ${ptoAlg(at100("tiempo_medio_s")[0])}${at100("tiempo_medio_s")[0]} y ${ptoAlg(at100("tiempo_medio_s")[1])}${at100("tiempo_medio_s")[1]}</h4>
        <p>Con n = 100 una corrida de ${at100("tiempo_medio_s")[0]} tarda ${f(val(ef, at100("tiempo_medio_s")[0], 100, "tiempo_medio_s") * 1000, 0)} ms, frente a
        ${f(val(ef, "ACO", 100, "tiempo_medio_s"), 1)} s de ACO. Su costo por evaluación casi no cambia con n porque el vecino 2-opt se evalúa con 4 distancias (O(1)).
        ACO es el que peor escala: construir una ruta cuesta O(n²).</p></div>
      <div class="explica"><h4>En calidad: ${ptoAlg("ACO")}ACO</h4>
        <p>Su error mediano pasa de ${pct(val(rend, "ACO", 20, "error_mediana_%"))} a ${pct(val(rend, "ACO", 100, "error_mediana_%"))}, el menor en todos los tamaños.
        Con n = 100 solo ACO y SA alcanzan alguna vez el umbral del 1 %. HC es ≈ ${f(val(ef, "ACO", 100, "tiempo_medio_s") / val(ef, "HC", 100, "tiempo_medio_s"), 0)} veces más rápido que ACO pero su error es ${f(val(rend, "HC", 100, "error_mediana_%") / val(rend, "ACO", 100, "error_mediana_%"), 1)} veces mayor.</p></div>
    </div></div>`;
  const dibujar = () => {
    chips($("#chips3"), ORDEN, dibujar);
    const vis = ORDEN.filter(a => ESTADO.visibles.has(a));
    const serie = (tabla, k, esc = 1) => vis.map(a => ({ nombre: a, color: color(a), x: NS, y: NS.map(n => val(tabla, a, n, k) * esc), puntos: true, etiquetaFinal: true }));
    const comun = { xMarcas: NS, xMin: NS[0] - 6, xMax: NS[NS.length - 1] + 14, xEtiqueta: "Número de ciudades n", xEtiquetaCorta: "n", alto: 320 };
    G.lineas($("#g31"), { ...comun, series: serie(ef, "tiempo_medio_s"), yTipo: "log", yEtiqueta: "segundos (escala log)", unidadY: " s" });
    G.lineas($("#g32"), { ...comun, series: serie(ef, "memoria_media_MB"), yTipo: "log", yEtiqueta: "MB (escala log)", unidadY: " MB" });
    G.lineas($("#g33"), { ...comun, series: serie(ef, "tiempo_por_1000FEs_ms"), yTipo: "log", yEtiqueta: "ms por 1000 FEs (log)", unidadY: " ms" });
    G.lineas($("#g34"), { ...comun, series: serie(rend, "error_mediana_%"), yTipo: "symlog", yEtiqueta: "error mediano (%)", unidadY: " %", refs: [{ y: 1, texto: "1 %" }] });
  };
  dibujar();
}

/* =====================================================================
   PESTAÑA 4: RENDIMIENTO, CONVERGENCIA Y ESTABILIDAD
   ===================================================================== */
function pintarRendimiento() {
  const R = ESTADO.res;
  if (!R.disponible) { $("#contenido").innerHTML = sinResultados(); return; }
  const n = ESTADO.n4, c = ESTADO.config.config;
  const rend = R.rendimiento.filter(r => r.n === n), rk = R.ranking.filter(r => r.n === n);
  $("#contenido").innerHTML = `
  <div class="intro"><h2>Punto 4 · Rendimiento, convergencia y estabilidad</h2>
    <p>Resultados de las ${c.repeticiones} × ${c.semillas_publicas_instancias.length} = ${c.repeticiones * c.semillas_publicas_instancias.length} corridas de cada algoritmo para el tamaño elegido.</p></div>
  <div class="tarjeta" style="padding:12px 18px"><div class="cabeza" style="margin:0"><div style="display:flex;gap:12px;align-items:center"><b>Tamaño:</b><span id="seg4"></span></div><div id="chips4"></div></div></div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>(a) Convergencia promedio con banda de variabilidad</h3><div id="g41"></div>
      <p class="leyenda-rap">Línea = media; banda = percentiles 25–75. Todas las corridas se evaluaron en los mismos puntos del presupuesto antes de promediar.</p></div>
    <div class="tarjeta"><h3>(b) Diagrama de caja del error relativo final</h3><div id="g42"></div>
      <p class="leyenda-rap">Caja baja = buena calidad; caja angosta = estable. Pase el mouse sobre una caja para ver sus valores.</p></div>
  </div>
  <div class="tarjeta"><h3>(c) Tabla de rendimiento · n = ${n}</h3>
    <div class="tabla-cont"><table><tr><th>Algoritmo</th><th>Error mejor</th><th>Error medio</th><th>Error mediano</th><th>RIC</th><th>Éxito (≤ 1 %)</th><th>Mejora</th></tr>
    ${rend.map(r => `<tr><td>${ptoAlg(r.algoritmo)}${r.algoritmo} · ${INFO[r.algoritmo].nombre}</td><td>${pct(minError(r.algoritmo, n))}</td><td>${pct(r["error_medio_%"])}</td><td><b>${pct(r["error_mediana_%"])}</b></td>
      <td>${f(r.IQR_error)}</td><td>${f(r["exito_%"], 1)} %</td><td>${f(r["mejora_%"], 1)} %</td></tr>`).join("")}</table></div>
    <h4 style="margin:16px 0 6px">Costo absoluto por instancia <select id="sel-inst-costo" style="width:auto;margin-left:8px">${c.semillas_publicas_instancias.map((_, i) => `<option value="${i}">Instancia ${i}</option>`).join("")}</select></h4>
    <div class="tabla-cont" id="tabla-costos"></div></div>
  <div class="tarjeta"><div class="cabeza"><h3>(d) Rutas de los cinco métodos en la misma instancia (corrida mediana)</h3>
    <select id="sel-inst-ruta" style="width:auto">${c.semillas_publicas_instancias.map((_, i) => `<option value="${i}" ${i === ESTADO.inst4 ? "selected" : ""}>Instancia ${i}</option>`).join("")}</select></div>
    <div class="mini-rutas" id="rutas4"></div>
    <p class="leyenda-rap">Se muestra la corrida mediana (la típica), no la mejor. Fíjese en los cruces: 2-opt los elimina; PSO casi no aprende la geometría.</p></div>
  <div class="tarjeta"><h3>(e) Ranking por calidad, estabilidad y velocidad de convergencia · n = ${n}</h3>
    <div class="tabla-cont"><table><tr><th>Puesto global</th><th class="izq">Algoritmo</th><th>Calidad (rango Friedman)</th><th>Estabilidad (desv. del error)</th><th>Velocidad (área bajo la curva)</th></tr>
    ${rk.map(r => `<tr class="${r.pos_global === 1 ? "destacado" : ""}"><td>${r.pos_global}.º</td><td class="izq">${ptoAlg(r.algoritmo)}${r.algoritmo} · ${INFO[r.algoritmo].nombre}</td>
      <td>${r.pos_calidad}.º (${f(r["calidad (rango Friedman)"])})</td><td>${r.pos_estabilidad}.º (${f(r["estabilidad (desv. error %)"])})</td><td>${r.pos_velocidad}.º (${f(r["velocidad (AUC error)"], 1)})</td></tr>`).join("")}</table></div></div>`;
  $("#seg4").appendChild(segmentado(c.tamanos, n, v => { ESTADO.n4 = v; pintarRendimiento(); }));
  const dibujar = () => {
    chips($("#chips4"), ORDEN, dibujar);
    const vis = ORDEN.filter(a => ESTADO.visibles.has(a));
    const cur = R.curvas[String(n)];
    G.lineas($("#g41"), { series: vis.map(a => ({ nombre: a, color: color(a), x: cur[a].FEs, y: cur[a].media, lo: cur[a].q25, hi: cur[a].q75 })),
      xTipo: "log", yTipo: "symlog", xEtiqueta: "Evaluaciones (FEs, escala log)", xEtiquetaCorta: "FEs", yEtiqueta: "Error del mejor histórico (%)", unidadY: " %", refs: [{ y: 1, texto: "umbral 1 %" }], alto: 360 });
    G.cajas($("#g42"), { grupos: vis.map(a => ({ nombre: a, color: color(a), ...R.cajas[String(n)][a] })), yTipo: "symlog", yEtiqueta: "Error relativo final (%)", unidadY: " %", refs: [{ y: 1, texto: "1 %" }], alto: 360 });
  };
  dibujar();
  const tablaCostos = () => {
    const i = +$("#sel-inst-costo").value;
    const filasI = R.rendimiento_instancia.filter(r => r.n === n && r.instancia === i);
    $("#tabla-costos").innerHTML = `<table><tr><th>Algoritmo</th><th>Mejor</th><th>Media</th><th>Mediana</th><th>Desviación</th></tr>
      ${filasI.map(r => `<tr><td>${ptoAlg(r.algoritmo)}${r.algoritmo}</td><td>${f(r.mejor)}</td><td>${f(r.media)}</td><td>${f(r.mediana)}</td><td>${f(r.desv)}</td></tr>`).join("")}</table>`;
  };
  $("#sel-inst-costo").onchange = tablaCostos; tablaCostos();
  const rutas = async () => {
    const i = ESTADO.inst4 = +$("#sel-inst-ruta").value;
    const inst = await api(`/api/instancia?n=${n}&instancia=${i}`);
    const rm = R.rutas_medianas[`${n}_${i}`];
    $("#rutas4").innerHTML = ORDEN.map(a => `<div class="item"><h4>${ptoAlg(a)}${a}</h4><div class="sub">${f(rm[a].costo)} · error ${pct(rm[a].error)}</div><div id="r4-${a}"></div></div>`).join("");
    ORDEN.forEach(a => G.ruta($("#r4-" + a), { ciudades: inst.ciudades, ruta: rm[a].ruta, color: color(a), tam: 260, radio: n > 50 ? 2.6 : 3.4, grosor: 1.7 }));
  };
  $("#sel-inst-ruta").onchange = rutas; rutas();
}
function minError(a, n) {
  const cj = ESTADO.res.cajas[String(n)][a];
  return Math.min(cj.min, ...(cj.atipicos || [Infinity]));
}

/* =====================================================================
   PESTAÑA 5: CONCLUSIONES Y ESTADÍSTICA
   ===================================================================== */
function pintarConclusiones() {
  const R = ESTADO.res;
  if (!R.disponible) { $("#contenido").innerHTML = sinResultados(); return; }
  const n = ESTADO.n5, NS = ESTADO.config.config.tamanos;
  const fr = R.friedman.find(r => r.n === n);
  const rangos = R.rangos.filter(r => r.n === n).sort((a, b) => a.rango_promedio - b.rango_promedio);
  const ph = R.posthoc.filter(r => r.n === n);
  const val = (t, a, nn, k) => (t.find(r => r.algoritmo === a && r.n === nn) || {})[k];
  const mejorPor = (t, nn, k, menor = true) => [...ORDEN].sort((a, b) => (menor ? 1 : -1) * ((val(t, a, nn, k) ?? Infinity) - (val(t, b, nn, k) ?? Infinity)))[0];
  const ordenGlobal = nn => R.ranking.filter(r => r.n === nn).sort((a, b) => a.pos_global - b.pos_global).map(r => r.algoritmo);
  const par = (a, b) => ph.find(r => (r.A === a && r.B === b) || (r.A === b && r.B === a));
  const ef = R.eficiencia, rend = R.rendimiento, rk = R.ranking;
  const estab = (a, nn) => val(rk, a, nn, "estabilidad (desv. error %)");
  const sup = t => t.replace(/[-0-9]/g, c => "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"["-0123456789".indexOf(c)]);
  const pValor = p => { if (p >= 1e-4) return f(p, 4); const [m, e] = p.toExponential(1).split("e"); return `${m.replace(".", ",")} × 10${sup(String(+e))}`; };

  const preguntas = [
    ["1. ¿Qué algoritmo obtuvo las rutas de menor costo y cuál fue el más estable?",
      `<p>${NS.map(nn => `n = ${nn}: menor error mediano <b>${mejorPor(rend, nn, "error_mediana_%")}</b> (${pct(val(rend, mejorPor(rend, nn, "error_mediana_%"), nn, "error_mediana_%"))}); más estable <b>${[...ORDEN].sort((a, b) => estab(a, nn) - estab(b, nn))[0]}</b> (desv. ${f(Math.min(...ORDEN.map(a => estab(a, nn))))}).`).join("<br>")}</p>
       <p><b>Respuesta:</b> ACO en ambos casos y en todos los tamaños; gana todas sus comparaciones pareadas.</p>`],
    ["2. ¿Cuál alcanzó buenas soluciones usando menos evaluaciones?",
      `<p>${NS.map(nn => { const ok = ORDEN.filter(a => val(ef, a, nn, "FEs_umbral_mediana") !== null); const b = ok.sort((x, y) => val(ef, x, nn, "FEs_umbral_mediana") - val(ef, y, nn, "FEs_umbral_mediana"))[0];
        return `n = ${nn}: <b>${b}</b> llega al 1 % con una mediana de ${f(val(ef, b, nn, "FEs_umbral_mediana"), 0)} FEs (éxito ${f(val(ef, b, nn, "exito_pct"), 1)} %).`; }).join("<br>")}</p>
       <p><b>Respuesta:</b> ACO. Su primera ruta ya es buena porque usa la cercanía (1/d) para construir. HC es el segundo en velocidad de convergencia.</p>`],
    ["3. ¿Cuál tuvo menor tiempo y consumo de memoria? ¿Coincide con el de mejor calidad?",
      `<p>${NS.map(nn => `n = ${nn}: menor tiempo <b>${mejorPor(ef, nn, "tiempo_medio_s")}</b> (${f(val(ef, mejorPor(ef, nn, "tiempo_medio_s"), nn, "tiempo_medio_s") * 1000, 1)} ms); menor memoria <b>${mejorPor(ef, nn, "memoria_media_MB")}</b> (${f(val(ef, mejorPor(ef, nn, "memoria_media_MB"), nn, "memoria_media_MB"), 3)} MB).`).join("<br>")}</p>
       <p><b>Respuesta:</b> No coincide. El mejor en calidad (ACO) es el más lento con n = 100; en memoria, solo es el que más usa para n = 100. En los tamaños grandes la menor memoria medida la tiene GA. Hay un intercambio entre calidad y costo.</p>`],
    ["4. ¿Cómo cambió el ranking al aumentar el número de ciudades?",
      `<p>${NS.map(nn => `n = ${nn}: ${ordenGlobal(nn).map(a => `${ptoAlg(a)}${a}`).join(" › ")} · W de Kendall = ${f(R.friedman.find(r => r.n === nn).W_Kendall, 2)}`).join("<br>")}</p>
       <p><b>Respuesta:</b> ACO siempre 1.º y PSO siempre último. HC y SA se intercambian: con 20 ciudades los reinicios de HC bastan; con 50 y 100 aceptar empeoramientos (SA) es decisivo. El orden se vuelve más consistente (W sube).</p>`],
    ["5. ¿Qué efecto tiene el componente poblacional (GA, ACO, PSO) y la trayectoria única (HC, SA)?",
      `<p>La población ayuda <b>solo si comparte información útil</b>: en ACO la feromona es una memoria colectiva que se combina con la cercanía. En GA cada generación gasta ${ESTADO.config.config.parametros.GA.poblacion - 2} evaluaciones y el cruce rompe aristas buenas: converge lento (sigue mejorando al final). En PSO la codificación por claves impide aprovechar la memoria.
       La trayectoria única (HC, SA) es barata por evaluación y explota bien la vecindad 2-opt, pero puede atascarse en óptimos locales.</p>`],
    ["6. ¿Cuándo resulta útil aceptar empeoramientos (SA) o mantener diversidad?",
      `<p>Cuando hay <b>muchos óptimos locales</b> y <b>presupuesto para enfriar</b>. Con n = 20, HC ≈ SA; con n = 50 el error mediano pasa de ${pct(val(rend, "HC", 50, "error_mediana_%"))} (HC) a ${pct(val(rend, "SA", 50, "error_mediana_%"))} (SA) y con n = 100 de ${pct(val(rend, "HC", 100, "error_mediana_%"))} a ${pct(val(rend, "SA", 100, "error_mediana_%"))}.
       Pero si el presupuesto se corta temprano, SA va perdiendo (mire su curva en “S” en la pestaña 4). Demasiada diversidad también daña: en el piloto, GA con mutación 0,6 fue mucho peor.</p>`],
    ["7. ¿Existe un ganador absoluto? ¿Qué usar en cada escenario?",
      `<p><b>No.</b> Ningún algoritmo gana en calidad, tiempo y memoria a la vez (teorema “No Free Lunch”).</p>
       <table><tr><th>Escenario</th><th>Algoritmo recomendado</th><th class="izq">Por qué</th></tr>
         <tr><td class="izq">Respuesta rápida</td><td>${ptoAlg("HC")}HC (o SA)</td><td class="izq">milisegundos, ruta sin cruces</td></tr>
         <tr><td class="izq">Alta calidad</td><td>${ptoAlg("ACO")}ACO</td><td class="izq">mejor y más estable en todos los tamaños</td></tr>
         <tr><td class="izq">Menor memoria medida</td><td>${ptoAlg("GA")}GA</td><td class="izq">usa menos memoria en n = 50 y n = 100; en n = 20 empata prácticamente con ACO</td></tr>
         <tr><td class="izq">Memoria teórica baja</td><td>${ptoAlg("SA")}SA</td><td class="izq">puede guardar una sola ruta y calcular distancias al vuelo; 2.º en calidad</td></tr></table>`],
  ];

  $("#contenido").innerHTML = `
  <div class="intro"><h2>Punto 5 · Análisis crítico, estadística y conclusiones</h2>
    <p>No basta con que un promedio sea menor: hay que probar que la diferencia es <b>consistente</b> (no es suerte) y ver <b>qué tan grande</b> es.</p></div>
  <div class="tarjeta" style="padding:12px 18px"><div style="display:flex;gap:12px;align-items:center"><b>Tamaño:</b><span id="seg5"></span></div></div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>Prueba de Friedman (n = ${n})</h3>
      <div class="kpis" style="grid-template-columns:repeat(3,1fr);margin:6px 0 12px">
        <div class="kpi"><div class="t">χ² de Friedman</div><div class="v">${f(fr.chi2, 1)}</div><div class="d">${fr.bloques} carreras</div></div>
        <div class="kpi"><div class="t">Valor p</div><div class="v" style="font-size:1.2rem">${pValor(fr.p_valor)}</div><div class="d">${fr.p_valor < 0.05 ? "hay diferencias" : "sin diferencias"}</div></div>
        <div class="kpi"><div class="t">W de Kendall</div><div class="v">${f(fr.W_Kendall, 2)}</div><div class="d">0 = azar · 1 = mismo orden siempre</div></div></div>
      <p class="sub">Idea: en cada una de las ${fr.bloques} “carreras” (instancia × repetición, misma semilla) se da un puesto a cada algoritmo. Si todos fueran iguales, cada uno quedaría en promedio de 3.º.</p></div>
    <div class="tarjeta"><h3>Puesto promedio (1 = mejor)</h3><div id="g-rangos"></div></div>
  </div>
  <div class="tarjeta"><h3>¿Quién le gana a quién? (Wilcoxon pareado + corrección de Holm, n = ${n})</h3>
    <div class="tabla-cont"><table class="matriz"><tr><th></th>${ORDEN.map(a => `<th>${a}</th>`).join("")}</tr>
    ${ORDEN.map(a => `<tr><th class="izq">${ptoAlg(a)}${a}</th>${ORDEN.map(b => {
      if (a === b) return `<td class="diag">—</td>`;
      const p = par(a, b); const gana = p.mejor; const r = Math.abs(p.biserial_rangos);
      return `<td title="p (Holm) = ${pValor(p.p_Holm)} · efecto = ${f(r, 2)}" style="background:color-mix(in srgb, ${varColor(gana === "empate" ? a : gana)} ${Math.round(12 + 40 * r)}%, transparent)">${gana === "empate" ? "empate" : gana} <span class="sub">(${f(r, 2)})</span></td>`; }).join("")}</tr>`).join("")}
    </table></div>
    <p class="leyenda-rap">Cada celda dice quién da rutas más cortas en ese par y, entre paréntesis, el tamaño del efecto (0 = casi iguales, 1 = gana siempre). Color más intenso = diferencia más grande. Pase el mouse para ver el valor p ajustado.</p></div>
  <div class="tarjeta"><h3>Las 7 preguntas del taller, con evidencia</h3>
    ${preguntas.map(([p, r], i) => `<details class="pregunta" ${i === 0 ? "open" : ""}><summary>${p}</summary>${r}</details>`).join("")}</div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>Amenaza a la validez</h3><p>f* es la mejor ruta encontrada en el experimento, <b>no el óptimo real</b>: los errores son cotas inferiores y favorecen a quien define la referencia (ACO con n = 100).
      Además, los parámetros se ajustaron solo con n = 50 y el tiempo depende de qué tan vectorizado está cada código en Python.</p></div>
    <div class="tarjeta"><h3>Mejora para un experimento posterior</h3><p>Usar instancias con <b>óptimo conocido</b> (TSPLIB o el resolvedor Concorde), ajustar parámetros por tamaño con una herramienta automática (irace) y comparar tiempos con una implementación compilada (Numba).</p></div>
  </div>`;
  $("#seg5").appendChild(segmentado(NS, n, v => { ESTADO.n5 = v; pintarConclusiones(); }));
  G.barrasH($("#g-rangos"), { items: rangos.map(r => ({ nombre: r.algoritmo, color: color(r.algoritmo), valor: r.rango_promedio, texto: f(r.rango_promedio, 2) })), max: 5 });
}

/* =====================================================================
   PESTAÑA OPCIONAL: HÍBRIDO
   ===================================================================== */
function pintarHibrido() {
  const R = ESTADO.res;
  if (!R.disponible || !R.hibrido) { $("#contenido").innerHTML = sinResultados(); return; }
  const n = ESTADO.nH, NS = ESTADO.config.config.tamanos;
  const hb = R.hibrido.filter(r => r.n === n);
  const lista = ["ACO", "HC", "SA", "ACO+2opt"];
  $("#contenido").innerHTML = `
  <div class="intro"><h2>Pregunta opcional · Híbrido ACO + 2-opt</h2>
    <p>La colonia propone rutas y la mejor hormiga de cada iteración se pule con búsqueda local 2-opt. <b>Mismo presupuesto total de evaluaciones.</b></p></div>
  <div class="tarjeta" style="padding:12px 18px"><div style="display:flex;gap:12px;align-items:center"><b>Tamaño:</b><span id="segH"></span>
    <button class="boton-sec" id="probarH" style="margin-left:auto">▶ Probarlo en vivo</button></div></div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>Convergencia: híbrido vs. sus componentes</h3><div id="gH"></div></div>
    <div class="tarjeta"><h3>¿Mejora estadísticamente? (Wilcoxon + Holm)</h3>
      <div class="tabla-cont"><table><tr><th>Contra</th><th>Error med. híbrido</th><th>Error med. rival</th><th>Gana el híbrido</th><th>p (Holm)</th></tr>
      ${hb.map(r => `<tr><td>${ptoAlg(r.contra)}${r.contra}</td><td>${pct(r.error_mediana_hibrido)}</td><td>${pct(r.error_mediana_contra)}</td>
        <td><div class="barra-celda" style="--c:var(--c-ACO2)"><div class="b" style="width:${0.6 * r["gana_hibrido_%"]}px"></div>${f(r["gana_hibrido_%"], 1)} %</div></td>
        <td>${r.p_Holm < 1e-3 ? "< 0,001" : f(r.p_Holm, 3)}</td></tr>`).join("")}</table></div>
      <p class="leyenda-rap">“Gana el híbrido” = % de las 150 corridas emparejadas (misma semilla) en que el híbrido encontró una ruta más corta.</p>
      <div class="explica" style="--c:var(--c-ACO2);margin-top:14px"><h4>Conclusión</h4>
        <p>El híbrido le gana con claridad a HC y a SA, pero <b>no a ACO puro</b> (empata con n = 20 y pierde con n = 50 y 100).
        La búsqueda local gasta 5n evaluaciones por iteración, así que la colonia hace muchas menos iteraciones (≈ 100 en vez de 600 con n = 100) y la feromona aprende menos.
        Es mucho más rápido en segundos: si el límite fuera el tiempo y no las evaluaciones, el resultado podría cambiar.</p></div></div>
  </div>`;
  $("#segH").appendChild(segmentado(NS, n, v => { ESTADO.nH = v; pintarHibrido(); }));
  const cur = R.curvas[String(n)];
  G.lineas($("#gH"), { series: lista.map(a => ({ nombre: a, color: color(a), x: cur[a].FEs, y: cur[a].media, grosor: a === "ACO+2opt" ? 3.4 : 2 })),
    xTipo: "log", yTipo: "symlog", xEtiqueta: "Evaluaciones (FEs, escala log)", xEtiquetaCorta: "FEs", yEtiqueta: "Error medio del mejor histórico (%)", unidadY: " %", refs: [{ y: 1, texto: "1 %" }], alto: 380 });
  $("#probarH").onclick = () => { ESTADO.ej.alg = "ACO+2opt"; ESTADO.ej.n = n; ESTADO.ej.presupuesto = null; irA("ejecutar"); };
}

/* =====================================================================
   PESTAÑA TEORÍA
   ===================================================================== */
function pintarTeoria() {
  $("#contenido").innerHTML = `
  <div class="intro"><h2>Teoría rápida</h2><p>Lo mínimo para entender la interfaz. El documento final de entrega está en el <a href="/descargas/informe.pdf" target="_blank">informe en PDF</a>.</p></div>
  <div class="rejilla-2">
    <div class="tarjeta"><h3>El problema del viajante (TSP)</h3>
      <p>Un domiciliario debe visitar n casas una sola vez y volver al inicio gastando la menor distancia posible. Una solución es un <b>orden de visita</b> (permutación).</p>
      <div class="formula">f(π) = Σ<sub>k=1</sub><sup>n−1</sup> d(π<sub>k</sub>, π<sub>k+1</sub>) + d(π<sub>n</sub>, π<sub>1</sub>)</div>
      <p class="sub">Con 100 ciudades hay ≈ 4,7 × 10<sup>155</sup> rutas: imposible revisarlas todas.</p></div>
    <div class="tarjeta"><h3>¿Qué es una metaheurística?</h3>
      <p>Una <b>estrategia general</b> para buscar buenas soluciones sin revisarlas todas. Todas siguen la misma plantilla: generar candidatos → evaluarlos → decidir cuáles conservar → recordar la mejor. No garantizan el óptimo, pero encuentran rutas muy buenas con presupuesto limitado.</p></div>
    <div class="tarjeta"><h3>Explorar vs. explotar</h3>
      <p><b>Explorar</b>: buscar en zonas nuevas para no quedarse atrapado. <b>Explotar</b>: afinar alrededor de lo bueno. Cada algoritmo tiene su “perilla”: la temperatura en SA, la mutación en GA, la evaporación en ACO, la inercia en PSO.</p></div>
    <div class="tarjeta"><h3>Movimiento 2-opt (vecindad de HC y SA)</h3>
      <p>Se “descruzan” dos tramos invirtiendo el pedazo de en medio. El cambio de longitud se calcula con solo 4 distancias:</p>
      <div class="formula">Δ = d(a,c) + d(b,d) − d(a,b) − d(c,d)</div></div>
  </div>
  <div class="tarjeta"><h3>Los cinco algoritmos</h3>
    ${[...ORDEN, "ACO+2opt"].map(a => `<div class="explica" style="--c:${varColor(a)}"><h4>${ptoAlg(a)}${a} · ${INFO[a].nombre} <span class="etiqueta">${INFO[a].familia}</span></h4><p>${INFO[a].idea}</p><div class="formula">${INFO[a].formula}</div></div>`).join("")}</div>`;
}

/* Redibujar al cambiar el tamaño de la ventana (las gráficas usan el ancho real) */
let esperaResize = null;
window.addEventListener("resize", () => {
  clearTimeout(esperaResize);
  esperaResize = setTimeout(() => { if (ESTADO.config && !ESTADO.corriendo && ESTADO.tab !== "diseno") irA(ESTADO.tab); }, 250);
});

/* ------------------------------ inicio ------------------------------ */
observarTexto();
(async () => {
  try {
    [ESTADO.config, ESTADO.res] = await Promise.all([api("/api/config"), api("/api/resultados")]);
    irA("ejecutar");
  } catch (e) {
    $("#contenido").innerHTML = `<div class="tarjeta vacio">No se pudo conectar con el servidor. ¿Está corriendo <code>python interfaz_grafica.py</code>?<br>${e.message}</div>`;
  }
})();
