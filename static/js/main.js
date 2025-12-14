// ===== Configuration =====
const UPDATE_INTERVAL = 1000;
const MAX_WEIGHT = 100;

// ===== DOM Elements =====
const elements = {
    berat: document.getElementById('berat'),
    mode: document.getElementById('mode'),
    lastFeed: document.getElementById('last-feed'),
    espBadge: document.getElementById('esp-badge'),
    espStatusText: document.getElementById('esp-status-text'),
    progressBerat: document.getElementById('progress-berat'),
    btnManual: document.getElementById('btn-manual'),
    autoSelect: document.getElementById('auto-select'),
    manualSection: document.getElementById('manual-section'),
    toast: document.getElementById('toast'),
    toastIcon: document.getElementById('toast-icon'),
    toastMessage: document.getElementById('toast-message')
};

// ===== Helper: Format interval to readable string =====
function formatInterval(seconds) {
    if (seconds < 60) return seconds + ' detik';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' menit';
    return Math.floor(seconds / 3600) + ' jam';
}

// ===== Set Manual Mode =====
async function setManualMode() {
    try {
        const response = await fetch('/set_mode/MANUAL', { method: 'POST' });
        const data = await response.json();

        if (data.status === 'ok') {
            elements.btnManual.classList.add('active');
            elements.autoSelect.classList.remove('active');
            elements.autoSelect.value = '';  // Reset dropdown
            elements.manualSection.style.display = 'block';
            showToast('Mode MANUAL aktif', 'success');
        }
    } catch (error) {
        showToast('Gagal mengubah mode', 'error');
    }
}

// ===== Handle Auto Select =====
async function handleAutoSelect(interval) {
    if (!interval) return;

    try {
        // Set mode to AUTO and interval
        await fetch('/set_mode/AUTO', { method: 'POST' });
        const response = await fetch('/set_interval/' + interval, { method: 'POST' });
        const data = await response.json();

        if (data.status === 'ok') {
            elements.btnManual.classList.remove('active');
            elements.autoSelect.classList.add('active');
            elements.manualSection.style.display = 'none';
            showToast('Mode AUTO aktif! Interval: ' + formatInterval(parseInt(interval)), 'success');
        }
    } catch (error) {
        showToast('Gagal mengatur mode otomatis', 'error');
    }
}

// ===== Update Data from Server =====
async function updateData() {
    try {
        const response = await fetch('/status');
        const data = await response.json();

        // Update berat
        elements.berat.textContent = data.berat + ' g';

        // Update progress bar
        const percentage = Math.min((data.berat / MAX_WEIGHT) * 100, 100);
        elements.progressBerat.style.width = percentage + '%';

        if (data.berat < 20) {
            elements.progressBerat.classList.add('low');
        } else {
            elements.progressBerat.classList.remove('low');
        }

        // Update mode display
        if (data.mode === 'AUTO') {
            elements.mode.textContent = 'AUTO (' + formatInterval(data.interval) + ')';
            elements.btnManual.classList.remove('active');
            elements.autoSelect.classList.add('active');
            elements.autoSelect.value = data.interval.toString();
            elements.manualSection.style.display = 'none';
        } else {
            elements.mode.textContent = 'MANUAL';
            elements.btnManual.classList.add('active');
            elements.autoSelect.classList.remove('active');
            elements.autoSelect.value = '';
            elements.manualSection.style.display = 'block';
        }

        // Update last feed
        elements.lastFeed.textContent = data.last_feed;

        // Update ESP status
        if (data.esp_connected) {
            elements.espBadge.classList.add('connected');
            elements.espStatusText.textContent = 'Terhubung';
        } else {
            elements.espBadge.classList.remove('connected');
            elements.espStatusText.textContent = 'Menunggu ESP...';
        }
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// ===== Manual Feed =====
async function manualFeed() {
    try {
        const response = await fetch('/manual_feed', { method: 'POST' });
        const data = await response.json();

        if (data.message.includes('Dikirim') || data.message.includes('berhasil')) {
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        showToast('Gagal mengirim perintah', 'error');
    }
}

// ===== Toast Notification =====
function showToast(message, type = 'success') {
    elements.toast.className = 'toast show ' + type;
    elements.toastIcon.textContent = type === 'success' ? '✅' : '❌';
    elements.toastMessage.textContent = message;

    setTimeout(() => {
        elements.toast.classList.remove('show');
    }, 3000);
}

// ===== ML Prediction =====
async function predictFeed() {
    const jumlahAyam = document.getElementById('jumlah-ayam').value;
    const umurMinggu = document.getElementById('umur-minggu').value;
    const pakanSekarang = document.getElementById('pakan-sekarang').value;

    if (!jumlahAyam || !umurMinggu) {
        showToast('Harap isi semua field', 'error');
        return;
    }

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                jumlah_ayam: parseInt(jumlahAyam),
                umur_minggu: parseInt(umurMinggu),
                pakan_saat_ini: parseFloat(pakanSekarang) || 0
            })
        });

        const data = await response.json();

        if (data.status === 'ok') {
            document.getElementById('prediction-result').style.display = 'block';
            document.getElementById('prediction-value').textContent = data.prediksi_kg + ' kg';
            showToast('Prediksi berhasil!', 'success');
        } else {
            showToast(data.message || 'Gagal memprediksi', 'error');
        }
    } catch (error) {
        showToast('Gagal menghubungi server', 'error');
    }
}

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    updateData();
    window.setInterval(updateData, UPDATE_INTERVAL);
});
