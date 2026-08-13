document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("messages");

  // Conversation history is stateless server-side: we hold prior turns here and
  // send them with each request. Kept in step with the caps in app/routers/api.py
  // — exceeding any of them is a 422, so we trim rather than let the send fail.
  const MAX_HISTORY_TURNS = 10;
  const MAX_HISTORY_CHARS = 10000;
  const MAX_TURN_CHARS = 4000;

  const turns = [];

  // The input is a textarea so a long question stays readable. It starts one row
  // tall and grows with the content; CSS max-height clamps it and takes over
  // with a scrollbar.
  function autosize() {
    input.style.height = "auto";
    input.style.height = `${input.scrollHeight}px`;
  }

  input.addEventListener("input", autosize);
  // Size it once now: the natural `rows="1"` height and the height autosize
  // computes differ by a pixel or two, which would show as a jump on the first
  // keystroke and leave the box a different size after sending than before.
  autosize();

  // A textarea's default is Enter for a newline, which would leave a chat box
  // that can only be sent with the mouse. Swapped: Enter sends, Shift+Enter
  // writes a newline.
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  function historyToSend() {
    const kept = turns.slice(-MAX_HISTORY_TURNS);

    let total = kept.reduce((sum, turn) => sum + turn.content.length, 0);
    while (kept.length && total > MAX_HISTORY_CHARS) {
      total -= kept.shift().content.length;
    }

    // The API requires history to start with a user turn; trimming can leave an
    // assistant turn at the front.
    while (kept.length && kept[0].role !== "user") kept.shift();

    return kept;
  }

  function recordTurn(role, content) {
    turns.push({ role, content: content.slice(0, MAX_TURN_CHARS) });
  }

  function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
  }

  function addMessage(role) {
    const el = document.createElement("div");
    el.className = `message ${role}`;
    messages.appendChild(el);
    scrollToBottom();
    return el;
  }

  function setErrorReply(assistantEl, text = "Something went wrong. Please try again.") {
    assistantEl.textContent = text;
    scrollToBottom();
  }

  // Minted when the page was rendered and short-lived, so a page left open long
  // enough will start getting 401s until it is reloaded. Read per request rather
  // than cached at load, so a refreshed token would be picked up without a reload.
  function chatToken() {
    return document.querySelector('meta[name="chat-token"]')?.content ?? "";
  }

  async function streamReply(message, assistantEl) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${chatToken()}`,
      },
      body: JSON.stringify({ message, history: historyToSend() }),
    });

    if (response.status === 401) {
      setErrorReply(assistantEl, "Your session expired. Please reload the page.");
      return null;
    }

    if (!response.ok || !response.body) {
      setErrorReply(assistantEl);
      return null;
    }

    const outcome = response.headers.get("X-Chat-Outcome");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let reply = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      reply += chunk;
      assistantEl.textContent += chunk;
      scrollToBottom();
    }

    return { reply, outcome };
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addMessage("user").textContent = message;
    input.value = "";
    // Clearing the value does not shrink a grown textarea.
    autosize();
    input.disabled = true;

    const assistantEl = addMessage("assistant");
    try {
      const result = await streamReply(message, assistantEl);
      // Only a real answer enters the history. A refused message must not be
      // recorded: the next request would then be judged against a conversation
      // containing the attack, and one refusal would poison the whole session.
      // Failed turns are skipped for the same reason — an error is not something
      // the assistant said.
      if (result && result.outcome === "answered") {
        recordTurn("user", message);
        recordTurn("assistant", result.reply);
      }
    } catch (err) {
      setErrorReply(assistantEl);
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
});
