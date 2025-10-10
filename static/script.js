document.getElementById('uploadForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);
  const btn = document.getElementById('uploadBtnText');
  const originalText = btn.textContent;
  
  // Show loading state
  btn.innerHTML = '<span class="loading"></span> Uploading...';
  form.querySelector('button').disabled = true;
  
  try {
    const res = await fetch('/upload', {method: 'POST', body: data});
    const json = await res.json();
    const out = document.getElementById('uploadResult');
    
    if (json.need_manual_amount) {
      out.className = 'warning';
      out.innerHTML = `
        <p><strong>⚠️ Amount not detected</strong></p>
        <p>OCR detected text but couldn't find a clear amount.</p>
        ${json.debug_text ? `<p style="font-size: 0.875rem; color: var(--text-secondary);">Detected text: "${json.debug_text}"</p>` : ''}
        <p>Please enter the amount manually:</p>
        <form id="manualAdd" style="margin-top: 1rem;">
          <input type="number" step="0.01" name="amount" placeholder="Amount (₹)" required>
          <input type="text" name="category" placeholder="Category" value="Misc">
          <button type="submit">Save Entry</button>
        </form>
      `;
      
      document.getElementById('manualAdd').addEventListener('submit', async function(ev) {
        ev.preventDefault();
        const fdata = new FormData();
        fdata.append('amount', ev.target.amount.value);
        fdata.append('category', ev.target.category.value || 'Misc');
        
        const r = await fetch('/manual-entry', {method: 'POST', body: fdata});
        if (r.redirected) {
          window.location = r.url;
        } else {
          window.location = '/result';
        }
      });
    } else {
      out.className = 'success';
      out.innerHTML = `
        <p><strong>✅ Upload Successful!</strong></p>
        <p>Receipt processed and analyzed. Amount detected: ₹${json.extracted_amount || 'N/A'}</p>
        <a href="/result"><button style="margin-top: 0.5rem;">View Detailed Results →</button></a>
      `;
      
      // Reset form after 2 seconds
      setTimeout(() => {
        form.reset();
      }, 2000);
    }
  } catch (error) {
    const out = document.getElementById('uploadResult');
    out.className = 'error';
    out.innerHTML = `
      <p><strong>❌ Upload Failed</strong></p>
      <p>Error: ${error.message}</p>
    `;
  } finally {
    // Restore button
    btn.textContent = originalText;
    form.querySelector('button').disabled = false;
  }
});

// Add smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// Add file preview
document.getElementById('receiptInput')?.addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (file && file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = function(event) {
      const out = document.getElementById('uploadResult');
      out.innerHTML = `
        <div style="margin-top: 1rem;">
          <strong>Preview:</strong><br>
          <img src="${event.target.result}" alt="Receipt preview" 
               style="max-width: 100%; max-height: 300px; border-radius: 8px; margin-top: 0.5rem; border: 2px solid var(--border-color);">
        </div>
      `;
    };
    reader.readAsDataURL(file);
  }
});