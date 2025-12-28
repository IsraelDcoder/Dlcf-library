(function(){
  const socket = io();
  const room = `community_${COMMUNITY_ID}`;
  const chatWindow = document.getElementById('chatWindow');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');

  function appendMessage(data){
    const node = document.createElement('div');
    node.className = 'chat-msg';
    const time = new Date(data.created_at || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    node.innerHTML = `<strong>${escapeHtml(data.author)}</strong> <span class="time muted">${time}</span><div class="text">${escapeHtml(data.message)}</div>`;
    chatWindow.appendChild(node);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function escapeHtml(s){ return String(s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c]; }); }

  socket.on('connect', ()=>{
    socket.emit('join', {community_id: COMMUNITY_ID});
  });

  socket.on('message', (data)=>{
    appendMessage(data);
  });
  socket.on('post_created', (data)=>{
    // simple notify
    console.log('New post', data);
  });

  socket.on('user_muted', (data)=>{
    // update member badge
    const el = document.querySelector(`[data-user-id="${data.target}"]`);
    if(el){
      let badge = el.querySelector('.muted-badge');
      if(!badge){
        badge = document.createElement('span');
        badge.className = 'badge muted-badge';
        el.appendChild(badge);
      }
      badge.textContent = 'Muted until ' + (new Date(data.until)).toLocaleString();
    }
  });

  socket.on('user_unmuted', (data)=>{
    const el = document.querySelector(`[data-user-id="${data.target}"]`);
    if(el){
      const badge = el.querySelector('.muted-badge');
      if(badge) badge.remove();
    }
  });

  socket.on('muted', (data)=>{
    alert('You have been muted until ' + data.until);
  });

  chatForm.addEventListener('submit', (e)=>{
    e.preventDefault();
    const val = chatInput.value.trim();
    if(!val) return;
    socket.emit('message', {community_id: COMMUNITY_ID, message: val});
    chatInput.value = '';
  });

})();