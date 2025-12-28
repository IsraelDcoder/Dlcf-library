document.addEventListener('DOMContentLoaded', function(){
  const socket = io();
  const listEl = document.getElementById('live-list');
  const btnStart = document.getElementById('btn-start-live');
  const titleInput = document.getElementById('live-title');

  function refreshList(){
    fetch('/live/now').then(r=>r.json()).then(data=>{
      if(!data || data.length===0){
        listEl.innerHTML = '<div class="muted">No recent sessions</div>';
        return;
      }
      listEl.innerHTML = '';
      data.forEach(s=>{
        const el = document.createElement('div');
        el.className = 'live-item';
        el.innerHTML = `<strong>${s.title}</strong> <span class="muted">by ${s.host||'—'}</span> ` +
                       (s.is_live? '<span class="live-badge"><span class="dot"></span> Live Now</span>' : `<span class="muted">ended</span>`) +
                       ` <div class="live-actions">` +
                       (s.is_live? `<button data-id="${s.id}" class="btn btn-sm btn-outline btn-end">End</button>` : `<button data-id="${s.id}" class="btn btn-sm btn-outline btn-save">Save</button>`) +
                       (s.is_live? '' : `<label class="btn btn-sm btn-outline" style="margin-left:6px;cursor:pointer"><input type="file" data-id="${s.id}" class="live-upload-input" style="display:none"> Upload</label>`) +
                       `</div>`;
        listEl.appendChild(el);
      });
    }).catch(()=>{ listEl.innerHTML = '<div class="muted">Failed to load sessions</div>' });
  }

  btnStart && btnStart.addEventListener('click', function(){
    const title = titleInput.value || '';
    const q = title ? ('?title=' + encodeURIComponent(title)) : '';
    window.location.href = '/admin/live/new' + q;
  });

  listEl && listEl.addEventListener('click', function(e){
    if(e.target.matches('.btn-end')){
      const id = e.target.getAttribute('data-id');
      fetch(`/live/end/${id}`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({auto_publish:false})}).then(r=>r.json()).then(()=>refreshList());
    }
    if(e.target.matches('.btn-save')){
      const id = e.target.getAttribute('data-id');
      fetch(`/live/save/${id}`, {method:'POST'}).then(r=>r.json()).then(data=>{
        if(data && data.content_id){
          // redirect to edit page for tagging/categorizing
          window.location.href = `/content/edit/${data.content_id}`;
        } else {
          refreshList();
        }
      });
    }
    if(e.target.matches('.live-upload-input')){ /* file input change */ }
  });

  // delegate file input change
  listEl && listEl.addEventListener('change', function(e){
    if(e.target.matches('.live-upload-input')){
      const id = e.target.getAttribute('data-id');
      const file = e.target.files[0];
      if(!file) return;
      const form = new FormData();
      form.append('recording', file);
      fetch(`/live/upload/${id}`, {method:'POST', body: form})
        .then(r=>r.json())
        .then(data=>{
          if(data && data.status === 'ok'){
            // after upload, offer saving immediately
            if(confirm('Recording uploaded. Save as content now?')){
              fetch(`/live/save/${id}`, {method:'POST'})
                .then(r=>r.json())
                .then(d=>{
                  if(d && d.content_id){ window.location.href = `/content/edit/${d.content_id}` } else { refreshList(); }
                });
            } else {
              refreshList();
            }
          } else {
            alert('Failed to upload recording');
            refreshList();
          }
        }).catch(()=>{ alert('Upload failed'); refreshList(); });
    }
  });

  socket.on('live:recording_uploaded', function(msg){
    refreshList();
  });

  refreshList();
});
