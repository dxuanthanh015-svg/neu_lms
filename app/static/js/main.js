// ==========================================
// Interactive LMS M10 Scripts
// ==========================================

function showToast(message, isError = false) {
  const toast = document.getElementById('global-toast');
  if (!toast) return;
  toast.textContent = message;
  toast.style.backgroundColor = isError ? '#dc2626' : '#0f172a';
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 3500);
}

function notificationIcon(type) {
  if (type === 'ASSIGNMENT_OVERDUE') return 'fa-clock';
  if (type === 'ASSIGNMENT_POSTED') return 'fa-file-circle-plus';
  return 'fa-chalkboard-user';
}

function renderNotifications(notifications) {
  const list = document.getElementById('notification-list');
  if (!list) return;
  list.replaceChildren();
  if (!notifications.length) {
    const empty = document.createElement('p');
    empty.className = 'notification-empty';
    empty.textContent = 'Bạn chưa có thông báo nào.';
    list.appendChild(empty);
    return;
  }

  notifications.forEach(notice => {
    const item = document.createElement('a');
    item.className = `notification-item${notice.is_read ? '' : ' unread'}`;
    const target = typeof notice.target_url === 'string' && notice.target_url.startsWith('/') && !notice.target_url.startsWith('//')
      ? notice.target_url : '#';
    item.href = target;
    item.dataset.notificationId = notice.id;

    const icon = document.createElement('span');
    icon.className = 'notification-icon';
    const iconElement = document.createElement('i');
    iconElement.className = `fa-solid ${notificationIcon(notice.notification_type)}`;
    icon.appendChild(iconElement);

    const copy = document.createElement('span');
    copy.className = 'notification-copy';
    const title = document.createElement('span');
    title.className = 'notification-title';
    title.textContent = notice.title;
    const message = document.createElement('span');
    message.className = 'notification-message';
    message.textContent = notice.message;
    const time = document.createElement('time');
    time.className = 'notification-time';
    const createdAt = new Date(notice.created_at);
    time.dateTime = notice.created_at;
    time.textContent = Number.isNaN(createdAt.getTime()) ? '' : createdAt.toLocaleString('vi-VN', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
    copy.append(title, message, time);
    item.append(icon, copy);
    list.appendChild(item);
  });
}

async function refreshNotifications() {
  const badge = document.getElementById('notification-count');
  if (!badge) return;
  try {
    const response = await fetch('/api/notifications', { headers: { Accept: 'application/json' } });
    const data = await response.json();
    if (!response.ok || data.status !== 'success') return;
    const unread = Number(data.unread_count) || 0;
    badge.textContent = unread > 99 ? '99+' : String(unread);
    badge.hidden = unread === 0;
    renderNotifications(data.notifications || []);
  } catch (_) {
    // Keep the rest of the page usable when notifications cannot be fetched.
  }
}

function initializeNotificationBell() {
  const bell = document.getElementById('notification-bell');
  const panel = document.getElementById('notification-panel');
  const list = document.getElementById('notification-list');
  const readAll = document.getElementById('notification-read-all');
  if (!bell || !panel || !list) return;

  bell.addEventListener('click', async () => {
    const opening = panel.hidden;
    panel.hidden = !opening;
    bell.setAttribute('aria-expanded', String(opening));
    if (opening) await refreshNotifications();
  });

  list.addEventListener('click', async event => {
    const item = event.target.closest('.notification-item');
    if (!item || !item.dataset.notificationId) return;
    event.preventDefault();
    const target = item.href;
    try {
      await fetch(`/api/notifications/${encodeURIComponent(item.dataset.notificationId)}/read`, { method: 'POST' });
    } finally {
      if (target && target !== window.location.href) window.location.assign(target);
      else refreshNotifications();
    }
  });

  if (readAll) readAll.addEventListener('click', async () => {
    try {
      await fetch('/api/notifications/read-all', { method: 'POST' });
      await refreshNotifications();
    } catch (_) {}
  });

  document.addEventListener('click', event => {
    if (!panel.hidden && !event.target.closest('.notification-area')) {
      panel.hidden = true;
      bell.setAttribute('aria-expanded', 'false');
    }
  });

  refreshNotifications();
  window.setInterval(refreshNotifications, 60000);
}

function openModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) {
    el.classList.add('active');
    el.style.display = 'flex';
  }
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) {
    el.classList.remove('active');
    el.style.display = 'none';
  }
}

// Cập nhật cấu hình DRM
async function updateDrmSettings(materialId) {
  const chkOnline = document.getElementById('drm-view-online');
  const chkOffline = document.getElementById('drm-allow-offline');
  const versionSelect = document.getElementById('drm-version-select');

  const payload = {
    view_online_only: chkOnline ? chkOnline.checked : true,
    allow_offline_encrypted_study: chkOffline ? chkOffline.checked : false,
    version_tag: versionSelect ? versionSelect.value : 'v2.0'
  };

  try {
    const res = await fetch(`/api/materials/${materialId}/drm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(data.message);
      const syncEl = document.getElementById('drm-sync-time');
      if (syncEl) syncEl.textContent = `Hôm nay lúc ${data.signed_at.split(' ')[0]}`;
    } else {
      showToast(data.message || 'Lỗi lưu DRM', true);
    }
  } catch (err) {
    showToast('Lỗi kết nối máy chủ', true);
  }
}

// Xóa học liệu
async function deleteMaterial(materialId) {
  if (!confirm('Bạn có chắc chắn muốn xóa học liệu này khỏi bài học?')) return;
  try {
    const res = await fetch(`/api/materials/${materialId}/delete`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(data.message);
      setTimeout(() => location.reload(), 600);
    } else {
      showToast('Không thể xóa học liệu', true);
    }
  } catch (err) {
    showToast('Lỗi mạng', true);
  }
}

// Tải lên học liệu mới qua modal
async function submitUploadMaterial(e) {
  e.preventDefault();
  const title = document.getElementById('new-mat-title').value;
  const matType = document.getElementById('new-mat-type').value;
  const isShared = document.getElementById('new-mat-shared').checked;
  const lessonId = document.getElementById('new-mat-lesson-id').value;

  try {
    const res = await fetch('/api/materials/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lesson_id: lessonId,
        title: title,
        material_type: matType,
        is_shared_institutional_repo: isShared
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(data.message);
      closeModal('upload-material-modal');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast('Lỗi tải lên', true);
    }
  } catch (err) {
    showToast('Lỗi hệ thống', true);
  }
}

// Sinh câu hỏi bằng EduLLM AI
async function generateAiQuestion() {
  const btn = document.getElementById('btn-generate-ai');
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'EduLLM đang phân tích tài liệu...';
  }

  try {
    const res = await fetch('/api/ai/generate-question', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: 'Flask & RESTful Architecture',
        bloom_level: 'L3_APPLY'
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(data.message);
      setTimeout(() => location.reload(), 1000);
    }
  } catch (err) {
    showToast('Lỗi khi gọi AI', true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = '✨ AI EduLLM Sinh Đề Thi Mới';
    }
  }
}

// Duyệt câu hỏi
async function approveQuestion(qId) {
  try {
    const res = await fetch(`/api/questions/${qId}/approve`, { method: 'POST' });
    const data = await res.json();
    showToast(data.message);
    setTimeout(() => location.reload(), 600);
  } catch (err) {
    showToast('Lỗi duyệt câu hỏi', true);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initializeNotificationBell();
  const formUpload = document.getElementById('form-upload-material');
  if (formUpload) {
    formUpload.addEventListener('submit', submitUploadMaterial);
  }
});
