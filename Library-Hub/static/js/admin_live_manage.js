document.addEventListener('DOMContentLoaded', function(){
  const list = document.getElementById('live-management-list');
  const startBtn = document.getElementById('btn-start-live-global');
  const titleInput = document.getElementById('live-title-input');

  function refresh(){
    fetch('/live/now').then(r=>r.json()).then(data=>{
      // reload the page to get server-rendered content (simple approach)
      window.location.reload();
    }).catch(()=> console.warn('refresh failed'));
  }

  startBtn && startBtn.addEventListener('click', function(){
    const title = titleInput.value || '';
    const q = title ? ('?title=' + encodeURIComponent(title)) : '';
    window.location.href = '/admin/live/new' + q;
  });

  list && list.addEventListener('click', function(e){
    if(e.target.matches('.btn-end-session')){
      const id = e.target.getAttribute('data-id');
      fetch(`/live/end/${id}`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({auto_publish:false})}).then(()=> refresh());
    }
    if(e.target.matches('.btn-save-session')){
      const id = e.target.getAttribute('data-id');
      fetch(`/live/save/${id}`, {method:'POST'}).then(r=>r.json()).then(d=>{
        if(d && d.content_id){
          window.location.href = `/content/edit/${d.content_id}`;
        } else {
          refresh();
        }
      });
    }
  });

  // upload via delegated file inputs
  list && list.addEventListener('change', function(e){
    if(e.target.matches('.live-upload-input')){
      const id = e.target.getAttribute('data-id');
      const file = e.target.files[0];
      if(!file) return;
      const fd = new FormData();
      fd.append('recording', file);
      fetch(`/live/upload/${id}`, {method:'POST', body: fd}).then(r=>r.json()).then(d=>{
        if(d && d.status === 'ok'){
          if(confirm('Upload complete. Save recording as library content now?')){
            fetch(`/live/save/${id}`, {method:'POST'}).then(r=>r.json()).then(res=>{
              if(res && res.content_id){
                window.location.href = `/content/edit/${res.content_id}`;
              } else { refresh(); }
            });
          } else { refresh(); }
        } else { alert('Upload failed'); }
      }).catch(()=> alert('Upload failed'));
    }
  });

});
