document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const messages = document.getElementById("messages");

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

  function setErrorReply(assistantEl) {
    assistantEl.textContent = "Something went wrong. Please try again.";
    scrollToBottom();
  }

  async function streamReply(message, assistantEl) {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!response.ok || !response.body) {
      setErrorReply(assistantEl);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      assistantEl.textContent += decoder.decode(value, { stream: true });
      scrollToBottom();
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addMessage("user").textContent = message;
    input.value = "";
    input.disabled = true;

    const assistantEl = addMessage("assistant");
    try {
      await streamReply(message, assistantEl);
    } catch (err) {
      setErrorReply(assistantEl);
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
});
