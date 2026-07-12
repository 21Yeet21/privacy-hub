console.log("[Hub] Phase 3 Final loaded (Panic Button)");

(function () {
    "use strict";

    var status      = document.getElementById("status");
    var container   = document.getElementById("devicesContainer");
    var addForm     = document.getElementById("addDeviceForm");
    var newnymBtn   = document.getElementById("newnymBtn");

    function setStatus(message, type) {
        if (!status) return;
        status.textContent = message;
        status.className = "status" + (type ? " " + type : "");
    }

    function apiFetch(url, options) {
        options = options || {};
        options.headers = options.headers || {};
        if (!options.headers["Content-Type"]) {
            options.headers["Content-Type"] = "application/json";
        }
        return fetch(url, options).then(function (res) {
            if (res.status === 401) {
                window.location.href = "/login";
                throw new Error("Unauthorized");
            }
            return res.json().then(function (data) {
                if (!res.ok) throw new Error(data.error || "Request failed");
                return data;
            });
        });
    }

    function loadDevices() {
        setStatus("Fetching devices...", "loading");
        apiFetch("/api/devices")
            .then(function (devices) {
                renderDevices(devices);
                setStatus("Ready. " + devices.length + " device(s) connected.", "");
            })
            .catch(function (err) {
                if (err.message !== "Unauthorized") {
                    setStatus("Error: " + err.message, "error");
                }
            });
    }

    function renderDevices(devices) {
        container.innerHTML = "";
        if (!devices || devices.length === 0) {
            container.innerHTML = '<p style="color:var(--muted);">No devices configured yet. Add one above.</p>';
            return;
        }

        var modes = ["no_ads", "vpn_only", "full_privacy", "fully_hidden", "panic"];

        devices.forEach(function (device) {
            var card = document.createElement("div");
            card.className = "device-card";

            var modeBtns = modes.map(function (mode) {
                var isActive = device.mode === mode;
                var isDanger = mode === "fully_hidden";
                var isPanic = mode === "panic";
                var cls = "mode-btn";
                if (isActive) cls += " active";
                if (isDanger) cls += " danger";
                if (isPanic) cls += " panic";
                return '<button class="' + cls + '" data-ip="' + device.ip + '" data-mode="' + mode + '">' +
                       mode.replace(/_/g, " ") + "</button>";
            }).join("");

            var badge = '<span class="current-mode-badge ' + device.mode + '">' +
                        device.mode.replace(/_/g, " ") + "</span>";

            card.innerHTML =
                '<div class="device-info">' +
                    '<h3>' + device.name + badge + "</h3>" +
                    "<span>" + device.ip + "</span>" +
                "</div>" +
                '<div class="mode-selector">' +
                    modeBtns +
                    '<button class="delete-btn" data-ip="' + device.ip + '" data-action="delete">Delete</button>' +
                "</div>";

            container.appendChild(card);
        });
    }

    container.addEventListener("click", function (e) {
        var btn = e.target.closest("button");
        if (!btn) return;

        var ip    = btn.getAttribute("data-ip");
        var mode  = btn.getAttribute("data-mode");
        var action = btn.getAttribute("data-action");

        if (action === "delete") {
            if (!window.confirm("Remove this device and clear its rules?")) return;
            setStatus("Deleting " + ip + "...", "loading");
            apiFetch("/api/devices/" + ip, { method: "DELETE" })
                .then(function () {
                    setStatus("Device deleted: " + ip, "success");
                    loadDevices();
                })
                .catch(function (err) {
                    setStatus("Error: " + err.message, "error");
                });
        } else if (mode) {
            setStatus("Applying " + mode.replace(/_/g, " ") + " to " + ip + "...", "loading");
            apiFetch("/api/devices/" + ip + "/mode", {
                method: "POST",
                body: JSON.stringify({ mode: mode })
            })
            .then(function () {
                setStatus("Mode applied: " + mode.replace(/_/g, " ") + " for " + ip, "success");
                loadDevices();
            })
            .catch(function (err) {
                setStatus("Error: " + err.message, "error");
            });
        }
    });

    addForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var name = document.getElementById("deviceName").value;
        var ip   = document.getElementById("deviceIP").value;

        setStatus("Adding " + name + "...", "loading");
        apiFetch("/api/devices", {
            method: "POST",
            body: JSON.stringify({ name: name, ip: ip })
        })
        .then(function () {
            document.getElementById("deviceName").value = "";
            document.getElementById("deviceIP").value = "";
            setStatus("Device added: " + name, "success");
            loadDevices();
        })
        .catch(function (err) {
            setStatus("Error: " + err.message, "error");
        });
    });

    if (newnymBtn) {
        newnymBtn.addEventListener("click", function () {
            newnymBtn.disabled = true;
            newnymBtn.textContent = "Building circuits...";
            setStatus("Requesting new Tor identity...", "loading");

            apiFetch("/api/tor/newnym", { method: "POST" })
                .then(function (data) {
                    setStatus(data.message || "Done", "success");
                })
                .catch(function (err) {
                    setStatus("Tor error: " + err.message, "error");
                })
                .finally(function () {
                    setTimeout(function () {
                        newnymBtn.disabled = false;
                        newnymBtn.innerHTML = "&#x21bb; Refresh Tor Circuits";
                    }, 10000);
                });
        });
    }

    loadDevices();
})();
