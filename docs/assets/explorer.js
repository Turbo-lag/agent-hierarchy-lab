const names = {solo: "Solo", manager: "Manager–workers", pipeline: "Sequential pipeline",
  candidates: "Independent candidates", hierarchy: "Two-level hierarchy"};
const metrics = {elapsed_seconds: "Elapsed time", input_tokens: "Input tokens", output_tokens: "Output tokens"};
const taskSelect = document.querySelector("#task");
const metricSelect = document.querySelector("#metric");
const caption = document.querySelector("#chart-caption");
const bars = document.querySelector("#bars");

function render(observations) {
  const task = taskSelect.value;
  const metric = metricSelect.value;
  const timed = metric === "elapsed_seconds";
  const rows = observations.filter(row => row.task === task);
  const maximum = Math.max(...rows.map(row => row[metric]));
  caption.textContent = metrics[metric] + " per " + task + " run" + (timed ? ", in seconds" : "");
  const excluded = rows.some(row => !row.eligible);
  document.querySelector("#exclusion").textContent = excluded
    ? "† The striped bar includes the science candidates run. It failed the worker assignment rule." : "";
  bars.replaceChildren();
  for (const row of rows) {
    const line = document.createElement("div");
    line.className = row.eligible ? "barrow" : "barrow excluded";
    const link = document.createElement("a");
    link.href = "https://github.com/Turbo-lag/agent-hierarchy-lab/tree/main/results/pilot/" + task + "/" + row.architecture;
    link.textContent = names[row.architecture] + (row.eligible ? "" : " †");
    const track = document.createElement("div");
    track.className = "track";
    track.setAttribute("aria-hidden", "true");
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.width = (100 * row[metric] / maximum) + "%";
    track.append(bar);
    const value = document.createElement("strong");
    value.textContent = timed ? row[metric].toFixed(1) + " s" : row[metric].toLocaleString("en-US");
    line.append(link, track, value);
    bars.append(line);
  }
}
try {
  const response = await fetch("data/pilot.json");
  if (!response.ok) throw new Error("Dataset unavailable");
  const {observations} = await response.json();
  for (const select of [taskSelect, metricSelect]) select.addEventListener("change", () => render(observations));
  render(observations);
} catch {
  caption.textContent = "The chart data could not be loaded. Open All observations for the complete results.";
  taskSelect.disabled = metricSelect.disabled = true;
}
