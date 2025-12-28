// Minimal interactivity for the Create Community enterprise page
// Features: drag & drop image upload, preview, validation, character counter, live summary update, submit loading

document.addEventListener('DOMContentLoaded', function () {
  const desc = document.getElementById('description');
  const descCount = document.getElementById('desc-count');
  const nameInput = document.getElementById('name');
  const summaryName = document.getElementById('summary-name');
  const summaryDesc = document.getElementById('summary-desc');
  const preview = document.getElementById('preview');
  const uploadArea = document.getElementById('upload-area');
  const fileInput = document.getElementById('photo');
  const summaryAvatar = document.getElementById('summary-avatar');
  const createBtn = document.getElementById('create-btn');

  // Character counter for description
  if (desc && descCount) {
    function updateCount() {
      descCount.textContent = desc.value.length;
      summaryDesc.textContent = desc.value || '(Short description)';
    }
    desc.addEventListener('input', updateCount);
    updateCount();
  }

  // Live name update
  if (nameInput && summaryName) {
    nameInput.addEventListener('input', function () {
      summaryName.textContent = nameInput.value || '(Community name)';
    });
  }

  // Upload interactions
  function showError(msg) {
    const err = document.querySelector('.error[data-for="photo"]');
    if (err) err.textContent = msg;
  }

  function clearError() {
    const err = document.querySelector('.error[data-for="photo"]');
    if (err) err.textContent = '';
  }

  function showPreview(file) {
    preview.innerHTML = '';
    const img = document.createElement('img');
    img.alt = 'Community image preview';
    img.src = URL.createObjectURL(file);
    img.onload = () => URL.revokeObjectURL(img.src);
    preview.appendChild(img);
    summaryAvatar.style.backgroundImage = `url(${img.src})`;
  }

  // drag & drop
  ;['dragenter','dragover'].forEach(ev => uploadArea.addEventListener(ev, function (e) { e.preventDefault(); e.stopPropagation(); uploadArea.classList.add('dragover'); }));
  ;['dragleave','drop'].forEach(ev => uploadArea.addEventListener(ev, function (e) { e.preventDefault(); e.stopPropagation(); uploadArea.classList.remove('dragover'); }));

  uploadArea.addEventListener('drop', function (e) {
    const dt = e.dataTransfer;
    if (!dt || !dt.files || dt.files.length === 0) return;
    handleFile(dt.files[0]);
  });

  fileInput.addEventListener('change', function () {
    if (fileInput.files && fileInput.files[0]) {
      handleFile(fileInput.files[0]);
    }
  });

  document.getElementById('choose-file')?.addEventListener('click', function (e) {
    e.preventDefault(); fileInput.click();
  });

  function handleFile(file) {
    clearError();
    if (file.size > (2 * 1024 * 1024)) {
      showError('File is too large. Maximum allowed is 2 MB.');
      fileInput.value = '';
      return;
    }
    const allowed = ['image/png','image/jpeg','image/gif'];
    if (!allowed.includes(file.type)) {
      showError('Unsupported file type. Allowed: PNG, JPG, GIF.');
      fileInput.value = '';
      return;
    }
    showPreview(file);
  }

  // Submit loading state and simple inline validation
  const form = document.querySelector('.create-form');
  form.addEventListener('submit', function (e) {
    // basic client-side validation
    const name = nameInput.value.trim();
    if (!name) {
      e.preventDefault();
      const err = document.querySelector('.error[data-for="name"]');
      if (err) err.textContent = 'Community name is required.';
      nameInput.focus();
      return;
    }
    // show loading state
    createBtn.disabled = true;
    createBtn.textContent = 'Creating...';
  });

});