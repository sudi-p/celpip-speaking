const API = "/api";

function getUserName() { return localStorage.getItem("celpip_name") || ""; }
function setUserName(n) { localStorage.setItem("celpip_name", n.trim()); }

function initNameUI() {
  const name = getUserName();

  // Update greeting in navbar
  const greeting = document.getElementById("navbar-greeting");
  if (greeting && name) greeting.textContent = `Hello, ${name}`;

  // Burger / drawer toggle
  const burger  = document.getElementById("navbar-burger");
  const menu    = document.getElementById("navbar-menu");
  const overlay = document.getElementById("navbar-overlay");
  if (burger && menu) {
    const openDrawer = () => {
      menu.classList.add("is-open");
      burger.classList.add("is-open");
      if (overlay) overlay.classList.add("is-open");
    };
    const closeDrawer = () => {
      menu.classList.remove("is-open");
      burger.classList.remove("is-open");
      if (overlay) overlay.classList.remove("is-open");
    };
    burger.addEventListener("click", () => {
      menu.classList.contains("is-open") ? closeDrawer() : openDrawer();
    });
    if (overlay) overlay.addEventListener("click", closeDrawer);
    // Close on nav link click (navigates anyway, but cleans up animation)
    menu.querySelectorAll(".navbar-link").forEach((l) => l.addEventListener("click", closeDrawer));
  }

  // Gate — block page until a name is set
  const gate = document.getElementById("name-gate");
  if (!gate) return;
  if (!name) {
    gate.style.display = "flex";
    document.body.style.overflow = "hidden";
    const gateInput = document.getElementById("gate-name-input");
    const gateBtn   = document.getElementById("gate-submit");
    const dismiss = () => {
      const val = gateInput.value.trim();
      if (!val) { gateInput.classList.add("input-error"); return; }
      gateInput.classList.remove("input-error");
      setUserName(val);
      if (greeting) greeting.textContent = `Hello, ${val}`;
      gate.style.display = "none";
      document.body.style.overflow = "";
    };
    gateBtn.addEventListener("click", dismiss);
    gateInput.addEventListener("keydown", (e) => { if (e.key === "Enter") dismiss(); });
    gateInput.focus();
  }
}

const TASKS = {
  1: { name: "Giving Advice", prep: 30, speak: 90 },
  2: { name: "Personal Experience", prep: 30, speak: 60 },
  3: { name: "Describing a Scene", prep: 30, speak: 60 },
  4: { name: "Making Predictions", prep: 30, speak: 60 },
  5: { name: "Comparing & Persuading", prep: 120, speak: 60 },
  6: { name: "Difficult Situation", prep: 60, speak: 60 },
  7: { name: "Expressing Opinions", prep: 30, speak: 90 },
  8: { name: "Unusual Situation", prep: 30, speak: 60 },
};

function fmtTime(s) {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function countdown(seconds, onTick, onDone) {
  let remaining = seconds;
  onTick(remaining);
  const id = setInterval(() => {
    remaining -= 1;
    onTick(remaining);
    if (remaining <= 0) {
      clearInterval(id);
      onDone();
    }
  }, 1000);
  return id;
}

function renderEvaluation(containerEl, evalObj) {
  const listItems = (arr) =>
    Array.isArray(arr)
      ? arr.map((x) => `<li>${escapeHtml(x)}</li>`).join("")
      : "";

  const issueRows =
    Array.isArray(evalObj.transcript_issues) && evalObj.transcript_issues.length
      ? evalObj.transcript_issues
          .map(
            (it) => `
        <div class="issue-row">
          <div class="issue-type">${escapeHtml(it.type ?? "")}</div>
          <div class="issue-body">
            <div class="issue-quote">&ldquo;${escapeHtml(it.quote ?? "")}&rdquo;</div>
            <div class="issue-problem">${escapeHtml(it.problem ?? "")}</div>
            <div class="issue-fix"><span class="issue-fix-label">Fix:</span> ${escapeHtml(it.fix ?? "")}</div>
          </div>
        </div>`,
          )
          .join("")
      : "<p class='eval-empty'>No specific issues found.</p>";

  containerEl.innerHTML = `
    <div class="eval-section">
      <h3>Fluency</h3><p>${escapeHtml(evalObj.fluency ?? "")}</p>
    </div>
    <div class="eval-section">
      <h3>Grammar</h3><p>${escapeHtml(evalObj.grammar ?? "")}</p>
    </div>
    <div class="eval-section">
      <h3>Vocabulary</h3><p>${escapeHtml(evalObj.vocabulary ?? "")}</p>
    </div>
    <div class="eval-section">
      <h3>Coherence</h3><p>${escapeHtml(evalObj.coherence ?? "")}</p>
    </div>
    <div class="eval-section">
      <h3>Strengths</h3><ul>${listItems(evalObj.strengths)}</ul>
    </div>
    <div class="eval-section">
      <h3>Weaknesses</h3><ul>${listItems(evalObj.weaknesses)}</ul>
    </div>
    <div class="eval-section issues-section">
      <h3>Issues Found in Your Response</h3>
      <div class="issues-list">${issueRows}</div>
    </div>
    <div class="eval-section">
      <h3>Improvements</h3><ul>${listItems(evalObj.improvements)}</ul>
    </div>
    <div class="eval-section">
      <h3>Example Better Response</h3>
      <p class="example-response">${escapeHtml(evalObj.example_better_response ?? "")}</p>
    </div>
  `;
}

async function apiGet(path) {
  const resp = await fetch(`${API}${path}`);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error(err.error || resp.statusText);
  }
  return resp.json();
}

async function apiPost(path, body, isBlob = false) {
  let opts;
  if (body instanceof FormData) {
    opts = { method: "POST", body }; // browser sets Content-Type + boundary automatically
  } else if (isBlob) {
    opts = {
      method: "POST",
      body,
      headers: { "X-Audio-Type": body.type || "audio/webm" },
    };
  } else {
    opts = {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    };
  }
  const resp = await fetch(`${API}${path}`, opts);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error(err.error || resp.statusText);
  }
  return resp.json();
}

async function apiDelete(path) {
  const resp = await fetch(`${API}${path}`, { method: "DELETE" });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    throw new Error(err.error || resp.statusText);
  }
  return resp.json();
}
