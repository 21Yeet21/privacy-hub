// Privacy Hub Controller - Monkeytype Aesthetic
console.log("[Hub] UI Loaded");

(function () {
    "use strict";

    var status = document.getElementById("status");
    var container = document.getElementById("devicesContainer");
    var addForm = document.getElementById("addDeviceForm");
    var newIdentityBtn = document.getElementById("newIdentityBtn");

    function setStatus(message, type) {
        if (!status) return;
        status.textContent = message;
        status.className = "status" + (type ? " " + type : "");
    }

    function loadDevices() {
        setStatus("Fetching devices...", "loading");
        fetch("/api/devices", { method: "GET" })
            .then(function (response) { 
                if (response.status === 401) { window.location.href = "/login"; return; }
                return response.json(); 
            })
            .then(function (devices) {
                if (!devices) return;
                renderDevices(devices);
                setStatus("Ready. " + devices.length + " device(s) connected.", "");
            })
            .catch(function (err) {
                setStatus("Error fetching devices: " + err.message, "error");
            });
    }

    function renderDevices(devices) {
        container.innerHTML = '';
        if (!devices || devices.length === 0) {
            container.innerHTML = '<p style="color: var(--muted); font-size: 0.85rem;">No devices configured yet. Add one above.</p>';
            return;
        }

        var modes = ['no_ads', 'vpn_only', 'full_privacy', 'fully_hidden', 'panic'];
        
        devices.forEach(function (device) {
            var card = document.createElement("div");
            card.className = "device-card";
            card.setAttribute("data-mode", device.mode);

            var modeButtons = modes.map(function (mode) {
                var isActive = device.mode === mode;
                return '<button class="mode-btn ' + (isActive ? 'active' : '') + '" ' +
                       'data-mode="' + mode + '" ' +
                       'onclick="window.setDeviceMode(\'' + device.ip + '\', \'' + mode + '\')">' +
                       mode.replace(/_/g, ' ') +
                       '</button>';
            }).join('');

            card.innerHTML = `
                <div class="device-info">
                    <h3>${device.name}</h3>
                    <span>${device.ip}</span>
                </div>
                <div class="mode-selector">
                    ${modeButtons}
                    <button class="delete-btn" onclick="window.deleteDevice('${device.ip}')">Delete</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    window.setDeviceMode = function (ip, mode) {
        setStatus("Activating " + mode.replace(/_/g, ' ') + " for " + ip + "...", "loading");
        
        fetch("/api/devices/" + ip + "/mode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: mode })
        })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.status === "ok") {
                setStatus("Mode applied: " + mode.replace(/_/g, ' '), "success");
                loadDevices();
            } else {
                setStatus("Error: " + (data.error || "Unknown"), "error");
            }
        })
        .catch(function (err) {
            setStatus("Request failed: " + err.message, "error");
        });
    };

    window.deleteDevice = function (ip) {
        var ok = window.confirm("Remove this device and clear its rules?");
        if (!ok) return;

        setStatus("Deleting " + ip + "...", "loading");
        fetch("/api/devices/" + ip, { method: "DELETE" })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (data.status === "ok") {
                    setStatus("Device deleted: " + ip, "success");
                    loadDevices();
                } else {
                    setStatus("Error deleting device.", "error");
                }
            })
            .catch(function (err) {
                setStatus("Request failed: " + err.message, "error");
            });
    };

    addForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var name = document.getElementById("deviceName").value;
        var ip = document.getElementById("deviceIP").value;

        setStatus("Adding device " + name + "...", "loading");

        fetch("/api/devices", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name, ip: ip })
        })
        .then(function (response) { return response.json(); })
        .then(function (data) {
            if (data.status === "ok") {
                document.getElementById("deviceName").value = '';
                document.getElementById("deviceIP").value = '';
                setStatus("Device added: " + name, "success");
                loadDevices();
            } else {
                setStatus("Error: " + (data.error || "Unknown"), "error");
            }
        })
        .catch(function (err) {
            setStatus("Request failed: " + err.message, "error");
        });
    });

    // Tor New Identity
    if (newIdentityBtn) {
        newIdentityBtn.addEventListener("click", function () {
            if (!window.confirm("Refresh Tor circuits? This will briefly interrupt Tor traffic.")) return;
            
            setStatus("Requesting new Tor identity...", "loading");
            fetch("/api/tor/newnym", { method: "POST" })
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.status === "ok") {
                        setStatus("Tor circuits refreshed successfully!", "success");
                    } else {
                        setStatus("Error refreshing Tor: " + (data.error || "Unknown"), "error");
                    }
                })
                .catch(function(err) {
                    setStatus("Request failed: " + err.message, "error");
                });
        });
    }

    // Kick off initial load
    loadDevices();
})();
