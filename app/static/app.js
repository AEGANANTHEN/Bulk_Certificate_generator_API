let currentPollingInterval = null;
let currentJobId = null;

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tabId = btn.getAttribute('data-tab');
    document.getElementById(tabId).classList.add('active');
  });
});

// Load Sample Batch
function loadSampleBatch() {
  document.getElementById('event_name').value = 'Autonomous Drone Systems & Computer Vision';
  document.getElementById('title').value = 'Certificate of Excellence';
  document.getElementById('issuer_name').value = 'AEREO Engineering Academy';
  
  const sampleRecipients = [
    { name: "Aarav Sharma", email: "aarav.sharma@example.com" },
    { name: "Priya Patel", email: "priya.patel@example.com" },
    { name: "Rohan Kulkarni", email: "rohan.kulkarni@example.com" },
    { name: "Ananya Iyer", email: "ananya.iyer@example.com" },
    { name: "__FAIL__ (Simulated Failure)", email: "bad.email@@err" },
    { name: "Vikram Malhotra", email: "vikram.m@example.com" }
  ];

  document.getElementById('recipients_input').value = JSON.stringify(sampleRecipients, null, 2);
}

// Parse recipients from textarea (JSON or CSV)
function parseRecipients(input) {
  const trimmed = input.trim();
  if (!trimmed) return [];

  // Try parsing as JSON first
  if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
    try {
      const parsed = JSON.parse(trimmed);
      return Array.isArray(parsed) ? parsed : [parsed];
    } catch (e) {
      console.warn("Could not parse as JSON, trying CSV line format...");
    }
  }

  // Fallback: Line-separated CSV format: "Name, email" or just "Name"
  const lines = trimmed.split('\n').map(l => l.trim()).filter(Boolean);
  return lines.map(line => {
    const parts = line.split(',');
    return {
      name: parts[0]?.trim() || "",
      email: parts[1]?.trim() || null
    };
  });
}

// Submit Bulk Generation Job
async function submitJob(event) {
  event.preventDefault();
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Queueing Job...`;

  const title = document.getElementById('title').value.trim();
  const event_name = document.getElementById('event_name').value.trim();
  const issuer_name = document.getElementById('issuer_name').value.trim();
  const issue_date = document.getElementById('issue_date').value.trim() || null;
  const rawRecipients = document.getElementById('recipients_input').value;

  const recipients = parseRecipients(rawRecipients);

  if (!recipients.length) {
    alert("Please provide at least one recipient.");
    btn.disabled = false;
    btn.innerText = "🚀 Generate Certificates";
    return;
  }

  const payload = {
    title: title || "Certificate of Achievement",
    event_name: event_name,
    issuer_name: issuer_name || "AEREO Academy",
    issue_date: issue_date,
    recipients: recipients
  };

  try {
    const response = await fetch('/api/v1/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail ? JSON.stringify(err.detail) : 'Failed to submit job');
    }

    const job = await response.json();
    currentJobId = job.job_id;
    
    // Switch or show progress card
    document.getElementById('statusCard').style.display = 'block';
    startPolling(currentJobId);
  } catch (err) {
    alert("Error submitting job: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerText = "🚀 Generate Certificates";
  }
}

// Polling Job Progress
function startPolling(jobId) {
  if (currentPollingInterval) clearInterval(currentPollingInterval);

  pollStatus(jobId);
  currentPollingInterval = setInterval(() => pollStatus(jobId), 1000);
}

async function pollStatus(jobId) {
  try {
    const response = await fetch(`/api/v1/jobs/${jobId}`);
    if (!response.ok) return;

    const data = await response.json();
    updateUIWithJob(data);

    if (['COMPLETED', 'PARTIALLY_COMPLETED', 'FAILED'].includes(data.status)) {
      clearInterval(currentPollingInterval);
      currentPollingInterval = null;
    }
  } catch (e) {
    console.error("Polling error:", e);
  }
}

function updateUIWithJob(data) {
  // Update badge and message
  const badge = document.getElementById('jobStatusBadge');
  badge.className = `badge badge-${data.status.toLowerCase()}`;
  badge.innerText = data.status;

  document.getElementById('jobMessage').innerText = data.message;
  document.getElementById('statTotal').innerText = data.total_count;
  document.getElementById('statProcessed').innerText = data.processed_count;
  document.getElementById('statSuccess').innerText = data.success_count;
  document.getElementById('statFailure').innerText = data.failure_count;

  // Progress Bar
  const pct = data.progress_percentage || 0;
  document.getElementById('progressFill').style.width = `${pct}%`;
  document.getElementById('progressText').innerText = `${pct}%`;

  // Bulk ZIP Download Button
  const zipBtnContainer = document.getElementById('zipBtnContainer');
  if (data.zip_download_url && data.success_count > 0) {
    zipBtnContainer.innerHTML = `
      <a href="${data.zip_download_url}?format=pdf" class="btn-primary" style="display:inline-flex; width:auto; text-decoration:none; padding:0.6rem 1.25rem;">
        📦 Download All as ZIP (PDF)
      </a>
      <a href="${data.zip_download_url}?format=png" class="btn-secondary" style="display:inline-flex; width:auto; text-decoration:none; padding:0.6rem 1.25rem;">
        🖼️ Download All as ZIP (PNG)
      </a>
    `;
  } else {
    zipBtnContainer.innerHTML = '';
  }

  // Populate Table
  const tbody = document.getElementById('certificatesTableBody');
  tbody.innerHTML = '';

  data.certificates.forEach(c => {
    const tr = document.createElement('tr');
    const statusClass = c.status === 'SUCCESS' ? 'badge-completed' : (c.status === 'FAILED' ? 'badge-failed' : 'badge-pending');
    
    let actionsHtml = '-';
    if (c.status === 'SUCCESS') {
      actionsHtml = `
        <div class="table-actions">
          <a href="#" onclick="previewCert('${c.download_png_url}'); return false;" class="action-link">👁️ Preview</a>
          <a href="${c.download_pdf_url}" class="action-link" download>📄 PDF</a>
          <a href="${c.download_png_url}" class="action-link" download>🖼️ PNG</a>
        </div>
      `;
    } else if (c.status === 'FAILED') {
      actionsHtml = `<span style="color:var(--danger); font-size:0.75rem;" title="${c.error_message || ''}">⚠️ ${c.error_message || 'Failed'}</span>`;
    }

    tr.innerHTML = `
      <td><strong>${escapeHtml(c.recipient_name)}</strong><br><span style="color:var(--text-muted); font-size:0.75rem;">${c.recipient_email || 'No email'}</span></td>
      <td><code>${c.certificate_code}</code></td>
      <td><span class="badge ${statusClass}">${c.status}</span></td>
      <td>${actionsHtml}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Preview Modal
function previewCert(pngUrl) {
  const modal = document.getElementById('previewModal');
  const img = document.getElementById('previewImg');
  img.src = pngUrl;
  modal.classList.add('open');
}

function closePreview() {
  document.getElementById('previewModal').classList.remove('open');
}

// Certificate Verification
async function verifyCertificate(e) {
  e.preventDefault();
  const code = document.getElementById('verifyCodeInput').value.trim();
  const resultDiv = document.getElementById('verificationResult');
  
  if (!code) return;
  resultDiv.style.display = 'block';
  resultDiv.innerHTML = '<p>Verifying with registry...</p>';

  try {
    const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
    const data = await res.json();

    if (data.is_valid) {
      resultDiv.innerHTML = `
        <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid var(--success); border-radius: var(--radius-md); padding: 1.5rem; text-align: left;">
          <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
            <span style="font-size:1.5rem;">✅</span>
            <strong style="color:var(--success); font-size:1.15rem;">OFFICIAL AUTHENTIC CERTIFICATE</strong>
          </div>
          <p><strong>Recipient:</strong> ${escapeHtml(data.recipient_name)}</p>
          <p><strong>Event:</strong> ${escapeHtml(data.event_name)}</p>
          <p><strong>Issuing Authority:</strong> ${escapeHtml(data.issuer_name)}</p>
          <p><strong>Issue Date:</strong> ${data.issue_date}</p>
          <p><strong>Certificate ID:</strong> <code>${data.certificate_code}</code></p>
          <div style="margin-top:1rem;">
            <a href="${data.download_url}" target="_blank" class="nav-btn" style="border-color:var(--success); color:var(--success);">📥 Download Original PDF</a>
          </div>
        </div>
      `;
    } else {
      resultDiv.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid var(--danger); border-radius: var(--radius-md); padding: 1.5rem; text-align: left;">
          <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.75rem;">
            <span style="font-size:1.5rem;">❌</span>
            <strong style="color:var(--danger); font-size:1.15rem;">INVALID CERTIFICATE</strong>
          </div>
          <p>${escapeHtml(data.message)}</p>
        </div>
      `;
    }
  } catch (err) {
    resultDiv.innerHTML = `<p style="color:var(--danger);">Verification request failed: ${err.message}</p>`;
  }
}

function escapeHtml(text) {
  if (!text) return "";
  return text.replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[m]);
}
