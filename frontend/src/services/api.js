const request = async (path, options = {}) => {
  const response = await fetch(path, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const safe = payload.error || payload.detail?.error;
    const error = new Error(safe?.message || 'The local service could not complete that request.');
    error.code = safe?.code;
    error.retryable = safe?.retryable;
    error.status = response.status;
    throw error;
  }
  return payload;
};
const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
export const api = {
  health: () => request('/api/health'), profile: () => request('/api/profile'), config: () => request('/api/config/public'),
  sessions: () => request('/api/sessions'), session: (id) => request(`/api/sessions/${id}`),
  deleteSession: (id) => request(`/api/sessions/${id}`, { method: 'DELETE' }), clearSessions: () => request('/api/sessions', { method: 'DELETE' }),
  analyzeJob: (payload) => request('/api/job-match', json('POST', payload)), analyses: () => request('/api/job-analyses'),
  analysis: (id) => request(`/api/job-analyses/${id}`), deleteAnalysis: (id) => request(`/api/job-analyses/${id}`, { method: 'DELETE' }),
  clearAnalyses: () => request('/api/job-analyses', { method: 'DELETE' }),
};
