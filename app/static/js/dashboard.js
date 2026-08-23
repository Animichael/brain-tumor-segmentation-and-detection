/**
 * Dashboard sidebar behavior: desktop collapse-to-icons (persisted in
 * localStorage, matching the anti-flash logic in base.html) and the mobile
 * off-canvas drawer.
 */
document.addEventListener('DOMContentLoaded', () => {
  initSidebarCollapse();
  initSidebarMobile();
  initScanDropzone();
  initDeleteConfirm();
});

function initSidebarCollapse() {
  const btn = document.getElementById('sidebar-collapse-btn');
  if (!btn) return;

  const STORAGE_KEY = 'sidebarCollapsed';

  btn.addEventListener('click', () => {
    const isCollapsed = document.documentElement.classList.toggle('sidebar-collapsed');
    localStorage.setItem(STORAGE_KEY, String(isCollapsed));
  });
}

function initSidebarMobile() {
  const sidebar = document.getElementById('dashboard-sidebar');
  const toggleBtn = document.getElementById('sidebar-mobile-toggle');
  const backdrop = document.getElementById('sidebar-mobile-backdrop');
  if (!sidebar || !toggleBtn) return;

  const open = () => {
    sidebar.classList.add('is-mobile-open');
    backdrop?.classList.add('is-open');
  };
  const close = () => {
    sidebar.classList.remove('is-mobile-open');
    backdrop?.classList.remove('is-open');
  };

  toggleBtn.addEventListener('click', open);
  backdrop?.addEventListener('click', close);
  sidebar.querySelectorAll('a').forEach((link) => link.addEventListener('click', close));
}

/**
 * MRI scan dropzone: click-to-browse, drag-and-drop, an image preview with a
 * clear button, and a submitting/processing state on the analyze button.
 */
function initScanDropzone() {
  const dropzone = document.getElementById('scan-dropzone');
  const input = document.getElementById('scan_image');
  const form = document.getElementById('scan-upload-form');
  if (!dropzone || !input || !form) return;

  const content = document.getElementById('dropzone-content');
  const preview = document.getElementById('dropzone-preview');
  const previewImg = document.getElementById('dropzone-preview-img');
  const filenameEl = document.getElementById('dropzone-filename');
  const clearBtn = document.getElementById('dropzone-clear');
  const scanning = document.getElementById('dropzone-scanning');
  const submitBtn = document.getElementById('scan-upload-submit');

  function showPreview(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      previewImg.src = reader.result;
      filenameEl.textContent = file.name;
      content.hidden = true;
      preview.hidden = false;
    };
    reader.readAsDataURL(file);
  }

  function clearSelection() {
    input.value = '';
    preview.hidden = true;
    content.hidden = false;
  }

  input.addEventListener('change', () => showPreview(input.files[0]));

  clearBtn.addEventListener('click', (event) => {
    event.preventDefault();
    clearSelection();
  });

  ['dragenter', 'dragover'].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add('is-dragover');
    });
  });

  ['dragleave', 'drop'].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove('is-dragover');
    });
  });

  dropzone.addEventListener('drop', (event) => {
    const file = event.dataTransfer.files[0];
    if (file) {
      input.files = event.dataTransfer.files;
      showPreview(file);
    }
  });

  form.addEventListener('submit', (event) => {
    if (!input.files.length) return; // let native "required" validation handle it

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.querySelector('span').textContent = 'Analyzing…';
    }

    // Swap the dropzone into a "scanning" state so the spinner sits right on
    // the image the doctor just selected, not just the button.
    content.hidden = true;
    preview.hidden = true;
    if (scanning) scanning.hidden = false;
  });
}

/**
 * Results table row deletion: intercepts the delete form's submit, confirms
 * via a centered SweetAlert2 dialog, and only submits if the user confirms.
 */
function initDeleteConfirm() {
  document.querySelectorAll('.delete-result-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      event.preventDefault();
      if (typeof appAlert === 'undefined') {
        form.submit();
        return;
      }

      const name = form.dataset.confirmName || 'this record';
      appAlert
        .fire({
          icon: 'warning',
          title: 'Delete this scan result?',
          text: `This will permanently remove the scan and prediction for ${name}. This cannot be undone.`,
          showCancelButton: true,
          confirmButtonText: 'Delete',
          cancelButtonText: 'Cancel',
          confirmButtonColor: '#c0392b',
          reverseButtons: true,
        })
        .then((result) => {
          if (result.isConfirmed) {
            form.submit();
          }
        });
    });
  });
}
