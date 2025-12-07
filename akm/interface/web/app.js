//akm/interface/web/app.js
const API_URL = "http://localhost:8000";
let currentAddress = null;

// --- UI HELPER: Barra de Carga ---
function setLoading(isLoading) {
    const bar = document.getElementById('loading-bar');
    if (!bar) return; // Protección si no existe el elemento
    bar.style.width = isLoading ? '70%' : '100%';
    if (!isLoading) setTimeout(() => bar.style.width = '0%', 300);
}

// --- API CORE ---
async function apiCall(endpoint, method = 'GET', body = null) {
    setLoading(true);
    try {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) options.body = JSON.stringify(body);

        const res = await fetch(`${API_URL}${endpoint}`, options);
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Error desconocido');
        return data;
    } catch (error) {
        alert("❌ Error: " + error.message);
        throw error;
    } finally {
        setLoading(false);
    }
}

// --- LOGIC ---
async function createWallet() {
    const pwd = document.getElementById('create-password').value;
    if (!pwd) return alert("La contraseña es obligatoria");

    const data = await apiCall('/wallet/create', 'POST', { password: pwd });
    loginSuccess(data);

    if (data.mnemonic) {
        document.getElementById('mnemonic-alert').classList.remove('hidden');
        document.getElementById('mnemonic-words').innerText = data.mnemonic;
    }
}

async function loadWallet() {
    const pwd = document.getElementById('login-password').value;
    if (!pwd) return alert("Ingresa tu contraseña");

    const data = await apiCall('/wallet/load', 'POST', { password: pwd });
    loginSuccess(data);
}

// CORRECCIÓN AQUÍ: Ya no dividimos por COIN_SCALE. La API ya lo hizo.
async function refreshBalance() {
    if (!currentAddress) return;
    const data = await apiCall(`/balance/${currentAddress}`);

    // data.balance ya viene como "50.0" desde la API
    // Solo aseguramos el formato de 8 decimales
    document.getElementById('balance-amount').innerText = data.balance.toFixed(8);
    document.getElementById('utxo-count').innerText = data.utxo_count;
}

async function sendTransaction() {
    const to = document.getElementById('tx-to').value;
    const amountInput = document.getElementById('tx-amount').value;
    const amount = parseFloat(amountInput);

    if (!amount || amount <= 0) return alert("Ingresa un monto válido");

    if (!confirm(`¿Estás seguro de enviar ${amount} AKM?`)) return;

    // Enviamos el monto tal cual (ej: 1.5). La API lo convertirá a enteros.
    const data = await apiCall('/transactions', 'POST', {
        recipient_address: to,
        amount: amount,
        fee: 0.00001
    });

    alert(`✅ Transacción Exitosa\nHash: ${data.tx_hash}`);
    document.getElementById('tx-amount').value = '';

    setTimeout(refreshBalance, 2000);
}

function loginSuccess(data) {
    currentAddress = data.address;
    document.getElementById('my-address').innerText = currentAddress;

    document.getElementById('view-login').classList.add('hidden');
    document.getElementById('view-dashboard').classList.remove('hidden');

    refreshBalance();
    setInterval(refreshBalance, 5000);
}

function copyAddress() {
    const text = document.getElementById('my-address').innerText;
    navigator.clipboard.writeText(text);
    alert("Dirección copiada al portapapeles");
}

async function checkNode() {
    try {
        const data = await apiCall('/status');
        const badge = document.getElementById('node-status');
        if (badge) {
            badge.innerHTML = `<i class="bi bi-hdd-network-fill"></i> Bloque #${data.height}`;
            badge.className = "badge bg-success d-flex align-items-center gap-2 px-3 py-2 rounded-pill";
        }
    } catch (e) {
        const badge = document.getElementById('node-status');
        if (badge) {
            badge.innerHTML = `<i class="bi bi-wifi-off"></i> Offline`;
            badge.className = "badge bg-danger d-flex align-items-center gap-2 px-3 py-2 rounded-pill";
        }
    }
}

checkNode();
setInterval(checkNode, 3000);