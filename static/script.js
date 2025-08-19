document.getElementById('uploadForm')?.addEventListener('submit', async function(e){
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);
  const res = await fetch('/upload', {method:'POST', body: data});
  const json = await res.json();
  const out = document.getElementById('uploadResult');
  if(json.need_manual_amount){
    out.innerHTML = `<p>OCR couldn't find amount. Please enter amount manually <form id="manualAdd"><input name="amount" placeholder="Amount" required><input name="category" placeholder="Category"><button type="submit">Add</button></form></p>`;
    document.getElementById('manualAdd').addEventListener('submit', async function(ev){
      ev.preventDefault();
      const fdata = new FormData();
      fdata.append('amount', ev.target.amount.value);
      fdata.append('category', ev.target.category.value || 'Misc');
      const r = await fetch('/manual-entry', {method:'POST', body: fdata});
      if(r.redirected) window.location = r.url;
    });
  } else {
    out.innerHTML = '<p>Uploaded and processed. <a href="/result">View Result</a></p>';
  }
});