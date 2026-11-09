const form = document.getElementById("analyzeForm");
const textarea = document.getElementById("textToAnalyze");
const charCount = document.getElementById("charCount");
const submitBtn = document.getElementById("submitBtn");
const formError = document.getElementById("formError");
const resultPanel = document.getElementById("resultPanel");
const resultEmpty = document.getElementById("resultEmpty");
const resultData = document.getElementById("resultData");
const dominantEmoji = document.getElementById("dominantEmoji");
const dominantName = document.getElementById("dominantName");
const confidenceText = document.getElementById("confidenceText");
const wordCount = document.getElementById("wordCount");

const EMOTIONS = ["anger", "disgust", "fear", "joy", "sadness"];

function updateCount() {
    charCount.textContent = textarea.value.length.toLocaleString();
}

function setLoading(loading) {
    submitBtn.disabled = loading;
    submitBtn.classList.toggle("is-loading", loading);
    submitBtn.querySelector(".button-label").textContent = loading
        ? "Reading the room…"
        : "Analyze emotion";
    resultPanel.setAttribute("aria-busy", String(loading));
}

function showError(message) {
    formError.textContent = message;
    formError.hidden = false;
}

function clearError() {
    formError.hidden = true;
    formError.textContent = "";
}

function renderResult(data) {
    resultEmpty.hidden = true;
    resultData.hidden = false;
    resultPanel.classList.remove("is-empty");

    dominantEmoji.textContent = data.emoji || "😐";
    dominantName.textContent = data.dominant_emotion || "neutral";
    const confidence = Math.round((data.confidence || 0) * 100);
    confidenceText.textContent = `${confidence}% confidence · ${data.word_count || 0} words`;
    wordCount.textContent = `${data.word_count || 0} words analyzed`;

    for (const emotion of EMOTIONS) {
        const row = document.querySelector(`.bar-row[data-emotion="${emotion}"]`);
        if (!row) continue;
        const score = Number(data.scores?.[emotion] || 0);
        const percentage = Math.max(0, Math.min(100, score * 100));
        row.querySelector("[data-value]").textContent = `${percentage.toFixed(1)}%`;
        const fill = row.querySelector(".bar-fill");
        fill.style.width = "0%";
        requestAnimationFrame(() => {
            fill.style.width = `${percentage}%`;
        });
    }

    if (window.matchMedia("(max-width: 900px)").matches) {
        resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

async function analyze(text) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20_000);
    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
            signal: controller.signal,
        });
        const contentType = response.headers.get("content-type") || "";
        const data = contentType.includes("application/json")
            ? await response.json()
            : null;

        if (!data) throw new Error("The server returned an unexpected response.");
        if (!response.ok || !data.ok) {
            throw new Error(data.error || "Could not analyze that text.");
        }
        return data;
    } finally {
        clearTimeout(timeout);
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();

    const text = textarea.value.trim();
    if (!text) {
        showError("Enter a sentence or two first.");
        textarea.focus();
        return;
    }
    if (text.length > 5000) {
        showError("Please keep the text under 5,000 characters.");
        return;
    }

    setLoading(true);
    try {
        const data = await analyze(text);
        renderResult(data);
    } catch (error) {
        if (error.name === "AbortError") {
            showError("The request timed out. Please try again.");
        } else {
            showError(error.message || "Could not analyze that text.");
        }
    } finally {
        setLoading(false);
    }
});

textarea.addEventListener("input", updateCount);

textarea.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        form.requestSubmit();
    }
});

for (const button of document.querySelectorAll(".sample")) {
    button.addEventListener("click", () => {
        textarea.value = button.dataset.text || "";
        updateCount();
        clearError();
        textarea.focus();
    });
}

updateCount();
