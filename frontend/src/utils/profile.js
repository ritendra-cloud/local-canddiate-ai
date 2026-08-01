export const values = (items = []) => items.map((item) => typeof item === 'string' ? item : item.name || item.title || item.description).filter(Boolean);
export const skillCount = (skills = {}) => Object.values(skills).reduce((total, group) => total + (group?.length || 0), 0);
export const candidate = (profile) => profile?.candidate || {};
