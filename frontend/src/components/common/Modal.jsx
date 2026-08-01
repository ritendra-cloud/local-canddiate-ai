import { useEffect } from 'react';
import Button from './Button';
export default function Modal({ title, children, onClose, onConfirm, confirmLabel = 'Confirm' }) {
  useEffect(() => { const escape = (event) => event.key === 'Escape' && onClose(); window.addEventListener('keydown', escape); return () => window.removeEventListener('keydown', escape); }, [onClose]);
  return <div className="modal-backdrop" role="presentation"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><h2 id="modal-title">{title}</h2><p>{children}</p><div className="actions"><Button autoFocus variant="secondary" onClick={onClose}>Cancel</Button><Button variant="danger" onClick={onConfirm}>{confirmLabel}</Button></div></section></div>;
}
