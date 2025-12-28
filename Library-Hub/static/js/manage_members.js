document.addEventListener('DOMContentLoaded', function(){
  const form = document.querySelector('form');
  if(!form) return;
  const previewBtn = document.createElement('button');
  previewBtn.type = 'button';
  previewBtn.className = 'btn';
  previewBtn.textContent = 'Review & Confirm';
  form.appendChild(previewBtn);

  // modal
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.display = 'none';
  modal.innerHTML = `
    <div class="modal-content">
      <h3>Confirm membership changes</h3>
      <div id="previewList" style="max-height:300px;overflow:auto"></div>
      <div style="margin-top:12px;display:flex;gap:8px;justify-content:flex-end">
        <button id="cancelPreview" class="btn">Cancel</button>
        <button id="confirmPreview" class="btn btn-primary">Confirm</button>
      </div>
    </div>`;
  document.body.appendChild(modal);

  previewBtn.addEventListener('click', function(){
    const checked = Array.from(form.querySelectorAll('input[name="user_ids"]:checked'));
    if(checked.length===0){
      alert('Please select at least one user to add.');
      return;
    }
    const preview = document.getElementById('previewList');
    preview.innerHTML = '';
    checked.forEach(cb=>{
      const id = cb.value;
      const name = cb.parentElement.querySelector('strong').textContent;
      const role = form.querySelector(`select[name="role_${id}"]`).value;
      const node = document.createElement('div');
      node.textContent = `${name} — ${role}`;
      preview.appendChild(node);
    });
    modal.style.display = 'block';
  });

  document.getElementById('cancelPreview').addEventListener('click', function(){ modal.style.display='none'; });
  document.getElementById('confirmPreview').addEventListener('click', function(){ modal.style.display='none'; form.submit(); });
});