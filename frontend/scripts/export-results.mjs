import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = path.resolve(here, "..");
const repoDir = path.resolve(frontendDir, "..");
const outputDir = path.join(frontendDir, "public", "data");
fs.mkdirSync(outputDir, { recursive: true });

function readJson(relativePath) {
  const absolutePath = path.join(repoDir, relativePath);
  if (!fs.existsSync(absolutePath)) return { available: false, source: relativePath, data: null };
  try {
    return { available: true, source: relativePath, data: JSON.parse(fs.readFileSync(absolutePath, "utf8")) };
  } catch (error) {
    return { available: false, source: relativePath, data: null, error: String(error) };
  }
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (char === '"') quoted = false;
      else field += char;
    } else if (char === '"') quoted = true;
    else if (char === ",") { row.push(field); field = ""; }
    else if (char === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += char;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  const headers = (rows.shift() || []).map((value) => value.trim());
  return rows.filter((values) => values.some((value) => value.trim() !== "")).map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}

function readCsv(relativePath) {
  const absolutePath = path.join(repoDir, relativePath);
  if (!fs.existsSync(absolutePath)) return { available: false, source: relativePath, rows: [] };
  try {
    return { available: true, source: relativePath, rows: parseCsv(fs.readFileSync(absolutePath, "utf8")) };
  } catch (error) {
    return { available: false, source: relativePath, rows: [], error: String(error) };
  }
}

const finalJson = readJson("results/final_results.json");
const finalCsv = readCsv("results/final_results.csv");
const perClass = readCsv("results/per_class_metrics.csv");
const featureCurve = readCsv("results/accuracy_vs_features.csv");
const stability = readCsv("results/feature_stability.csv");
const dataset = readJson("data/processed/dataset_build_summary.json");

let experimentResults = null;
let experimentSource = "results/final_results.csv";
if (finalJson.available && finalJson.data?.results) {
  experimentResults = finalJson.data.results;
  experimentSource = finalJson.source;
} else if (finalCsv.available) {
  experimentResults = finalCsv.rows;
}

const evaluation = {
  available: Boolean(experimentResults),
  source: experimentSource,
  results: experimentResults,
  seeds: finalJson.available ? (finalJson.data.seeds ?? null) : null,
  files: {
    finalResultsCsv: finalCsv.available,
    perClassMetrics: perClass.available,
    accuracyVsFeatures: featureCurve.available,
    featureStability: stability.available,
  },
  perClassMetrics: perClass.available ? perClass.rows : null,
  featureCurve: featureCurve.available ? featureCurve.rows : null,
  featureStability: stability.available ? stability.rows : null,
  unavailableSources: [
    ...(!finalJson.available && !finalCsv.available ? ["results/final_results.csv", "results/final_results.json"] : []),
    ...(!perClass.available ? [perClass.source] : []),
    ...(!featureCurve.available ? [featureCurve.source] : []),
    ...(!stability.available ? [stability.source] : []),
  ],
};

fs.writeFileSync(path.join(outputDir, "evaluation.json"), `${JSON.stringify(evaluation, null, 2)}\n`);
fs.writeFileSync(path.join(outputDir, "dataset-summary.json"), `${JSON.stringify(dataset, null, 2)}\n`);
console.log(`Exported evaluation.json (${evaluation.available ? `source: ${experimentSource}` : "evaluation unavailable"})`);
console.log(`Exported dataset-summary.json (${dataset.available ? `source: ${dataset.source}` : "dataset summary unavailable"})`);
if (evaluation.unavailableSources.length) console.log(`Unavailable result sources: ${evaluation.unavailableSources.join(", ")}`);
