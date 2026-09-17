/**
 * MICRON BOM INTELLIGENCE CLIENT LOGIC
 */

const API_BASE = "";

// State
const state = {
  currentTab: "overview",
  overview: null,
  anomalies: [],
  reconciliation: [],
  catalogType: "single",
  catalogPage: 1,
  catalogPageSize: 25,
  catalogTotal: 0,
  currentMaterialForModal: null,
};

// DOM Elements
const el = {
  tabs: document.querySelectorAll(".nav-tab"),
  panes: document.querySelectorAll(".tab-pane"),
  btnRefresh: document.getElementById("btn-refresh"),
  globalSearch: document.getElementById("global-search"),
  searchSuggestions: document.getElementById("search-suggestions"),
  
  // KPI
  kpiSingleLevel: document.getElementById("kpi-single-level"),
  kpiUniqueHeaders: document.getElementById("kpi-unique-headers"),
  kpiFlatRecords: document.getElementById("kpi-flat-records"),
  kpiUniqueComp: document.getElementById("kpi-unique-comp"),
  kpiCriticalAnomalies: document.getElementById("kpi-critical-anomalies"),
  kpiTotalAnomalies: document.getElementById("kpi-total-anomalies"),
  kpiReconDiscrepancies: document.getElementById("kpi-recon-discrepancies"),
  badgeAnomalies: document.getElementById("badge-anomalies"),
  badgeRecon: document.getElementById("badge-recon"),
  
  // Overview containers
  stageDistContainer: document.getElementById("stage-distribution-container"),
  anomalySummaryContainer: document.getElementById("anomaly-summary-container"),
  reconSummaryCards: document.getElementById("recon-summary-cards"),
  btnGotoRecon: document.getElementById("btn-goto-recon"),

  // Anomalies
  anomaliesTableBody: document.getElementById("anomalies-table-body"),
  anomalyFilterType: document.getElementById("anomaly-filter-type"),
  anomalyFilterSeverity: document.getElementById("anomaly-filter-severity"),
  anomalySearchInput: document.getElementById("anomaly-search-input"),

  // Reconciliation
  reconTableBody: document.getElementById("recon-table-body"),
  reconFilterType: document.getElementById("recon-filter-type"),
  reconSearchInput: document.getElementById("recon-search-input"),

  // Tree & Lineage
  treeMaterialInput: document.getElementById("tree-material-input"),
  materialDatalist: document.getElementById("material-datalist"),
  btnLoadTree: document.getElementById("btn-load-tree"),
  btnTraceForward: document.getElementById("btn-trace-forward"),
  btnTraceReverse: document.getElementById("btn-trace-reverse"),
  treeRootContainer: document.getElementById("tree-root-container"),
  treeCurrentTitle: document.getElementById("tree-current-title"),
  lineageHeader: document.getElementById("lineage-header"),
  lineageBadge: document.getElementById("lineage-badge"),
  lineageStepsContainer: document.getElementById("lineage-steps-container"),

  // Catalog
  btnCatalogSingle: document.getElementById("btn-catalog-single"),
  btnCatalogFlat: document.getElementById("btn-catalog-flat"),
  catalogSearch: document.getElementById("catalog-search"),
  catalogTableHead: document.getElementById("catalog-table-head"),
  catalogTableBody: document.getElementById("catalog-table-body"),
  catalogPageInfo: document.getElementById("catalog-page-info"),
  btnPagePrev: document.getElementById("btn-page-prev"),
  btnPageNext: document.getElementById("btn-page-next"),

  // Modal
  modal: document.getElementById("material-modal"),
  modalTitle: document.getElementById("modal-material-title"),
  modalBody: document.getElementById("modal-material-body"),
  btnCloseModal: document.getElementById("btn-close-modal"),
  btnModalCloseAction: document.getElementById("btn-modal-close-action"),
  btnModalTree: document.getElementById("btn-modal-tree"),
};

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadAllData();
  loadMaterialDatalist();
});

function initEventListeners() {
  // Navigation Tabs
  el.tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      switchTab(target);
    });
  });

  if (el.btnGotoRecon) {
    el.btnGotoRecon.addEventListener("click", () => switchTab("reconciliation"));
  }

  if (el.btnRefresh) {
    el.btnRefresh.addEventListener("click", loadAllData);
  }

  // Global search autocomplete
  let searchTimer;
  el.globalSearch.addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    const q = e.target.value.trim();
    if (!q) {
      el.searchSuggestions.classList.add("hidden");
      return;
    }
    searchTimer = setTimeout(async () => {
      const res = await fetch(`${API_BASE}/api/materials?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      renderSuggestions(data.materials);
    }, 200);
  });

  document.addEventListener("click", (e) => {
    if (!el.searchSuggestions.contains(e.target) && e.target !== el.globalSearch) {
      el.searchSuggestions.classList.add("hidden");
    }
  });

  // Anomaly Filters
  el.anomalyFilterType.addEventListener("change", filterAnomalies);
  el.anomalyFilterSeverity.addEventListener("change", filterAnomalies);
  if (el.anomalySearchInput) {
    el.anomalySearchInput.addEventListener("input", filterAnomalies);
  }

  // Recon Filters
  el.reconFilterType.addEventListener("change", filterReconciliation);
  if (el.reconSearchInput) {
    el.reconSearchInput.addEventListener("input", filterReconciliation);
  }

  // Tree & Lineage triggers
  el.btnLoadTree.addEventListener("click", () => {
    const mat = el.treeMaterialInput.value.trim();
    loadTree(mat);
  });

  el.btnTraceForward.addEventListener("click", () => {
    const mat = el.treeMaterialInput.value.trim();
    loadLineage(mat, "forward");
  });

  el.btnTraceReverse.addEventListener("click", () => {
    const mat = el.treeMaterialInput.value.trim();
    loadLineage(mat, "reverse");
  });

  // Catalog tab toggles
  el.btnCatalogSingle.addEventListener("click", () => {
    state.catalogType = "single";
    state.catalogPage = 1;
    el.btnCatalogSingle.classList.add("active");
    el.btnCatalogFlat.classList.remove("active");
    loadCatalog();
  });

  el.btnCatalogFlat.addEventListener("click", () => {
    state.catalogType = "flat";
    state.catalogPage = 1;
    el.btnCatalogFlat.classList.add("active");
    el.btnCatalogSingle.classList.remove("active");
    loadCatalog();
  });

  let catalogSearchTimer;
  el.catalogSearch.addEventListener("input", () => {
    clearTimeout(catalogSearchTimer);
    catalogSearchTimer = setTimeout(() => {
      state.catalogPage = 1;
      loadCatalog();
    }, 300);
  });

  el.btnPagePrev.addEventListener("click", () => {
    if (state.catalogPage > 1) {
      state.catalogPage--;
      loadCatalog();
    }
  });

  el.btnPageNext.addEventListener("click", () => {
    const maxPage = Math.ceil(state.catalogTotal / state.catalogPageSize);
    if (state.catalogPage < maxPage) {
      state.catalogPage++;
      loadCatalog();
    }
  });

  // Modal actions
  const closeModal = () => el.modal.classList.add("hidden");
  el.btnCloseModal.addEventListener("click", closeModal);
  if (el.btnModalCloseAction) {
    el.btnModalCloseAction.addEventListener("click", closeModal);
  }
  document.querySelector(".modal-backdrop").addEventListener("click", closeModal);

  el.btnModalTree.addEventListener("click", () => {
    if (state.currentMaterialForModal) {
      closeModal();
      switchTab("tree");
      el.treeMaterialInput.value = state.currentMaterialForModal;
      loadTree(state.currentMaterialForModal);
    }
  });
}

function switchTab(tabId) {
  state.currentTab = tabId;
  el.tabs.forEach(t => {
    t.classList.toggle("active", t.dataset.tab === tabId);
  });
  el.panes.forEach(p => {
    p.classList.toggle("active", p.id === `tab-${tabId}`);
  });

  if (tabId === "tree" && !el.treeRootContainer.children.length) {
    loadTree(el.treeMaterialInput.value.trim());
  } else if (tabId === "catalog") {
    loadCatalog();
  }
}

// -------------------------------------------------------------
// DATA FETCHING & RENDERING
// -------------------------------------------------------------

async function loadAllData() {
  try {
    const [overviewRes, anomaliesRes, reconRes] = await Promise.all([
      fetch(`${API_BASE}/api/overview`),
      fetch(`${API_BASE}/api/anomalies`),
      fetch(`${API_BASE}/api/reconciliation`)
    ]);

    const overview = await overviewRes.json();
    const anomaliesData = await anomaliesRes.json();
    const reconData = await reconRes.json();

    state.overview = overview;
    state.anomalies = anomaliesData.anomalies || [];
    state.reconciliation = reconData.results || [];

    renderOverview(overview);
    renderAnomalies(state.anomalies);
    renderReconciliation(state.reconciliation);

    // If material input is empty, default to first FPN
    if (!el.treeMaterialInput.value) {
      const mats = await (await fetch(`${API_BASE}/api/materials`)).json();
      const firstFpn = mats.materials.find(m => m.startsWith("FPN-")) || mats.materials[0];
      if (firstFpn) el.treeMaterialInput.value = firstFpn;
    }

  } catch (err) {
    console.error("Failed to load initial data:", err);
  }
}

async function loadMaterialDatalist() {
  try {
    const res = await fetch(`${API_BASE}/api/materials`);
    const data = await res.json();
    el.materialDatalist.innerHTML = data.materials
      .map(m => `<option value="${m}"></option>`)
      .join("");
  } catch (e) {
    console.error(e);
  }
}

function renderSuggestions(materials) {
  if (!materials || !materials.length) {
    el.searchSuggestions.innerHTML = `<div class="suggestion-item" style="color:var(--text-dim)">No materials found</div>`;
    el.searchSuggestions.classList.remove("hidden");
    return;
  }

  el.searchSuggestions.innerHTML = materials.slice(0, 10).map(m => `
    <div class="suggestion-item" data-mat="${m}">
      <span>${m}</span>
      <span style="font-size:10px; color:var(--accent-cyan)">Explore →</span>
    </div>
  `).join("");

  el.searchSuggestions.querySelectorAll(".suggestion-item").forEach(item => {
    item.addEventListener("click", () => {
      const mat = item.dataset.mat;
      el.globalSearch.value = mat;
      el.searchSuggestions.classList.add("hidden");
      openMaterialModal(mat);
    });
  });

  el.searchSuggestions.classList.remove("hidden");
}

function renderOverview(data) {
  if (!data) return;

  const db = data.database || {};
  const anom = data.anomalies || {};
  const recon = data.reconciliation || {};

  el.kpiSingleLevel.textContent = (db.singleLevelRecords || 0).toLocaleString();
  el.kpiUniqueHeaders.textContent = `${db.uniqueHeaders || 0} headers / plants`;
  el.kpiFlatRecords.textContent = (db.flatRecords || 0).toLocaleString();
  el.kpiUniqueComp.textContent = `${db.uniqueComponents || 0} unique components`;

  const crit = anom.bySeverity?.CRITICAL || 0;
  const totAnom = anom.total || 0;
  el.kpiCriticalAnomalies.textContent = crit;
  el.kpiTotalAnomalies.textContent = `${totAnom} flagged anomalies`;
  el.badgeAnomalies.textContent = totAnom;

  const diffCount = recon.discrepancies || 0;
  el.kpiReconDiscrepancies.textContent = diffCount;
  el.badgeRecon.textContent = diffCount;

  // Render Stage Distribution Bars
  if (db.stageDistribution && db.stageDistribution.length) {
    const maxCnt = Math.max(...db.stageDistribution.map(s => s.count), 1);
    el.stageDistContainer.innerHTML = db.stageDistribution.map(s => `
      <div class="stage-bar-item">
        <div class="stage-bar-meta">
          <span class="stage-name">${s.stage}</span>
          <span class="stage-count">${s.count} headers</span>
        </div>
        <div class="stage-bar-track">
          <div class="stage-bar-fill" style="width: ${(s.count / maxCnt) * 100}%"></div>
        </div>
      </div>
    `).join("");
  }

  // Render Anomaly Type composition
  if (anom.byType) {
    const entries = Object.entries(anom.byType);
    el.anomalySummaryContainer.innerHTML = entries.map(([type, count]) => {
      const isCrit = ["CYCLE", "STAGE_VIOLATION"].includes(type);
      return `
        <div class="anomaly-item-row">
          <div class="anomaly-item-type">
            <span class="dot-indicator ${isCrit ? 'dot-critical' : 'dot-warning'}"></span>
            <span>${type}</span>
          </div>
          <span class="anomaly-item-count ${isCrit ? 'text-critical' : 'text-warning'}">${count}</span>
        </div>
      `;
    }).join("");
  }

  // Render Recon breakdown cards
  if (recon.byType) {
    const reconTypes = [
      { key: "MATERIAL_MISMATCH", label: "Material Mismatches" },
      { key: "PHANTOM_ENTRY", label: "Phantom Entries" },
      { key: "FLAT_ONLY", label: "Flat ERP Only" },
      { key: "RECONSTRUCTION_ONLY", label: "Reconstruction Only" }
    ];

    el.reconSummaryCards.innerHTML = reconTypes.map(rt => `
      <div class="recon-stat-box">
        <div class="count">${recon.byType[rt.key] || 0}</div>
        <div class="label">${rt.label}</div>
      </div>
    `).join("");
  }
}

// -------------------------------------------------------------
// ANOMALIES VIEW
// -------------------------------------------------------------

function filterAnomalies() {
  const typeFilter = el.anomalyFilterType.value;
  const sevFilter = el.anomalyFilterSeverity.value;
  const query = el.anomalySearchInput?.value.toLowerCase().trim() || "";

  const filtered = state.anomalies.filter(a => {
    if (typeFilter && a.type !== typeFilter) return false;
    if (sevFilter && a.severity !== sevFilter) return false;
    if (query) {
      const mat = String(a.material || "").toLowerCase();
      const desc = String(a.description || "").toLowerCase();
      const path = Array.isArray(a.path) ? a.path.join(" ").toLowerCase() : "";
      if (!mat.includes(query) && !desc.includes(query) && !path.includes(query)) return false;
    }
    return true;
  });

  renderAnomalies(filtered);
}

function renderAnomalies(anomalies) {
  if (!anomalies.length) {
    el.anomaliesTableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4" style="color:var(--text-dim)">
          No anomalies matching criteria.
        </td>
      </tr>
    `;
    return;
  }

  el.anomaliesTableBody.innerHTML = anomalies.slice(0, 150).map(a => {
    const isCrit = a.severity === "CRITICAL";
    const pathStr = Array.isArray(a.path) ? a.path.join(" → ") : (a.break_point ? `Break: ${a.break_point}` : "--");

    return `
      <tr>
        <td>
          <span class="${isCrit ? 'badge-sev-critical' : 'badge-sev-warning'}">
            ${a.severity}
          </span>
        </td>
        <td><span class="mono-tag">${a.type}</span></td>
        <td><strong>${a.material || '--'}</strong></td>
        <td><span style="color:var(--text-muted)">${a.description || '--'}</span></td>
        <td><span class="mono-path" title="${pathStr}">${pathStr}</span></td>
        <td>
          <button class="btn-sm btn-outline" onclick="openMaterialModal('${a.material}')">Inspect</button>
        </td>
      </tr>
    `;
  }).join("");
}

// -------------------------------------------------------------
// RECONCILIATION VIEW
// -------------------------------------------------------------

function filterReconciliation() {
  const typeFilter = el.reconFilterType.value;
  const query = el.reconSearchInput?.value.toLowerCase().trim() || "";

  const filtered = state.reconciliation.filter(r => {
    if (typeFilter && r.type !== typeFilter) return false;
    if (query) {
      const json = JSON.stringify(r).toLowerCase();
      if (!json.includes(query)) return false;
    }
    return true;
  });

  renderReconciliation(filtered);
}

function renderReconciliation(results) {
  if (!results.length) {
    el.reconTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center py-4" style="color:var(--text-dim)">
          No reconciliation discrepancies found.
        </td>
      </tr>
    `;
    return;
  }

  el.reconTableBody.innerHTML = results.slice(0, 100).map(r => {
    const fpn = r.fpn || r.record?.FPN || (r.provided ? r.provided.FPN : "--");
    let detail = "";

    if (r.type === "MATERIAL_MISMATCH") {
      const diffs = Object.entries(r.differences || {}).map(([col, d]) => {
        return `<strong>${col}</strong>: <span style="color:#38bdf8">${d.reconstructed || 'None'}</span> vs <span style="color:#fb7185">${d.provided || 'None'}</span>`;
      }).join("<br>");
      detail = diffs || "Value discrepancy detected";
    } else if (r.type === "PHANTOM_ENTRY") {
      detail = `Unknown material: <span style="color:#fb7185">${r.material}</span> in ERP record`;
    } else if (r.type === "FLAT_ONLY") {
      detail = `Exists in ERP flat records but not reconstructible via single-level relations.`;
    } else if (r.type === "RECONSTRUCTION_ONLY") {
      detail = `Reconstructed from single-level graph but missing from ERP flat dataset.`;
    }

    return `
      <tr>
        <td><span class="badge-sev-warning">DISCREPANCY</span></td>
        <td><span class="mono-tag">${r.type}</span></td>
        <td><strong>${fpn}</strong></td>
        <td>${detail}</td>
        <td>
          <button class="btn-sm btn-outline" onclick="openMaterialModal('${fpn}')">Explore Tree</button>
        </td>
      </tr>
    `;
  }).join("");
}

// -------------------------------------------------------------
// TREE HIERARCHY & LINEAGE
// -------------------------------------------------------------

async function loadTree(material) {
  if (!material) return;
  el.treeRootContainer.innerHTML = `<div class="loader-placeholder">Exploding BOM tree for ${material}...</div>`;
  el.treeCurrentTitle.textContent = `Exploding: ${material}`;

  try {
    const res = await fetch(`${API_BASE}/api/tree?material=${encodeURIComponent(material)}`);
    const treeData = await res.json();
    if (treeData.error) {
      el.treeRootContainer.innerHTML = `<div class="loader-placeholder text-critical">${treeData.error}</div>`;
      return;
    }
    renderTree(treeData, el.treeRootContainer);
  } catch (err) {
    el.treeRootContainer.innerHTML = `<div class="loader-placeholder text-critical">Error rendering tree: ${err}</div>`;
  }
}

function renderTree(node, container) {
  container.innerHTML = "";
  const ul = document.createElement("ul");
  ul.appendChild(createTreeNodeElement(node));
  container.appendChild(ul);
  requestAnimationFrame(() => drawCycleConnections(container));
}

function createTreeNodeElement(node) {
  const li = document.createElement("li");
  const edgeAnomalies = node.edge_anomalies || [];

  if (edgeAnomalies.some(a => a.type === "STAGE_VIOLATION")) {
    li.classList.add("edge-stage-violation");
  }
  if (edgeAnomalies.some(a => a.type === "EXPIRED_ACTIVE")) {
    li.classList.add("edge-expired-active");
  }

  const chip = document.createElement("div");
  chip.className = "node-chip";
  chip.dataset.material = node.material;
  
  if (node.material.startsWith("FPN-")) chip.classList.add("stage-fpn");
  else if (node.material.startsWith("RAW-")) chip.classList.add("stage-raw");
  if (node.cycle) chip.classList.add("node-cycle");

  const anomalyBadges = edgeAnomalies.map(anomaly => {
    const label = anomaly.type === "STAGE_VIOLATION" ? "STAGE VIOLATION" : "EXPIRED ACTIVE";
    const className = anomaly.type === "STAGE_VIOLATION" ? "stage-alert" : "expired-alert";
    return `<span class="node-anomaly-badge ${className}" title="${anomaly.description}">${label}</span>`;
  }).join("");

  chip.innerHTML = `${node.material} ${node.cycle ? '<span class="cycle-return-label">↩ CYCLE</span>' : ''}${anomalyBadges}`;
  chip.addEventListener("click", () => openMaterialModal(node.material));

  li.appendChild(chip);

  if (node.children && node.children.length > 0) {
    const subUl = document.createElement("ul");
    node.children.forEach(child => {
      subUl.appendChild(createTreeNodeElement(child));
    });
    li.appendChild(subUl);
  }

  return li;
}

function drawCycleConnections(container) {
  container.querySelectorAll(".cycle-connector-svg").forEach(svg => svg.remove());

  const cycleNodes = [...container.querySelectorAll(".node-chip.node-cycle")];
  if (!cycleNodes.length) return;

  const containerRect = container.getBoundingClientRect();
  const width = Math.max(container.scrollWidth, container.clientWidth);
  const height = Math.max(container.scrollHeight, container.clientHeight);
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.classList.add("cycle-connector-svg");
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.innerHTML = `
    <defs>
      <marker id="cycle-arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
        <path d="M0,0 L8,4 L0,8 Z" fill="#f43f5e"></path>
      </marker>
    </defs>
  `;

  cycleNodes.forEach(cycleNode => {
    const target = [...container.querySelectorAll(".node-chip")].find(candidate =>
      candidate !== cycleNode &&
      !candidate.classList.contains("node-cycle") &&
      candidate.dataset.material === cycleNode.dataset.material
    );
    if (!target) return;

    const sourceRect = cycleNode.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const sourceX = sourceRect.right - containerRect.left;
    const sourceY = sourceRect.top + sourceRect.height / 2 - containerRect.top;
    const targetX = targetRect.right - containerRect.left;
    const targetY = targetRect.top + targetRect.height / 2 - containerRect.top;
    const loopX = Math.max(sourceX, targetX) + 70;

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M ${sourceX} ${sourceY} C ${loopX} ${sourceY}, ${loopX} ${targetY}, ${targetX + 5} ${targetY}`);
    path.setAttribute("class", "cycle-return-path");
    path.setAttribute("marker-end", "url(#cycle-arrowhead)");
    svg.appendChild(path);
  });

  container.prepend(svg);
}

async function loadLineage(material, direction) {
  if (!material) {
    alert("Please specify a target material.");
    return;
  }

  el.lineageHeader.textContent = `Lineage: ${material}`;
  el.lineageBadge.textContent = direction.toUpperCase();
  el.lineageStepsContainer.innerHTML = `<div class="loader-placeholder">Tracing ${direction} supply chain...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/lineage?material=${encodeURIComponent(material)}&direction=${direction}`);
    const data = await res.json();

    if (!data.lineage || !data.lineage.length) {
      el.lineageStepsContainer.innerHTML = `<div class="placeholder-text">No ${direction} lineage connections found.</div>`;
      return;
    }

    el.lineageStepsContainer.innerHTML = data.lineage.map((item, idx) => `
      <div class="lineage-item" onclick="openMaterialModal('${item}')" style="cursor:pointer">
        <span class="lineage-index">${idx + 1}.</span>
        <span>${item}</span>
      </div>
    `).join("");

  } catch (err) {
    el.lineageStepsContainer.innerHTML = `<div class="placeholder-text text-critical">Failed to trace: ${err}</div>`;
  }
}

// -------------------------------------------------------------
// DATA CATALOG
// -------------------------------------------------------------

async function loadCatalog() {
  const type = state.catalogType;
  const page = state.catalogPage;
  const q = el.catalogSearch.value.trim();

  const endpoint = type === "single" ? "/api/records/single" : "/api/records/flat";
  el.catalogTableBody.innerHTML = `<tr><td colspan="10" class="text-center py-4">Fetching database records...</td></tr>`;

  try {
    const res = await fetch(`${API_BASE}${endpoint}?page=${page}&pageSize=${state.catalogPageSize}&q=${encodeURIComponent(q)}`);
    const data = await res.json();

    state.catalogTotal = data.total;

    // Header setup
    if (type === "single") {
      el.catalogTableHead.innerHTML = `
        <tr>
          <th>ID</th>
          <th>HDR Material</th>
          <th>Group</th>
          <th>COMP Material</th>
          <th>Comp Group</th>
          <th>Qty</th>
          <th>Plant</th>
          <th>Status</th>
          <th>Valid Range</th>
        </tr>
      `;
      el.catalogTableBody.innerHTML = data.rows.map(r => `
        <tr>
          <td><span class="mono-tag">${r.id}</span></td>
          <td><strong>${r.HDR_MATERIAL}</strong></td>
          <td><span class="mono-tag">${r.HDR_MATL_GROUP || '--'}</span></td>
          <td><strong>${r.COMP_MATERIAL}</strong></td>
          <td><span class="mono-tag">${r.COMP_MATL_GROUP || '--'}</span></td>
          <td>${r.COMP_QTY || 1}</td>
          <td>${r.PLANT || '--'}</td>
          <td>${r.BOM_STATUS || '--'}</td>
          <td><span style="font-size:11px">${r.VALID_FROM || ''} → ${r.VALID_TO || '9999'}</span></td>
        </tr>
      `).join("");
    } else {
      el.catalogTableHead.innerHTML = `
        <tr>
          <th>ID</th>
          <th>FPN</th>
          <th>PKGD</th>
          <th>TSTD</th>
          <th>ASMBLD</th>
          <th>MODULE</th>
          <th>CHIP</th>
          <th>DIE</th>
          <th>WAFER</th>
          <th>RAW</th>
        </tr>
      `;
      el.catalogTableBody.innerHTML = data.rows.map(r => `
        <tr>
          <td><span class="mono-tag">${r.id}</span></td>
          <td><strong style="color:var(--accent-cyan)">${r.FPN || '--'}</strong></td>
          <td>${r.PKGD || '--'}</td>
          <td>${r.TSTD || '--'}</td>
          <td>${r.ASMBLD || '--'}</td>
          <td>${r.MODULE || '--'}</td>
          <td>${r.CHIP || '--'}</td>
          <td>${r.DIE || '--'}</td>
          <td>${r.WAFER || '--'}</td>
          <td><span style="color:var(--accent-emerald)">${r.RAW || '--'}</span></td>
        </tr>
      `).join("");
    }

    const start = (page - 1) * state.catalogPageSize + 1;
    const end = Math.min(page * state.catalogPageSize, data.total);
    el.catalogPageInfo.textContent = `Showing ${start}-${end} of ${data.total} records`;

    el.btnPagePrev.disabled = page <= 1;
    el.btnPageNext.disabled = end >= data.total;

  } catch (err) {
    el.catalogTableBody.innerHTML = `<tr><td colspan="10" class="text-center py-4 text-critical">Error: ${err}</td></tr>`;
  }
}

// -------------------------------------------------------------
// MATERIAL INSPECTOR MODAL
// -------------------------------------------------------------

async function openMaterialModal(material) {
  if (!material || material === "--") return;
  state.currentMaterialForModal = material;

  el.modalTitle.textContent = `Material Audit: ${material}`;
  el.modalBody.innerHTML = `<div class="loader-placeholder">Loading material lineage and associated anomalies...</div>`;
  el.modal.classList.remove("hidden");

  try {
    const [forwardRes, reverseRes] = await Promise.all([
      fetch(`${API_BASE}/api/lineage?material=${encodeURIComponent(material)}&direction=forward`),
      fetch(`${API_BASE}/api/lineage?material=${encodeURIComponent(material)}&direction=reverse`)
    ]);

    const forward = await forwardRes.json();
    const reverse = await reverseRes.json();

    // Check if involved in anomalies
    const relatedAnomalies = state.anomalies.filter(a => {
      if (a.material === material) return true;
      if (Array.isArray(a.path) && a.path.includes(material)) return true;
      return false;
    });

    el.modalBody.innerHTML = `
      <div style="margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
          <span style="color:var(--text-muted)">Stage Designation:</span>
          <span class="mono-tag" style="color:var(--accent-cyan)">${inferStage(material)}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
          <span style="color:var(--text-muted)">Forward Sub-Assemblies (Explosion):</span>
          <strong>${(forward.lineage || []).length} items</strong>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
          <span style="color:var(--text-muted)">Where-Used Implosion (Parents):</span>
          <strong>${(reverse.lineage || []).length} items</strong>
        </div>
      </div>

      <h4 style="margin: 14px 0 8px 0; font-size:12px; color:var(--text-muted); text-transform:uppercase;">Flagged Anomalies (${relatedAnomalies.length})</h4>
      ${relatedAnomalies.length ? `
        <div style="max-height:160px; overflow-y:auto;">
          ${relatedAnomalies.map(a => `
            <div style="padding:6px 10px; background:#131e33; border-radius:4px; margin-bottom:4px; font-size:12px;">
              <span class="${a.severity === 'CRITICAL' ? 'badge-sev-critical' : 'badge-sev-warning'}">${a.type}</span>
              <span style="margin-left:6px; color:var(--text-muted);">${a.description}</span>
            </div>
          `).join("")}
        </div>
      ` : '<p style="color:var(--accent-emerald); font-size:12px;">✓ No direct anomalies registered for this material.</p>'}
    `;

  } catch (err) {
    el.modalBody.innerHTML = `<div class="text-critical">Failed to load material detail: ${err}</div>`;
  }
}

function inferStage(mat) {
  if (mat.startsWith("FPN-")) return "FPN (Finished Part Number)";
  if (mat.startsWith("PKGD-")) return "PKGD (Packaged Product)";
  if (mat.startsWith("TSTD-")) return "TSTD (Tested Product)";
  if (mat.startsWith("ASMBLD-")) return "ASMBLD (Assembled Unit)";
  if (mat.startsWith("MOD-")) return "MODULE (Module)";
  if (mat.startsWith("CHIP-")) return "CHIP (Processed Chip)";
  if (mat.startsWith("DIE-")) return "DIE (Silicon Die)";
  if (mat.startsWith("WAFER-")) return "WAFER (Processed Wafer)";
  if (mat.startsWith("FAB_OUT-")) return "FAB_OUT (Fabrication Output)";
  if (mat.startsWith("RAW-")) return "RAW (Raw Material)";
  return "CUSTOM / INTERMEDIATE";
}

// -------------------------------------------------------------
// AI CONVERSATIONAL AGENT CLIENT
// -------------------------------------------------------------

function initAIChat() {
  const drawer = document.getElementById("ai-chat-drawer");
  const btnOpen = document.getElementById("btn-open-chat");
  const btnClose = document.getElementById("btn-close-chat");
  const btnSend = document.getElementById("btn-send-chat");
  const input = document.getElementById("chat-user-input");
  const messagesContainer = document.getElementById("chat-messages");
  const promptChips = document.querySelectorAll(".chip-btn");

  if (!drawer || !btnOpen) return;

  btnOpen.addEventListener("click", () => {
    drawer.classList.remove("closed");
    input.focus();
  });

  btnClose.addEventListener("click", () => {
    drawer.classList.add("closed");
  });

  promptChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.dataset.prompt;
      input.value = prompt;
      sendChatMessage();
    });
  });

  btnSend.addEventListener("click", sendChatMessage);

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  async function sendChatMessage() {
    const text = input.value.trim();
    if (!text) return;

    // Append user message bubble
    appendMessage(text, "user");
    input.value = "";

    // Show typing bubble
    const typingId = appendMessage("Thinking and querying BOM graph...", "assistant typing");
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
        signal: controller.signal
      });
      const data = await res.json();

      if (data.reply) {
        appendMessage(data.reply, "assistant");
      } else if (data.error) {
        appendMessage(`❌ Error: ${data.error}`, "assistant");
      }
    } catch (err) {
      if (err.name === "AbortError") {
        appendMessage("❌ The AI request timed out. Please try again.", "assistant");
      } else {
        appendMessage(`❌ Network error: ${err}`, "assistant");
      }
    } finally {
      clearTimeout(timeoutId);
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();
    }
  }

  function appendMessage(text, role) {
    const id = "msg-" + Date.now() + "-" + Math.random().toString(36).substr(2, 4);
    const div = document.createElement("div");
    div.id = id;
    div.className = `chat-msg ${role}`;
    
    // Parse basic markdown bullets / bold
    let formatted = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code style="background:#1b2844;padding:2px 4px;border-radius:3px;font-size:12px;">$1</code>')
      .replace(/\n/g, '<br>');
      
    div.innerHTML = formatted;
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return id;
  }
}

// Global scope attachment for inline handlers
window.openMaterialModal = openMaterialModal;

document.addEventListener("DOMContentLoaded", () => {
  initAIChat();
});
