/* ==========================================================================
   AEREO Enterprise Certificate Engine - Client Logic
   ========================================================================== */

let currentPollingInterval = null;
let currentJobId = null;
let currentCertificatesList = [];
let currentFilter = 'all';

// --------------------------------------------------------------------------
// Tab Navigation
// --------------------------------------------------------------------------
document.querySelectorAll('.view-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.view-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tabId = btn.getAttribute('data-tab');
    const pane = document.getElementById(tabId);
    if (pane) pane.classList.add('active');
  });
});

// --------------------------------------------------------------------------
// Toast Notification Engine
// --------------------------------------------------------------------------
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = {
    success: '✅',
    error: '❌',
    info: 'ℹ️'
  };

  const toast = document.createElement('div');
  toast.className = `toast-item ${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// --------------------------------------------------------------------------
// Recipient Roster Helpers & Parsing
// --------------------------------------------------------------------------
function updateRosterCount() {
  const textarea = document.getElementById('recipients_input');
  const countPill = document.getElementById('rosterCountPill');
  if (!textarea || !countPill) return;

  const recipients = parseRecipients(textarea.value);
  const count = recipients.length;

  if (count === 0) {
    countPill.textContent = '0 Recipients';
    countPill.className = 'roster-counter';
  } else {
    countPill.textContent = `${count} Recipient${count === 1 ? '' : 's'} Detected`;
    countPill.className = 'roster-counter has-items';
  }
}

function parseRecipients(input) {
  const trimmed = (input || '').trim();
  if (!trimmed) return [];

  // Try parsing as JSON array
  if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
    try {
      const parsed = JSON.parse(trimmed);
      const arr = Array.isArray(parsed) ? parsed : [parsed];
      return arr.map(item => ({
        name: (item.name || item.recipient_name || '').trim(),
        email: (item.email || item.recipient_email || null)
      })).filter(r => r.name.length > 0 || r.email);
    } catch (e) {
      // Continue to CSV parsing fallback
    }
  }

  // Fallback: CSV or Line-separated format
  const lines = trimmed.split('\n').map(l => l.trim()).filter(Boolean);
  return lines.map(line => {
    const parts = line.split(',');
    return {
      name: (parts[0] || '').trim(),
      email: parts[1] ? parts[1].trim() : null
    };
  });
}

function loadSampleBatch() {
  const sampleRecipients = [
    { name: "Aarav Sharma", email: "aarav.sharma@aereo.in" },
    { name: "Priya Patel", email: "priya.patel@aereo.in" },
    { name: "Rohan Kulkarni", email: "rohan.kulkarni@example.com" },
    { name: "Ananya Iyer", email: "ananya.iyer@example.com" },
    { name: "__FAIL__ (Fault Isolation Test)", email: "bad.email@@err" },
    { name: "Vikram Malhotra", email: "vikram.m@example.com" }
  ];

  document.getElementById('event_name').value = 'Autonomous Drone Systems & Computer Vision';
  document.getElementById('title').value = 'Certificate of Achievement';
  document.getElementById('issuer_name').value = 'AEREO Academy';
  
  const textarea = document.getElementById('recipients_input');
  textarea.value = sampleRecipients.map(r => `${r.name}, ${r.email}`).join('\n');
  updateRosterCount();
  showToast('Sample batch loaded with error-isolation test row', 'info');
}

function clearRoster() {
  const textarea = document.getElementById('recipients_input');
  textarea.value = '';
  updateRosterCount();
  showToast('Roster cleared', 'info');
}

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    const content = e.target.result;
    document.getElementById('recipients_input').value = content;
    updateRosterCount();
    showToast(`Loaded CSV file (${file.name})`, 'success');
  };
  reader.readAsText(file);
}

// Drag & drop support on textarea
const rosterTextarea = document.getElementById('recipients_input');
if (rosterTextarea) {
  ['dragenter', 'dragover'].forEach(eventName => {
    rosterTextarea.addEventListener(eventName, (e) => {
      e.preventDefault();
      rosterTextarea.classList.add('roster-drag-active');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    rosterTextarea.addEventListener(eventName, (e) => {
      e.preventDefault();
      rosterTextarea.classList.remove('roster-drag-active');
    }, false);
  });

  rosterTextarea.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
      const reader = new FileReader();
      reader.onload = (re) => {
        rosterTextarea.value = re.target.result;
        updateRosterCount();
        showToast(`Imported ${files[0].name}`, 'success');
      };
      reader.readAsText(files[0]);
    }
  });

  // Keyboard shortcut Ctrl + Enter to submit
  rosterTextarea.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('jobForm').requestSubmit();
    }
  });
}

// --------------------------------------------------------------------------
// Job Submission & Telemetry Polling
// --------------------------------------------------------------------------
async function submitJob(event) {
  if (event) event.preventDefault();

  const submitBtn = document.getElementById('submitBtn');
  const submitText = document.getElementById('submitText');
  const submitIcon = document.getElementById('submitIcon');

  submitBtn.disabled = true;
  submitIcon.innerHTML = `<span class="spinner-ring"></span>`;
  submitText.textContent = 'Enqueuing Batch...';

  const title = document.getElementById('title').value.trim();
  const event_name = document.getElementById('event_name').value.trim();
  const issuer_name = document.getElementById('issuer_name').value.trim();
  const issue_date = document.getElementById('issue_date').value.trim() || null;
  const rawRecipients = document.getElementById('recipients_input').value;

  const recipients = parseRecipients(rawRecipients);

  if (!recipients.length) {
    showToast('Please add at least one recipient', 'error');
    submitBtn.disabled = false;
    submitIcon.textContent = '⚡';
    submitText.textContent = 'Generate Certificates (Batch Process)';
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

    // Toggle view states
    document.getElementById('idleStateCard').style.display = 'none';
    document.getElementById('statusCard').style.display = 'block';

    showToast(`Job queued (${job.total_count} recipients). Processing...`, 'success');
    startPolling(currentJobId);
  } catch (err) {
    showToast(`Job dispatch failed: ${err.message}`, 'error');
  } finally {
    submitBtn.disabled = false;
    submitIcon.textContent = '⚡';
    submitText.textContent = 'Generate Certificates (Batch Process)';
  }
}

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
      if (data.status === 'COMPLETED') {
        showToast('All certificates generated successfully!', 'success');
      } else if (data.status === 'PARTIALLY_COMPLETED') {
        showToast(`Job completed: ${data.success_count} succeeded, ${data.failure_count} isolated failures.`, 'info');
      }
    }
  } catch (e) {
    console.error("Telemetry error:", e);
  }
}

function updateUIWithJob(data) {
  // Update Stage Badge
  const badge = document.getElementById('jobStatusBadge');
  badge.className = `job-stage-badge badge-${data.status.toLowerCase()}`;
  badge.innerText = data.status.replace('_', ' ');

  // Status message & Progress
  document.getElementById('jobMessage').innerText = data.message;
  const pct = data.progress_percentage || 0;
  document.getElementById('progressFill').style.width = `${pct}%`;
  document.getElementById('progressText').innerText = `${pct}%`;

  // Metric Counters
  document.getElementById('statTotal').innerText = data.total_count;
  document.getElementById('statProcessed').innerText = data.processed_count;
  document.getElementById('statSuccess').innerText = data.success_count;
  document.getElementById('statFailure').innerText = data.failure_count;

  // Bulk ZIP Download Ribbon
  const ribbon = document.getElementById('zipRibbonContainer');
  if (data.zip_download_url && data.success_count > 0) {
    ribbon.innerHTML = `
      <a href="${data.zip_download_url}?format=pdf" class="btn-primary-action">
        <span>📦</span> Download All as ZIP (PDF)
      </a>
      <a href="${data.zip_download_url}?format=png" class="btn-secondary-action">
        <span>🖼️</span> Download All as ZIP (PNG)
      </a>
    `;
  } else {
    ribbon.innerHTML = '';
  }

  // Update Global List & Table
  currentCertificatesList = data.certificates || [];
  updateFilterPillCounts();
  renderCertificateTable();
}

// --------------------------------------------------------------------------
// Table Rendering, Search & Filtering
// --------------------------------------------------------------------------
function updateFilterPillCounts() {
  const allCount = currentCertificatesList.length;
  const successCount = currentCertificatesList.filter(c => c.status === 'SUCCESS').length;
  const failedCount = currentCertificatesList.filter(c => c.status === 'FAILED').length;

  document.getElementById('pillCountAll').innerText = allCount;
  document.getElementById('pillCountSuccess').innerText = successCount;
  document.getElementById('pillCountFailed').innerText = failedCount;
}

function setFilter(filterType) {
  currentFilter = filterType;
  document.querySelectorAll('.filter-pill').forEach(btn => btn.classList.remove('active'));
  const activeBtn = Array.from(document.querySelectorAll('.filter-pill')).find(b => b.textContent.toLowerCase().includes(filterType));
  if (activeBtn) activeBtn.classList.add('active');
  renderCertificateTable();
}

function filterCertTable() {
  renderCertificateTable();
}

function renderCertificateTable() {
  const tbody = document.getElementById('certificatesTableBody');
  if (!tbody) return;

  const searchQuery = (document.getElementById('tableSearchInput')?.value || '').toLowerCase().trim();

  let filtered = currentCertificatesList.filter(c => {
    if (currentFilter === 'success' && c.status !== 'SUCCESS') return false;
    if (currentFilter === 'failed' && c.status !== 'FAILED') return false;

    if (searchQuery) {
      const matchName = (c.recipient_name || '').toLowerCase().includes(searchQuery);
      const matchEmail = (c.recipient_email || '').toLowerCase().includes(searchQuery);
      const matchCode = (c.certificate_code || '').toLowerCase().includes(searchQuery);
      if (!matchName && !matchEmail && !matchCode) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" style="text-align:center; padding:2rem; color:var(--text-muted);">
          No matching certificate records found.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = '';
  filtered.forEach(c => {
    const tr = document.createElement('tr');
    
    // Avatar initials
    const initials = (c.recipient_name || 'U').split(' ').map(p => p[0]).slice(0, 2).join('').toUpperCase();
    
    // Status Badge
    const statusClass = c.status === 'SUCCESS' ? 'badge-completed' : (c.status === 'FAILED' ? 'badge-failed' : 'badge-pending');

    // Actions Column
    let actionsHtml = '-';
    if (c.status === 'SUCCESS') {
      actionsHtml = `
        <div class="row-actions-group">
          <button type="button" class="row-action-btn gold" onclick="openPreview('${c.download_png_url}', '${c.download_pdf_url}')">
            👁️ Preview
          </button>
          <a href="${c.download_pdf_url}" class="row-action-btn" download>
            📄 PDF
          </a>
          <a href="${c.download_png_url}" class="row-action-btn" download>
            🖼️ PNG
          </a>
          <button type="button" class="row-action-btn" onclick="prefillVerification('${c.certificate_code}')">
            🔍
          </button>
        </div>
      `;
    } else if (c.status === 'FAILED') {
      actionsHtml = `
        <span style="color:var(--color-danger); font-size:0.75rem;" title="${escapeHtml(c.error_message || '')}">
          ⚠️ ${escapeHtml(c.error_message || 'Validation error')}
        </span>
      `;
    }

    tr.innerHTML = `
      <td>
        <div class="recipient-cell">
          <div class="recipient-avatar">${initials}</div>
          <div class="recipient-info">
            <span class="recipient-name">${escapeHtml(c.recipient_name || 'Anonymous')}</span>
            <span class="recipient-email">${escapeHtml(c.recipient_email || 'No email specified')}</span>
          </div>
        </div>
      </td>
      <td>
        <span class="code-copy-pill" onclick="copyCode('${c.certificate_code}')" title="Click to copy ID">
          <span>${c.certificate_code}</span>
          <span style="font-size:0.7rem; color:var(--text-muted);">📋</span>
        </span>
      </td>
      <td>
        <span class="job-stage-badge ${statusClass}">${c.status}</span>
      </td>
      <td>${actionsHtml}</td>
    `;
    tbody.appendChild(tr);
  });
}

function copyCode(code) {
  navigator.clipboard.writeText(code).then(() => {
    showToast(`Copied certificate ID: ${code}`, 'success');
  }).catch(() => {
    showToast(`Certificate ID: ${code}`, 'info');
  });
}

// --------------------------------------------------------------------------
// Modal Preview Engine
// --------------------------------------------------------------------------
function openPreview(pngUrl, pdfUrl) {
  const modal = document.getElementById('previewModal');
  const img = document.getElementById('previewImg');
  const pdfBtn = document.getElementById('modalDownloadPdf');
  const pngBtn = document.getElementById('modalDownloadPng');

  img.src = pngUrl;
  if (pdfBtn) pdfBtn.href = pdfUrl || '#';
  if (pngBtn) pngBtn.href = pngUrl || '#';

  modal.classList.add('open');
}

function closePreview() {
  const modal = document.getElementById('previewModal');
  modal.classList.remove('open');
}

// --------------------------------------------------------------------------
// Credential Verification Portal
// --------------------------------------------------------------------------
function prefillVerification(code) {
  // Switch to verification tab
  document.querySelector('.view-tab-btn[data-tab="tab-verify"]').click();
  const input = document.getElementById('verifyCodeInput');
  input.value = code;
  verifyCertificate();
}

async function verifyCertificate(e) {
  if (e) e.preventDefault();
  const code = document.getElementById('verifyCodeInput').value.trim();
  const resultDiv = document.getElementById('verificationResult');

  if (!code) {
    showToast('Please enter a certificate ID', 'error');
    return;
  }

  resultDiv.style.display = 'block';
  resultDiv.innerHTML = '<div style="padding:1.5rem; color:var(--text-secondary);"><span class="spinner-ring"></span> Authenticating against cryptographic registry...</div>';

  try {
    const res = await fetch(`/api/v1/certificates/verify/${encodeURIComponent(code)}`);
    const data = await res.json();

    if (data.is_valid) {
      resultDiv.innerHTML = `
        <div class="credential-verified-card">
          <div class="credential-verified-header">
            <div class="verified-stamp-icon">✓</div>
            <div>
              <h3 style="color:#34d399; font-size:1.15rem; font-weight:800;">OFFICIAL AUTHENTIC CREDENTIAL</h3>
              <p style="font-size:0.8rem; color:var(--text-secondary);">Issued by AEREO Credential Registry</p>
            </div>
          </div>

          <div class="credential-details-grid">
            <div class="credential-field">
              <label>Recipient Name</label>
              <div class="val">${escapeHtml(data.recipient_name)}</div>
            </div>
            <div class="credential-field">
              <label>Certificate Serial</label>
              <div class="val" style="font-family:var(--font-mono); color:var(--accent-gold-light);">${escapeHtml(data.certificate_code)}</div>
            </div>
            <div class="credential-field">
              <label>Event / Program</label>
              <div class="val">${escapeHtml(data.event_name)}</div>
            </div>
            <div class="credential-field">
              <label>Issuing Authority</label>
              <div class="val">${escapeHtml(data.issuer_name)}</div>
            </div>
            <div class="credential-field">
              <label>Issuance Date</label>
              <div class="val">${escapeHtml(data.issue_date || 'N/A')}</div>
            </div>
            <div class="credential-field">
              <label>Registry Status</label>
              <div class="val" style="color:#34d399;">Active & Valid</div>
            </div>
          </div>

          <div style="display:flex; gap:0.75rem; margin-top:1.5rem;">
            <a href="${data.download_url}" target="_blank" class="btn-primary-action">
              <span>📥</span> Download Original PDF
            </a>
          </div>
        </div>
      `;
    } else {
      resultDiv.innerHTML = `
        <div style="background:rgba(239, 68, 68, 0.12); border:1px solid rgba(239, 68, 68, 0.4); border-radius:var(--radius-lg); padding:2rem; text-align:left;">
          <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem;">
            <span style="font-size:1.5rem;">❌</span>
            <strong style="color:var(--color-danger); font-size:1.1rem;">CREDENTIAL NOT FOUND OR INVALID</strong>
          </div>
          <p style="color:var(--text-secondary); font-size:0.9rem;">
            ${escapeHtml(data.message || 'No record matches this certificate code in the AEREO registry.')}
          </p>
        </div>
      `;
    }
  } catch (err) {
    resultDiv.innerHTML = `<p style="color:var(--color-danger);">Verification failed: ${err.message}</p>`;
  }
}

// --------------------------------------------------------------------------
// Utility
// --------------------------------------------------------------------------
function escapeHtml(text) {
  if (!text) return "";
  return text.replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[m]);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  updateRosterCount();
});
