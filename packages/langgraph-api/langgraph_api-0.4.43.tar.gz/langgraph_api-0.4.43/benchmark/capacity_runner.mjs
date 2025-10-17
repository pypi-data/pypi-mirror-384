/*
 * Adaptive capacity benchmark orchestrator.
 * Ramps TARGET from RAMP_START up to RAMP_END by RAMP_MULTIPLIER.
 * For each level N: optional cleanup → run k6 (N users, 1 run each) → wait summary → decide next.
 * No retries anywhere; errors reduce success rate.
 */

import { execFileSync } from 'node:child_process';
import { readdirSync, readFileSync, writeFileSync, createReadStream } from 'node:fs';
import { join } from 'node:path';
import readline from 'node:readline';
import QuickChart from 'quickchart-js';
import { baseUrlToBaseUrlName } from './capacity_urls.mjs';

function envBool(name, def = false) {
  const v = process.env[name];
  if (v === undefined || v === null) return def;
  return String(v).toLowerCase() === 'true';
}

function envInt(name, def) {
  const v = process.env[name];
  if (!v) return def;
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : def;
}

function envFloat(name, def) {
  const v = process.env[name];
  if (!v) return def;
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : def;
}

const BASE_URL = process.env.BASE_URL;
const LANGSMITH_API_KEY = process.env.LANGSMITH_API_KEY;

const RAMP_START = envInt('RAMP_START', 10);
const RAMP_END = envInt('RAMP_END', 1000);
const RAMP_MULTIPLIER = envFloat('RAMP_MULTIPLIER', 10);
const WAIT_SECONDS = envInt('WAIT_SECONDS', 60);
const SUCCESS_THRESHOLD = envFloat('SUCCESS_THRESHOLD', 0.99);
const CLEAR_BETWEEN_STEPS = envBool('CLEAR_BETWEEN_STEPS', true);
const CLEAR_DELAY_SECONDS = envInt('CLEAR_DELAY_SECONDS', 5);

// Agent params
const DATA_SIZE = envInt('DATA_SIZE', 1000);
const DELAY = envInt('DELAY', 0);
const EXPAND = envInt('EXPAND', 50);
const STEPS = envInt('STEPS', 10);

if (!BASE_URL) {
  console.error('BASE_URL is required');
  process.exit(1);
}
if (!(RAMP_MULTIPLIER > 1)) {
  console.error('RAMP_MULTIPLIER must be > 1');
  process.exit(1);
}

function headers() {
  const h = { 'Content-Type': 'application/json' };
  if (LANGSMITH_API_KEY) h['x-api-key'] = LANGSMITH_API_KEY;
  return h;
}

async function cleanThreads() {
  if (!CLEAR_BETWEEN_STEPS) return;
  const hdrs = headers();
  const searchUrl = `${BASE_URL}/threads/search`;
  let totalDeleted = 0;
  // Loop until no more threads
  while (true) {
    const res = await fetch(searchUrl, {
      method: 'POST',
      headers: hdrs,
      body: JSON.stringify({ limit: 1000 }),
    });
    if (!res.ok) {
      console.error(`Cleanup search failed: ${res.status} ${res.statusText}`);
      break;
    }
    const threads = await res.json();
    if (!Array.isArray(threads) || threads.length === 0) break;
    for (const t of threads) {
      try {
        const del = await fetch(`${BASE_URL}/threads/${t.thread_id}`, {
          method: 'DELETE',
          headers: hdrs,
        });
        if (del.ok) totalDeleted++;
      } catch (e) {
        // Ignore delete errors; do not retry
      }
    }
  }
  if (CLEAR_DELAY_SECONDS > 0) {
    await new Promise((r) => setTimeout(r, CLEAR_DELAY_SECONDS * 1000));
  }
  console.log(`Cleanup completed. Deleted ~${totalDeleted} threads.`);
}

function runK6(target) {
  const env = {
    ...process.env,
    BASE_URL,
    LANGSMITH_API_KEY,
    TARGET: String(target),
    WAIT_SECONDS: String(WAIT_SECONDS),
    SUCCESS_THRESHOLD: String(SUCCESS_THRESHOLD),
    DATA_SIZE: String(DATA_SIZE),
    DELAY: String(DELAY),
    EXPAND: String(EXPAND),
    STEPS: String(STEPS),
  };
  console.log(`Running k6 with TARGET=${target}`);
  // Also write raw JSON stream for per-stage histograms
  const ts = new Date().toISOString().replace(/:/g, '-').replace(/\..+/, '');
  const rawOut = `capacity_raw_t${target}_${ts}.json`;
  // We rely on handleSummary to write capacity_summary_t${TARGET}_<ts>.json
  execFileSync('k6', ['run', '--out', `json=${rawOut}`, 'capacity_k6.js'], {
    cwd: process.cwd(),
    env,
    stdio: 'inherit',
  });
  return { rawOut, ts };
}

function loadSummaryForTarget(target) {
  const files = readdirSync(process.cwd())
    .filter((f) => f.startsWith(`capacity_summary_t${target}_`) && f.endsWith('.json'))
    .sort();
  if (files.length === 0) {
    throw new Error(`No capacity summary file found for target ${target}`);
  }
  const latest = files[files.length - 1];
  const content = readFileSync(join(process.cwd(), latest), 'utf-8');
  return JSON.parse(content);
}

async function main() {
  let n = RAMP_START;
  let lastSuccess = null; // { target, avgDurationSeconds, successRate }
  let failedStep = null; // { target, successRate }

  while (n <= RAMP_END) {
    console.log(`\n=== Capacity step: N=${n} ===`);
    if (CLEAR_BETWEEN_STEPS) {
      console.log('Clearing threads before step...');
      await cleanThreads();
    }

    try {
      const { rawOut, ts } = runK6(n);
      try {
        await generateHistogramsForStage(rawOut, n, ts);
      } catch (e) {
        console.error(`Failed to generate histograms for N=${n}:`, e?.message || e);
      }
    } catch (e) {
      console.error(`k6 run failed at N=${n}:`, e?.message || e);
      // Treat as failure for this step
    }

    let successRate = 0;
    let avgDurationSeconds = null;
    try {
      const summary = loadSummaryForTarget(n);
      const s = summary?.metrics?.successRate; // percent
      successRate = Number.isFinite(s) ? s / 100 : 0;
      avgDurationSeconds = summary?.metrics?.runDuration?.avg ?? null;
      console.log(`Step N=${n} successRate=${(successRate * 100).toFixed(2)}% avgDur=${avgDurationSeconds ?? 'n/a'}s`);
    } catch (e) {
      console.error(`Failed to read summary for N=${n}:`, e?.message || e);
    }

    if (successRate >= SUCCESS_THRESHOLD) {
      lastSuccess = { target: n, avgDurationSeconds, successRate };
      // next n
      const next = Math.floor(n * RAMP_MULTIPLIER);
      if (next <= n) {
        console.log('Next ramp value would not increase; stopping.');
        break;
      }
      n = next;
    } else {
      failedStep = { target: n, avgDurationSeconds, successRate };
      break;
    }
  }

  const ts = new Date().toISOString().replace(/:/g, '-').replace(/\..+/, '');
  const report = {
    baseUrl: BASE_URL,
    baseUrlName: baseUrlToBaseUrlName[BASE_URL],
    timestamp: ts,
    ramp: { start: RAMP_START, end: RAMP_END, multiplier: RAMP_MULTIPLIER },
    waitSeconds: WAIT_SECONDS,
    threshold: SUCCESS_THRESHOLD,
    last_success_target: lastSuccess?.target ?? 0,
    last_success_avg_duration_seconds: lastSuccess?.avgDurationSeconds ?? null,
    last_success_rate: lastSuccess?.successRate ?? null,
    failed_target: failedStep?.target ?? null,
    failed_success_rate: failedStep?.successRate ?? null,
    failed_avg_duration_seconds: failedStep?.avgDurationSeconds ?? null,
  };
  const fname = `capacity_report_${ts}.json`;
  writeFileSync(join(process.cwd(), fname), JSON.stringify(report, null, 2));

  // Export selected fields as GitHub Action outputs if available
  if (process.env.GITHUB_OUTPUT) {
    const out = [
      `last_success_target=${report.last_success_target}`,
      `last_success_avg_duration_seconds=${report.last_success_avg_duration_seconds}`,
      `failed_target=${report.failed_target}`,
      `failed_success_rate=${report.failed_success_rate}`,
      `failed_avg_duration_seconds=${report.failed_avg_duration_seconds}`,
    ].join('\n');
    writeFileSync(process.env.GITHUB_OUTPUT, `${out}\n`, { flag: 'a' });
  }

  console.log('=== Capacity Benchmark Report ===');
  console.log(`Last successful step: ${report.last_success_target}`);
  console.log(`Average duration (s) at success: ${report.last_success_avg_duration_seconds}`);
  console.log(`Failed step: ${report.failed_target} with success rate: ${report.failed_success_rate}`);
}

main().catch((e) => {
  console.error('Fatal error in capacity runner:', e?.stack || e?.message || e);
  process.exit(1);
});

// Build and save histogram charts for one stage from raw K6 JSON
async function generateHistogramsForStage(rawFile, target, ts) {
  // Parse streaming JSONL from k6 --out json
  const metrics = {
    run_duration: [],
    run_pickup_duration: [],
    run_return_duration: [],
    run_insertion_duration: [],
    run_oss_duration: [],
  };

  await new Promise((resolve, reject) => {
    const rl = readline.createInterface({ input: createReadStream(join(process.cwd(), rawFile), { encoding: 'utf-8' }), crlfDelay: Infinity });
    rl.on('line', (line) => {
      try {
        const entry = JSON.parse(line);
        if (entry.type === 'Point') {
          const name = entry.metric;
          if (name in metrics) {
            const v = entry?.data?.value;
            if (Number.isFinite(v)) metrics[name].push(v);
          }
        }
      } catch (_) {
        // ignore parse errors
      }
    });
    rl.on('close', resolve);
    rl.on('error', reject);
  });

  // Build pie chart for component breakdown based on average seconds
  const avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0);
  const avgInsertionS = avg(metrics.run_insertion_duration) / 1000;
  const avgPickupS = avg(metrics.run_pickup_duration) / 1000;
  const avgOssS = avg(metrics.run_oss_duration) / 1000;
  const avgReturnS = avg(metrics.run_return_duration) / 1000;
  const parts = [avgInsertionS, avgPickupS, avgOssS, avgReturnS];
  const totalParts = parts.reduce((a, b) => a + b, 0);
  if (totalParts > 0) {
    const chart = new QuickChart();
    chart.setWidth(700);
    chart.setHeight(500);
    chart.setFormat('png');
    chart.setConfig({
      type: 'pie',
      data: {
        labels: ['Insertion', 'Pickup', 'OSS', 'Return'],
        datasets: [{
          label: `Breakdown of Run Duration (N=${target})`,
          data: parts.map((v) => Number(v.toFixed(4))),
          backgroundColor: [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
          ],
          borderColor: [
            'rgba(255, 99, 132, 1)',
            'rgba(54, 162, 235, 1)',
            'rgba(255, 206, 86, 1)',
            'rgba(75, 192, 192, 1)',
          ],
          borderWidth: 1,
        }],
      },
      options: {
        plugins: {
          title: { display: true, text: `Run Duration Breakdown (s) — N=${target}` },
          legend: { position: 'right' },
          tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${ctx.parsed.toFixed(3)}s` } },
        },
      },
    });
    const pieBuf = await chart.toBinary();
    const piePath = join(process.cwd(), `capacity_pie_breakdown_t${target}_${ts}.png`);
    writeFileSync(piePath, pieBuf);
    console.log(`Saved pie chart: ${piePath}`);
  }
}
