/**
 * A dialog, using the element the platform already has.
 *
 * `<dialog>` gives focus trapping, Escape to close, inertness of the page
 * behind it and the top layer, all without a library. Reimplementing those in
 * React is how modals end up unusable with a keyboard.
 */

import { useEffect, useRef, type ReactNode } from 'react'

export function Modal({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}) {
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  }, [open])

  return (
    <dialog ref={dialog} onClose={onClose} onCancel={onClose}>
      <div className="dialog-head">
        <strong>{title}</strong>
        <button className="quiet" onClick={onClose} aria-label="close">
          ×
        </button>
      </div>
      {children}
    </dialog>
  )
}
