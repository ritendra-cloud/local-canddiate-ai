export async function streamChat({ message, sessionId, signal, onEvent }) {
  const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, session_id: sessionId }), signal });
  if (!response.ok) throw new Error('The local chat service could not complete the request.');
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = '';
  while (true) {
    const { value, done } = await reader.read(); if (done) break;
    buffer += decoder.decode(value, { stream: true }); const blocks = buffer.split('\n\n'); buffer = blocks.pop();
    blocks.forEach((block) => { const type = block.match(/^event: (.+)$/m)?.[1]; const raw = block.match(/^data: (.+)$/m)?.[1]; if (type && raw) onEvent(type, JSON.parse(raw)); });
  }
}
