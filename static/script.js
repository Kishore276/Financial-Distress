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
    const res = await fetch('/upload', {
      method: 'POST', 
      body: data
    });
    
    if (!res.ok) {
      throw new Error(`Server error: ${res.status} ${res.statusText}`);
    }
    
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
      
      // Build alternatives HTML if available
      let alternativesHtml = '';
      if (json.alternative_amounts && json.alternative_amounts.length > 0) {
        alternativesHtml = `
          <div style="margin-top: 1rem; padding: 1rem; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
            <p><strong>⚠️ Amount incorrect?</strong></p>
            <p style="font-size: 0.875rem; margin: 0.5rem 0;">Other amounts detected in receipt:</p>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
              ${json.alternative_amounts.map(amt => 
                `<button onclick="correctAmount(${amt})" style="padding: 0.5rem 1rem; background: white; border: 2px solid #ffc107; border-radius: 6px; cursor: pointer; font-weight: 600;">₹${amt}</button>`
              ).join('')}
            </div>
            <p style="font-size: 0.875rem; margin-top: 0.5rem; color: var(--text-secondary);">
              Click a button to use that amount instead, or use manual entry below.
            </p>
          </div>
        `;
      }
      
      out.innerHTML = `
        <p><strong>✅ Upload Successful!</strong></p>
        <p>Receipt processed and analyzed. Amount detected: <strong style="font-size: 1.2rem; color: var(--primary-color);">₹${json.extracted_amount || 'N/A'}</strong></p>
        ${alternativesHtml}
        <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
          <a href="/result"><button style="flex: 1;">View Detailed Results →</button></a>
        </div>
      `;
      
      // Reset form after 2 seconds
      setTimeout(() => {
        form.reset();
      }, 2000);
    }
  } catch (error) {
    console.error('Upload error:', error);
    const out = document.getElementById('uploadResult');
    out.className = 'error';
    out.innerHTML = `
      <p><strong>❌ Upload Failed</strong></p>
      <p>Error: ${error.message}</p>
      <p style="font-size: 0.875rem; color: var(--text-secondary);">
        Make sure the Flask server is running at http://127.0.0.1:5000
      </p>
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

// Function to correct amount with alternative
window.correctAmount = async function(amount) {
  if (!confirm(`Use ₹${amount} as the correct amount?`)) {
    return;
  }
  
  const fdata = new FormData();
  fdata.append('amount', amount);
  fdata.append('category', 'Misc');
  fdata.append('date', new Date().toISOString().split('T')[0]);
  
  try {
    const res = await fetch('/manual-entry', {method: 'POST', body: fdata});
    if (res.ok || res.redirected) {
      window.location = '/result';
    }
  } catch (error) {
    alert('Failed to update amount: ' + error.message);
  }
};

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