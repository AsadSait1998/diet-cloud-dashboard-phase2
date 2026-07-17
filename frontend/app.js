(function () {
  "use strict";

  const config = window.DIET_DASHBOARD_CONFIG || { apiBaseUrl: "/api" };
  const colors = ["#174f3b", "#e97b62", "#e1ad45", "#4b7898", "#7b5e8b", "#6b9d72", "#c76581", "#829b3f"];
  const macroColors = { protein_g: "#174f3b", carbs_g: "#e97b62", fat_g: "#e1ad45" };
  const state = { payload: null, loading: false, initializedFilters: false, controller: null };
  const byId = (id) => document.getElementById(id);

  const elements = {
    form: byId("filter-form"),
    search: byId("search-input"),
    diet: byId("diet-filter"),
    cuisine: byId("cuisine-filter"),
    clear: byId("clear-filters"),
    refresh: byId("refresh-data"),
    retry: byId("retry-button"),
    error: byId("error-alert"),
    errorMessage: byId("error-message"),
    loading: byId("loading-overlay"),
    connection: byId("connection-status"),
    connectionText: byId("connection-text")
  };

  function formatNumber(value, digits = 0) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "--";
    return number.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
  }

  function setText(id, value) {
    byId(id).textContent = value;
  }

  function endpointUrl(forceRefresh) {
    const base = String(config.apiBaseUrl || "/api").replace(/\/+$/, "");
    const url = new URL(`${base}/diet-insights`, window.location.href);
    if (elements.diet.value) url.searchParams.set("diet_types", elements.diet.value);
    if (elements.cuisine.value) url.searchParams.set("cuisine", elements.cuisine.value);
    if (elements.search.value.trim()) url.searchParams.set("search", elements.search.value.trim());
    if (forceRefresh) url.searchParams.set("refresh", "true");
    return url;
  }

  function setConnection(kind, text) {
    elements.connection.classList.remove("online", "offline");
    if (kind) elements.connection.classList.add(kind);
    elements.connectionText.textContent = text;
  }

  function showLoading(visible) {
    state.loading = visible;
    elements.loading.classList.toggle("hidden", !visible);
    elements.loading.setAttribute("aria-hidden", String(!visible));
    elements.form.querySelectorAll("button, input, select").forEach((control) => {
      control.disabled = visible;
    });
  }

  function showError(message) {
    elements.errorMessage.textContent = message;
    elements.error.classList.remove("hidden");
    setConnection("offline", "API unavailable");
  }

  function clearError() {
    elements.error.classList.add("hidden");
  }

  async function fetchInsights(forceRefresh = false) {
    if (state.controller) state.controller.abort();
    state.controller = new AbortController();
    const timeout = window.setTimeout(() => state.controller.abort(), 20000);
    showLoading(true);
    clearError();
    setConnection("", "Analyzing cloud data");
    try {
      const response = await fetch(endpointUrl(forceRefresh), {
        headers: { Accept: "application/json" },
        signal: state.controller.signal
      });
      let body;
      try {
        body = await response.json();
      } catch (_error) {
        throw new Error(`The API returned an unreadable response (HTTP ${response.status}).`);
      }
      if (!response.ok) throw new Error(body.message || `The API returned HTTP ${response.status}.`);
      state.payload = body;
      renderDashboard(body);
      const sourceName = String(body.metadata?.source?.storage || "").toLowerCase();
      setConnection("online", sourceName.includes("local") ? "Local API connected" : "Live Azure API connected");
    } catch (error) {
      if (error.name !== "AbortError" || state.loading) {
        const message = error.name === "AbortError" ? "The API request timed out after 20 seconds." : error.message;
        showError(`${message} Endpoint: ${endpointUrl(false).origin}${endpointUrl(false).pathname}`);
      }
    } finally {
      window.clearTimeout(timeout);
      showLoading(false);
    }
  }

  function populateSelect(select, values, firstLabel) {
    const previous = select.value;
    select.replaceChildren();
    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = firstLabel;
    select.appendChild(allOption);
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
    if (values.includes(previous)) select.value = previous;
  }

  function sourceLabel(source) {
    if (!source) return "Unknown source";
    if (source.storage === "Azure Blob Storage") return `Blob: ${source.container}/${source.blob}`;
    return source.storage || "Unknown source";
  }

  function renderDashboard(payload) {
    const summary = payload.summary;
    const metadata = payload.metadata;
    if (!state.initializedFilters) {
      populateSelect(elements.diet, payload.filters.available_diet_types || [], "All diet types");
      populateSelect(elements.cuisine, payload.filters.available_cuisines || [], "All cuisines");
      state.initializedFilters = true;
    }

    setText("metric-recipes", formatNumber(summary.recipe_count));
    setText("metric-diets", formatNumber(summary.diet_type_count));
    setText("metric-protein", formatNumber(summary.average_protein_g, 1));
    setText("metric-carbs", formatNumber(summary.average_carbs_g, 1));
    setText("metric-fat", formatNumber(summary.average_fat_g, 1));
    setText("metric-record-context", `of ${formatNumber(metadata.records_in_dataset)} total records`);
    setText("execution-label", `${formatNumber(metadata.execution_time_ms, 1)} ms`);
    setText("source-label", sourceLabel(metadata.source));
    const generated = new Date(metadata.generated_at_utc);
    setText("refresh-label", Number.isNaN(generated.valueOf()) ? "Just now" : generated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    const dietLabel = summary.diet_type_count === 1 ? "diet type" : "diet types";
    setText("result-summary", `${formatNumber(metadata.records_after_filtering)} recipes · ${formatNumber(summary.diet_type_count)} ${dietLabel}`);

    renderMacroTable(payload.charts.average_macros_by_diet || []);
    renderAllCharts();
  }

  function renderMacroTable(rows) {
    const body = byId("macro-table-body");
    body.replaceChildren();
    if (!rows.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 4;
      cell.textContent = "No recipes match the selected filters.";
      row.appendChild(cell);
      body.appendChild(row);
      return;
    }
    rows.forEach((item) => {
      const row = document.createElement("tr");
      [item.diet_type, formatNumber(item.protein_g, 2), formatNumber(item.carbs_g, 2), formatNumber(item.fat_g, 2)].forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      });
      body.appendChild(row);
    });
  }

  function canvasSetup(id, preferredHeight) {
    const canvas = byId(id);
    const width = Math.max(300, Math.floor(canvas.getBoundingClientRect().width || 600));
    const height = preferredHeight;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * ratio);
    canvas.height = Math.floor(height * ratio);
    canvas.style.height = `${height}px`;
    const context = canvas.getContext("2d");
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.clearRect(0, 0, width, height);
    context.lineCap = "round";
    context.lineJoin = "round";
    return { context, width, height };
  }

  function canvasMessage(context, width, height, message) {
    context.fillStyle = "#607068";
    context.font = "600 13px Inter, system-ui, sans-serif";
    context.textAlign = "center";
    context.fillText(message, width / 2, height / 2);
  }

  function axisNumber(value) {
    if (value >= 1000) return `${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`;
    return Math.round(value).toString();
  }

  function roundedRect(context, x, y, width, height, radius) {
    const r = Math.min(radius, width / 2, height / 2);
    context.beginPath();
    context.moveTo(x + r, y);
    context.arcTo(x + width, y, x + width, y + height, r);
    context.arcTo(x + width, y + height, x, y + height, r);
    context.arcTo(x, y + height, x, y, r);
    context.arcTo(x, y, x + width, y, r);
    context.closePath();
  }

  function drawMacroChart(rows) {
    const { context: ctx, width, height } = canvasSetup("macro-chart", 400);
    if (!rows.length) return canvasMessage(ctx, width, height, "No macro data for these filters");
    const margins = { top: 18, right: 14, bottom: 95, left: 48 };
    const plotWidth = width - margins.left - margins.right;
    const plotHeight = height - margins.top - margins.bottom;
    const maxValue = Math.max(1, ...rows.flatMap((row) => [row.protein_g, row.carbs_g, row.fat_g]));
    const axisMax = Math.ceil(maxValue / 25) * 25;

    ctx.font = "11px Inter, system-ui, sans-serif";
    for (let tick = 0; tick <= 4; tick += 1) {
      const y = margins.top + plotHeight - (tick / 4) * plotHeight;
      ctx.strokeStyle = "#dde1da";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(margins.left, y); ctx.lineTo(width - margins.right, y); ctx.stroke();
      ctx.fillStyle = "#76827c";
      ctx.textAlign = "right";
      ctx.fillText(axisNumber((tick / 4) * axisMax), margins.left - 8, y + 4);
    }

    const groupWidth = plotWidth / rows.length;
    const barWidth = Math.max(4, Math.min(22, (groupWidth - 12) / 3));
    rows.forEach((row, index) => {
      const center = margins.left + groupWidth * index + groupWidth / 2;
      ["protein_g", "carbs_g", "fat_g"].forEach((key, macroIndex) => {
        const barHeight = (row[key] / axisMax) * plotHeight;
        const x = center + (macroIndex - 1) * (barWidth + 2) - barWidth / 2;
        const y = margins.top + plotHeight - barHeight;
        ctx.fillStyle = macroColors[key];
        roundedRect(ctx, x, y, barWidth, barHeight, 3);
        ctx.fill();
      });
      ctx.save();
      ctx.translate(center + 3, margins.top + plotHeight + 13);
      ctx.rotate(-Math.PI / 4);
      ctx.fillStyle = "#4f5f57";
      ctx.font = "600 11px Inter, system-ui, sans-serif";
      ctx.textAlign = "right";
      const label = row.diet_type.length > 22 ? `${row.diet_type.slice(0, 20)}…` : row.diet_type;
      ctx.fillText(label, 0, 0);
      ctx.restore();
    });
  }

  function drawDistributionChart(rows) {
    const { context: ctx, width, height } = canvasSetup("distribution-chart", 330);
    const total = rows.reduce((sum, row) => sum + row.recipe_count, 0);
    if (!total) return canvasMessage(ctx, width, height, "No recipe distribution to display");
    const compact = width < 460;
    const centerX = compact ? width / 2 : width * .34;
    const centerY = compact ? 115 : height / 2;
    const radius = Math.min(compact ? 78 : 96, width * .24);
    let angle = -Math.PI / 2;
    rows.forEach((row, index) => {
      const sweep = (row.recipe_count / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, angle, angle + sweep);
      ctx.strokeStyle = colors[index % colors.length];
      ctx.lineWidth = Math.max(22, radius * .34);
      ctx.stroke();
      angle += sweep;
    });
    ctx.fillStyle = "#12231c";
    ctx.textAlign = "center";
    ctx.font = "500 28px Georgia, serif";
    ctx.fillText(formatNumber(total), centerX, centerY + 2);
    ctx.fillStyle = "#607068";
    ctx.font = "700 10px Inter, system-ui, sans-serif";
    ctx.fillText("RECIPES", centerX, centerY + 21);

    const legendX = compact ? 20 : width * .61;
    const legendY = compact ? 224 : Math.max(24, height / 2 - rows.length * 11);
    const columnWidth = compact ? width / 2 - 24 : width * .37;
    rows.forEach((row, index) => {
      const column = compact ? index % 2 : 0;
      const line = compact ? Math.floor(index / 2) : index;
      const x = legendX + column * columnWidth;
      const y = legendY + line * 24;
      ctx.fillStyle = colors[index % colors.length];
      roundedRect(ctx, x, y - 8, 9, 9, 2); ctx.fill();
      ctx.fillStyle = "#405048";
      ctx.textAlign = "left";
      ctx.font = "600 10.5px Inter, system-ui, sans-serif";
      const label = row.diet_type.length > 15 ? `${row.diet_type.slice(0, 13)}…` : row.diet_type;
      ctx.fillText(`${label} · ${Math.round(row.recipe_count / total * 100)}%`, x + 15, y);
    });
  }

  function drawCuisineChart(rows) {
    const { context: ctx, width, height } = canvasSetup("cuisine-chart", 330);
    if (!rows.length) return canvasMessage(ctx, width, height, "No cuisine data for these filters");
    const left = Math.min(122, width * .35);
    const right = 30;
    const top = 12;
    const rowHeight = (height - top - 10) / rows.length;
    const maxValue = Math.max(...rows.map((row) => row.recipe_count), 1);
    rows.forEach((row, index) => {
      const y = top + index * rowHeight + rowHeight * .16;
      const barHeight = rowHeight * .58;
      const barWidth = (row.recipe_count / maxValue) * (width - left - right);
      ctx.fillStyle = "#e9ede6";
      roundedRect(ctx, left, y, width - left - right, barHeight, barHeight / 2); ctx.fill();
      ctx.fillStyle = index === 0 ? "#174f3b" : "#79a18f";
      roundedRect(ctx, left, y, Math.max(3, barWidth), barHeight, barHeight / 2); ctx.fill();
      ctx.fillStyle = "#405048";
      ctx.textAlign = "right";
      ctx.font = "600 10.5px Inter, system-ui, sans-serif";
      const label = row.cuisine_type.length > 17 ? `${row.cuisine_type.slice(0, 15)}…` : row.cuisine_type;
      ctx.fillText(label, left - 9, y + barHeight * .72);
      ctx.fillStyle = index === 0 ? "#ffffff" : "#12231c";
      ctx.textAlign = barWidth > 34 ? "right" : "left";
      ctx.font = "800 10px Inter, system-ui, sans-serif";
      ctx.fillText(formatNumber(row.recipe_count), left + (barWidth > 34 ? barWidth - 7 : barWidth + 6), y + barHeight * .72);
    });
  }

  function drawScatterChart(points) {
    const { context: ctx, width, height } = canvasSetup("scatter-chart", 390);
    if (!points.length) return canvasMessage(ctx, width, height, "No recipe points for these filters");
    const margins = { top: 47, right: 24, bottom: 52, left: 58 };
    const plotWidth = width - margins.left - margins.right;
    const plotHeight = height - margins.top - margins.bottom;
    const maxX = Math.max(1, ...points.map((point) => point.carbs_g));
    const maxY = Math.max(1, ...points.map((point) => point.protein_g));
    const axisX = Math.ceil(maxX / 100) * 100;
    const axisY = Math.ceil(maxY / 100) * 100;
    const diets = [...new Set(points.map((point) => point.diet_type))];
    const dietColor = new Map(diets.map((diet, index) => [diet, colors[index % colors.length]]));

    ctx.font = "10.5px Inter, system-ui, sans-serif";
    for (let tick = 0; tick <= 5; tick += 1) {
      const x = margins.left + tick / 5 * plotWidth;
      const y = margins.top + plotHeight - tick / 5 * plotHeight;
      ctx.strokeStyle = "#dde1da";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, margins.top); ctx.lineTo(x, margins.top + plotHeight); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(margins.left, y); ctx.lineTo(margins.left + plotWidth, y); ctx.stroke();
      ctx.fillStyle = "#76827c";
      ctx.textAlign = "center";
      ctx.fillText(axisNumber(tick / 5 * axisX), x, margins.top + plotHeight + 18);
      ctx.textAlign = "right";
      ctx.fillText(axisNumber(tick / 5 * axisY), margins.left - 9, y + 4);
    }
    ctx.fillStyle = "#607068";
    ctx.textAlign = "center";
    ctx.font = "700 10px Inter, system-ui, sans-serif";
    ctx.fillText("CARBOHYDRATES (G)", margins.left + plotWidth / 2, height - 7);
    ctx.save(); ctx.translate(13, margins.top + plotHeight / 2); ctx.rotate(-Math.PI / 2); ctx.fillText("PROTEIN (G)", 0, 0); ctx.restore();

    points.forEach((point) => {
      const x = margins.left + point.carbs_g / axisX * plotWidth;
      const y = margins.top + plotHeight - point.protein_g / axisY * plotHeight;
      const radius = Math.max(2.5, Math.min(7, 2.5 + Math.sqrt(Math.max(0, point.fat_g)) / 5));
      ctx.globalAlpha = .68;
      ctx.fillStyle = dietColor.get(point.diet_type);
      ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.fill();
    });
    ctx.globalAlpha = 1;

    let legendX = margins.left;
    let legendY = 14;
    ctx.font = "600 10px Inter, system-ui, sans-serif";
    diets.forEach((diet) => {
      const labelWidth = ctx.measureText(diet).width + 23;
      if (legendX + labelWidth > width - 15) { legendX = margins.left; legendY += 18; }
      ctx.fillStyle = dietColor.get(diet); ctx.beginPath(); ctx.arc(legendX + 4, legendY - 3, 4, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#405048"; ctx.textAlign = "left"; ctx.fillText(diet, legendX + 12, legendY);
      legendX += labelWidth;
    });
  }

  function renderAllCharts() {
    if (!state.payload) return;
    const charts = state.payload.charts;
    drawMacroChart(charts.average_macros_by_diet || []);
    drawDistributionChart(charts.recipe_distribution_by_diet || []);
    drawCuisineChart(charts.top_cuisines || []);
    drawScatterChart(charts.protein_vs_carbs || []);
  }

  elements.form.addEventListener("submit", (event) => {
    event.preventDefault();
    fetchInsights(false);
  });
  elements.clear.addEventListener("click", () => {
    elements.search.value = "";
    elements.diet.value = "";
    elements.cuisine.value = "";
    fetchInsights(false);
  });
  elements.refresh.addEventListener("click", () => fetchInsights(true));
  elements.retry.addEventListener("click", () => fetchInsights(false));

  let resizeTimer;
  window.addEventListener("resize", () => {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(renderAllCharts, 140);
  });

  fetchInsights(false);
}());
