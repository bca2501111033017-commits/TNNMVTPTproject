/* =========================================================================
   EduGenie frontend logic
   No frameworks - plain DOM manipulation, talking only to the FastAPI
   backend via fetch(). Never touches the Gemini API directly.
   ========================================================================= */

const TASKS = {
  explain: {
    title: "Explain a concept",
    description: "Enter any topic and EduGenie will break it down in simple terms.",
    endpoint: "/explain",
    buildFields: () => `
      <label class="field-label" for="field-topic">Topic</label>
      <input type="text" id="field-topic" name="topic" placeholder="Enter a topic to explain..." maxlength="300" />
    `,
    buildPayload: () => ({ topic: getValue("field-topic") }),
    render: (data) => renderProseCard("Explanation", data.explanation),
  },

  qa: {
    title: "Ask a question",
    description: "Ask any academic or general educational question and get a concise answer.",
    endpoint: "/qa",
    buildFields: () => `
      <label class="field-label" for="field-question">Question</label>
      <textarea id="field-question" name="question" placeholder="Ask your question..." maxlength="1000"></textarea>
    `,
    buildPayload: () => ({ question: getValue("field-question") }),
    render: (data) => renderProseCard("Answer", data.answer),
  },

  quiz: {
    title: "Generate a quiz",
    description: "Enter a topic, or paste educational text, to generate a 3-question quiz.",
    endpoint: "/quiz",
    buildFields: () => `
      <div class="mode-toggle" id="quiz-mode-toggle">
        <button type="button" class="is-active" data-mode="topic">By topic</button>
        <button type="button" data-mode="text">By pasting text</button>
      </div>
      <div id="quiz-topic-field">
        <label class="field-label" for="field-quiz-topic">Topic</label>
        <input type="text" id="field-quiz-topic" name="topic" placeholder="Enter a topic or educational text..." maxlength="300" />
      </div>
      <div id="quiz-text-field" hidden>
        <label class="field-label" for="field-quiz-text">Educational text</label>
        <textarea id="field-quiz-text" name="text" placeholder="Paste the passage to quiz on..." maxlength="6000"></textarea>
      </div>
    `,
    afterRender: () => {
      const toggle = document.getElementById("quiz-mode-toggle");
      const topicField = document.getElementById("quiz-topic-field");
      const textField = document.getElementById("quiz-text-field");
      toggle.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-mode]");
        if (!btn) return;
        toggle.querySelectorAll("button").forEach((b) => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        const mode = btn.dataset.mode;
        topicField.hidden = mode !== "topic";
        textField.hidden = mode !== "text";
      });
    },
    buildPayload: () => {
      const textField = document.getElementById("quiz-text-field");
      const usingText = !textField.hidden;
      if (usingText) {
        return { text: getValue("field-quiz-text") };
      }
      return { topic: getValue("field-quiz-topic") };
    },
    render: (data) => renderQuizCard(data),
  },

  summary: {
    title: "Summarize a passage",
    description: "Paste a long educational passage and get a concise, easy-to-read summary.",
    endpoint: "/summarize",
    buildFields: () => `
      <label class="field-label" for="field-summary-text">Text</label>
      <textarea id="field-summary-text" name="text" placeholder="Paste the text you want to summarize..." maxlength="12000"></textarea>
    `,
    buildPayload: () => ({ text: getValue("field-summary-text") }),
    render: (data) => renderProseCard("Summary", data.summary),
  },

  path: {
    title: "Personalized learning path",
    description: "Tell EduGenie a topic and your level, and get a Beginner \u2192 Advanced roadmap.",
    endpoint: "/learn/recommendations",
    buildFields: () => `
      <div class="field-row">
        <div>
          <label class="field-label" for="field-path-topic">Topic</label>
          <input type="text" id="field-path-topic" name="topic" placeholder="e.g. SQL, Python, Data Structures..." maxlength="300" />
        </div>
        <div>
          <label class="field-label" for="field-path-level">Current level</label>
          <select id="field-path-level" name="level">
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
        </div>
      </div>
    `,
    buildPayload: () => ({
      topic: getValue("field-path-topic"),
      level: getValue("field-path-level"),
    }),
    render: (data) => renderLearningPathCard(data),
  },
};

let currentTask = "explain";

/* -------------------------------------------------------------------------
   DOM helpers
   ------------------------------------------------------------------------- */
function getValue(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : "";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

/* Turn simple Markdown-ish text (Gemini output) into safe HTML: paragraphs,
   bullet lists ("- " or "* "), and **bold** spans. Nothing fancy on purpose,
   this keeps the beginner-friendly project easy to follow. */
function formatProse(text) {
  const lines = (text || "").split("\n");
  let html = "";
  let inList = false;

  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };

  for (let rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      continue;
    }

    const bulletMatch = line.match(/^[-*]\s+(.*)/);
    const headingMatch = line.match(/^#{1,4}\s+(.*)/);

    if (headingMatch) {
      closeList();
      html += `<h4>${inlineFormat(headingMatch[1])}</h4>`;
    } else if (bulletMatch) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += `<li>${inlineFormat(bulletMatch[1])}</li>`;
    } else {
      closeList();
      html += `<p>${inlineFormat(line)}</p>`;
    }
  }
  closeList();
  return html;
}

function inlineFormat(text) {
  let safe = escapeHtml(text);
  safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  return safe;
}

/* -------------------------------------------------------------------------
   Task switching
   ------------------------------------------------------------------------- */
function selectTask(taskKey) {
  currentTask = taskKey;
  const task = TASKS[taskKey];

  document.querySelectorAll(".task-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.task === taskKey);
  });

  document.getElementById("task-title").textContent = task.title;
  document.getElementById("task-description").textContent = task.description;
  document.getElementById("dynamic-fields").innerHTML = task.buildFields();

  if (typeof task.afterRender === "function") {
    task.afterRender();
  }

  hideError();
  resetResultArea();
}

function resetResultArea() {
  const resultArea = document.getElementById("result-area");
  resultArea.innerHTML = `
    <div class="result-placeholder" id="result-placeholder">
      <p>Your results will appear here once you click <strong>Generate</strong>.</p>
    </div>
  `;
}

/* -------------------------------------------------------------------------
   Error banner
   ------------------------------------------------------------------------- */
function showError(message) {
  const banner = document.getElementById("error-banner");
  banner.textContent = message;
  banner.hidden = false;
}

function hideError() {
  const banner = document.getElementById("error-banner");
  banner.hidden = true;
  banner.textContent = "";
}

/* -------------------------------------------------------------------------
   Client-side validation per task (keeps friendly messages instant)
   ------------------------------------------------------------------------- */
function validatePayload(taskKey, payload) {
  if (taskKey === "explain" && !payload.topic) return "Please enter a topic to explain.";
  if (taskKey === "qa" && !payload.question) return "Please enter a question.";
  if (taskKey === "summary" && !payload.text) return "Please paste some text to summarize.";
  if (taskKey === "path" && !payload.topic) return "Please enter a topic for the learning path.";
  if (taskKey === "quiz" && !payload.topic && !payload.text) {
    return "Please enter a topic or paste some text for the quiz.";
  }
  return null;
}

/* -------------------------------------------------------------------------
   Form submission
   ------------------------------------------------------------------------- */
async function handleSubmit(event) {
  event.preventDefault();
  hideError();

  const task = TASKS[currentTask];
  const payload = task.buildPayload();

  const validationError = validatePayload(currentTask, payload);
  if (validationError) {
    showError(validationError);
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(task.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    let data;
    try {
      data = await response.json();
    } catch (parseErr) {
      throw new Error("Unable to connect to the server.");
    }

    if (!response.ok) {
      throw new Error(data.error || "Something went wrong. Please try again.");
    }

    task.render(data);
  } catch (err) {
    showError(err.message || "Unable to connect to the server.");
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  const btn = document.getElementById("generate-btn");
  const label = btn.querySelector(".btn-label");
  btn.disabled = isLoading;
  btn.classList.toggle("is-loading", isLoading);
  label.textContent = isLoading ? "Generating…" : "Generate";
}

/* -------------------------------------------------------------------------
   Renderers
   ------------------------------------------------------------------------- */
function renderProseCard(heading, text) {
  const resultArea = document.getElementById("result-area");
  resultArea.innerHTML = `
    <article class="result-card">
      <h3>${escapeHtml(heading)}</h3>
      ${formatProse(text)}
    </article>
  `;
}

function renderQuizCard(data) {
  const resultArea = document.getElementById("result-area");
  const questions = data.questions || [];

  const questionsHtml = questions
    .map((q, qIndex) => {
      const optionsHtml = q.options
        .map((opt, oIndex) => `
          <label class="quiz-option" data-question="${qIndex}" data-option="${escapeHtml(opt)}">
            <input type="radio" name="quiz-q${qIndex}" value="${escapeHtml(opt)}" />
            <span>${escapeHtml(opt)}</span>
          </label>
        `)
        .join("");

      return `
        <div class="quiz-question" data-question-index="${qIndex}" data-correct="${escapeHtml(q.correct_answer)}">
          <fieldset>
            <legend class="quiz-question-title">${qIndex + 1}. ${escapeHtml(q.question)}</legend>
            <div class="quiz-options">${optionsHtml}</div>
          </fieldset>
          <div class="quiz-status" data-status-for="${qIndex}"></div>
        </div>
      `;
    })
    .join("");

  resultArea.innerHTML = `
    <article class="result-card">
      <h3>Quiz</h3>
      <div id="quiz-score-banner"></div>
      <form id="quiz-form">
        ${questionsHtml}
        <button type="submit" class="quiz-submit-btn" id="quiz-submit-btn">Submit Quiz</button>
      </form>
    </article>
  `;

  document.getElementById("quiz-form").addEventListener("submit", (e) => {
    e.preventDefault();
    gradeQuiz(questions.length);
  });
}

function gradeQuiz(totalQuestions) {
  let score = 0;

  document.querySelectorAll(".quiz-question").forEach((questionEl) => {
    const qIndex = questionEl.dataset.questionIndex;
    const correctAnswer = questionEl.dataset.correct;
    const selected = questionEl.querySelector(`input[name="quiz-q${qIndex}"]:checked`);
    const statusEl = questionEl.querySelector(`[data-status-for="${qIndex}"]`);

    questionEl.querySelectorAll(".quiz-option").forEach((optionLabel) => {
      const optionValue = optionLabel.dataset.option;
      optionLabel.classList.remove("is-correct", "is-incorrect");
      if (optionValue === correctAnswer) {
        optionLabel.classList.add("is-correct");
      } else if (selected && optionValue === selected.value) {
        optionLabel.classList.add("is-incorrect");
      }
    });

    if (selected && selected.value === correctAnswer) {
      score += 1;
      statusEl.textContent = "Correct!";
      statusEl.className = "quiz-status correct";
    } else if (selected) {
      statusEl.textContent = `Incorrect. Correct answer: ${correctAnswer}`;
      statusEl.className = "quiz-status incorrect";
    } else {
      statusEl.textContent = `Not answered. Correct answer: ${correctAnswer}`;
      statusEl.className = "quiz-status incorrect";
    }
  });

  document.getElementById("quiz-score-banner").innerHTML = `
    <div class="quiz-score-banner">
      <span class="score-value">${score} / ${totalQuestions}</span>
      <span>correct</span>
    </div>
  `;

  document.getElementById("quiz-submit-btn").disabled = true;
  document.querySelectorAll("#quiz-form input[type=radio]").forEach((el) => (el.disabled = true));
}

function renderLearningPathCard(data) {
  const resultArea = document.getElementById("result-area");
  const stages = data.stages || [];
  const resources = data.resources || [];
  const tips = data.tips || [];

  const stagesHtml = stages
    .map(
      (stage) => `
        <div class="path-stage">
          <div class="path-stage-label">
            <span class="path-stage-name">${escapeHtml(stage.stage || "")}</span>
            <span class="path-stage-timeline">${escapeHtml(stage.timeline || "")}</span>
          </div>
          <ul class="path-topics">
            ${(stage.topics || []).map((t) => `<li>${escapeHtml(t)}</li>`).join("")}
          </ul>
        </div>
      `
    )
    .join("");

  const resourcesHtml = resources
    .map(
      (r) => `
        <div class="resource-chip">
          <span class="resource-type">${escapeHtml(r.type || "Resource")}</span>
          ${escapeHtml(r.title || "")}
        </div>
      `
    )
    .join("");

  const tipsHtml = tips.map((t) => `<li>${escapeHtml(t)}</li>`).join("");

  resultArea.innerHTML = `
    <article class="result-card">
      <h3>Learning path: ${escapeHtml(data.topic || "")}</h3>
      <p>Starting level: <strong>${escapeHtml(data.current_level || "Beginner")}</strong></p>
      ${stagesHtml}
      ${resources.length ? `<h4>Resources</h4><div class="resource-grid">${resourcesHtml}</div>` : ""}
      ${tips.length ? `<h4>Tips</h4><ul>${tipsHtml}</ul>` : ""}
    </article>
  `;
}

/* -------------------------------------------------------------------------
   Health check (shown in the header)
   ------------------------------------------------------------------------- */
async function checkHealth() {
  const dot = document.getElementById("status-dot");
  const text = document.getElementById("status-text");
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error("down");
    dot.classList.add("is-ok");
    text.textContent = "Service online";
  } catch (err) {
    dot.classList.add("is-down");
    text.textContent = "Service unavailable";
  }
}

/* -------------------------------------------------------------------------
   Init
   ------------------------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("task-rail").addEventListener("click", (e) => {
    const btn = e.target.closest(".task-btn");
    if (!btn) return;
    selectTask(btn.dataset.task);
  });

  document.getElementById("task-form").addEventListener("submit", handleSubmit);

  selectTask("explain");
  checkHealth();
});
