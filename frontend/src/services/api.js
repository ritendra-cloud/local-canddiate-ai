const get=(path)=>fetch(path).then(async r=>{if(!r.ok) throw Object.assign(new Error('Request failed'),{status:r.status}); return r.json()});
export const api={health:()=>get('/api/health'),profile:()=>get('/api/profile'),config:()=>get('/api/config/public'),sessions:()=>get('/api/sessions')};
