document.addEventListener('DOMContentLoaded', () => {
  // Helper: lazy-create the modal container
  function getOrCreateJsonModal() {
    let modalEl = document.getElementById('jsonPreviewModal');
    if (modalEl) return modalEl;

    // build modal structure
    modalEl = document.createElement('div');
    modalEl.id = 'jsonPreviewModal';
    modalEl.className = 'modal';
    modalEl.tabIndex = -1;
    modalEl.setAttribute('role','dialog');
    modalEl.innerHTML = `
      <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Aperçu JSON</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Fermer"></button>
          </div>
          <div class="modal-body"></div>
        </div>
      </div>
    `;
    document.body.appendChild(modalEl);
    return modalEl;
  }

  // 1) Inline toggle logic (▶/▼)
  document.body.addEventListener('click', e => {
    if (!e.target.classList.contains('json-toggle')) return;
    const cell = e.target.closest('.json-modal-json-cell');
    const pre  = cell.querySelector('.json-modal-json-content');
    const open = getComputedStyle(pre).display === 'none';
    pre.style.display    = open ? 'block' : 'none';
    e.target.textContent = open ? '▼' : '▶';
  });


    // 2) Open modal & inject cloned .pre-container
  document.body.addEventListener('click', e => {
    if (!e.target.classList.contains('view-json')) return;
    const cell       = e.target.closest('.json-modal-json-cell');
    const preWrapper = cell.querySelector('.json-modal-pre-container');
    const cloneWrap  = preWrapper.cloneNode(true);
    // force visible
    cloneWrap.style.display = 'block';

    const modalEl   = getOrCreateJsonModal();
    const modalBody = modalEl.querySelector('.modal-body');
    modalBody.innerHTML = '';
    modalBody.appendChild(cloneWrap);
    new bootstrap.Modal(modalEl).show();
  });

    // 3) Copy-button handler
  document.body.addEventListener('click', e => {
    if (!e.target.classList.contains('json-modal-copy-btn')) return;
    const wrapper = e.target.closest('.json-modal-pre-container');
    const pre     = wrapper.querySelector('pre');
    if (!pre) return;
    navigator.clipboard.writeText(pre.textContent.trim())
      .then(() => {
        e.target.textContent = '✓';
        setTimeout(() => e.target.innerHTML = '<i class="fa-regular fa-copy"></i>', 1500);
      })
      .catch(() => {
        e.target.textContent = '✗';
        setTimeout(() => e.target.innerHTML = '<i class="fa-regular fa-copy"></i>', 1500);
      });
  });
});
