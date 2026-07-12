#!/usr/bin/env python3
"""
Privacy Hub Controller - Phase 3 (Final)
Multi-user per-device policy routing with auth, Tor control, and Panic Button.
"""

import json
import os
import subprocess
import hashlib
import socket
from functools import wraps
from dotenv import load_dotenv
from flask import (Flask, render_template, request, session,
                   redirect, url_for, jsonify)

# Load secrets from .env file
load_dotenv()

# ============================================================
#  CONFIGURATION (Pulled securely from .env)
# ============================================================
FLASK_SECRET_KEY   = os.getenv("FLASK_SECRET_KEY")
ADMIN_PASSWORD      = os.getenv("ADMIN_PASSWORD")
TOR_CONTROL_PASS    = os.getenv("TOR_CONTROL_PASS")

WG_INTERFACE        = "wg0"
WARP_INTERFACE      = "warp0"
WARP_CONF           = "/etc/wireguard/warp0.conf"
WG_SUBNET           = "10.8.0.1"

TOR_TRANSPORT_PORT  = 9040
TOR_DNS_PORT        = 9053
TOR_CONTROL_PORT    = 9051

DEVICES_FILE        = "/home/hm/privacy-hub/devices.json"

TBL_NO_ADS          = 100
TBL_VPN_ONLY        = 101
TBL_FULL_PRIVACY    = 102
TBL_FULLY_HIDDEN    = 103
TBL_PANIC           = 104  # Blackhole table
# ============================================================

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
ADMIN_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "logged_in" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"status": "error", "error": "Unauthorized"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        pw = request.form.get("password", "")
        if hashlib.sha256(pw.encode()).hexdigest() == ADMIN_HASH:
            session["logged_in"] = True
            session.permanent = True
            return redirect(url_for("index"))
        error = "Invalid password"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


def load_devices():
    if not os.path.exists(DEVICES_FILE):
        return []
    with open(DEVICES_FILE, "r") as fh:
        return json.load(fh)


def save_devices(devices):
    with open(DEVICES_FILE, "w") as fh:
        json.dump(devices, fh, indent=2)


@app.route("/api/devices", methods=["GET"])
@login_required
def api_list_devices():
    return jsonify(load_devices())


@app.route("/api/devices", methods=["POST"])
@login_required
def api_add_device():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    ip   = data.get("ip", "").strip()
    if not name or not ip:
        return jsonify({"status": "error", "error": "Name and IP required"}), 400
    devices = load_devices()
    if any(d["ip"] == ip for d in devices):
        return jsonify({"status": "error", "error": "IP already exists"}), 409
    devices.append({"name": name, "ip": ip, "mode": "no_ads"})
    save_devices(devices)
    apply_device_rules(ip, "no_ads")
    return jsonify({"status": "ok"})


@app.route("/api/devices/<path:ip>", methods=["DELETE"])
@login_required
def api_delete_device(ip):
    devices = load_devices()
    devices = [d for d in devices if d["ip"] != ip]
    save_devices(devices)
    clear_device_rules(ip)
    return jsonify({"status": "ok"})


@app.route("/api/devices/<path:ip>/mode", methods=["POST"])
@login_required
def api_set_mode(ip):
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "")
    valid = ["no_ads", "vpn_only", "full_privacy", "fully_hidden", "panic"]
    if mode not in valid:
        return jsonify({"status": "error", "error": "Invalid mode"}), 400
    devices = load_devices()
    for d in devices:
        if d["ip"] == ip:
            d["mode"] = mode
            break
    save_devices(devices)
    apply_device_rules(ip, mode)
    return jsonify({"status": "ok"})


@app.route("/api/tor/newnym", methods=["POST"])
@login_required
def api_tor_newnym():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(("127.0.0.1", TOR_CONTROL_PORT))
        s.sendall('AUTHENTICATE "{}"\r\n'.format(TOR_CONTROL_PASS).encode())
        resp = s.recv(1024).decode().strip()
        if resp != "250 OK":
            s.close()
            return jsonify({"status": "error", "error": "Tor auth failed: " + resp}), 500
        s.sendall(b"SIGNAL NEWNYM\r\n")
        resp = s.recv(1024).decode().strip()
        s.close()
        if "250 OK" in resp:
            return jsonify({"status": "ok", "message": "New Tor circuits built"})
        return jsonify({"status": "error", "error": resp}), 500
    except socket.timeout:
        return jsonify({"status": "error", "error": "Tor control port timed out"}), 500
    except ConnectionRefusedError:
        return jsonify({"status": "error", "error": "Tor control port not reachable"}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


def run(cmd, quiet=False):
    full = ["sudo"] + cmd
    try:
        subprocess.run(full, check=True,
                       stdout=subprocess.DEVNULL if quiet else None,
                       stderr=subprocess.DEVNULL if quiet else None)
    except subprocess.CalledProcessError:
        if not quiet:
            print("[WARN] command failed: " + " ".join(full))


def clear_device_rules(ip):
    for tbl in [TBL_NO_ADS, TBL_VPN_ONLY, TBL_FULL_PRIVACY, TBL_FULLY_HIDDEN, TBL_PANIC]:
        run(["iptables", "-t", "mangle", "-D", "PREROUTING",
             "-s", ip, "-j", "MARK", "--set-mark", str(tbl)], quiet=True)
        run(["ip", "rule", "del", "from", ip, "lookup", str(tbl)], quiet=True)

    run(["iptables", "-t", "nat", "-D", "PREROUTING",
         "-s", ip, "-d", WG_SUBNET, "-j", "RETURN"], quiet=True)
    run(["iptables", "-t", "nat", "-D", "PREROUTING",
         "-s", ip, "-p", "tcp", "-j", "REDIRECT",
         "--to-ports", str(TOR_TRANSPORT_PORT)], quiet=True)
    run(["iptables", "-t", "nat", "-D", "PREROUTING",
         "-s", ip, "-p", "udp", "--dport", "53", "-j", "REDIRECT",
         "--to-ports", str(TOR_DNS_PORT)], quiet=True)

    print("[Rules] Cleared all rules for " + ip)


def apply_device_rules(ip, mode):
    clear_device_rules(ip)

    table_map = {
        "no_ads":       (TBL_NO_ADS,       WG_INTERFACE),
        "vpn_only":     (TBL_VPN_ONLY,     WARP_INTERFACE),
        "full_privacy": (TBL_FULL_PRIVACY, WARP_INTERFACE),
        "fully_hidden": (TBL_FULLY_HIDDEN, None),
        "panic":        (TBL_PANIC,        None),
    }
    tbl, iface = table_map[mode]

    run(["iptables", "-t", "mangle", "-A", "PREROUTING",
         "-s", ip, "-j", "MARK", "--set-mark", str(tbl)])
    run(["ip", "rule", "add", "from", ip, "lookup", str(tbl)])

    if mode == "fully_hidden":
        run(["iptables", "-t", "nat", "-A", "PREROUTING",
             "-s", ip, "-d", WG_SUBNET, "-j", "RETURN"])
        run(["iptables", "-t", "nat", "-A", "PREROUTING",
             "-s", ip, "-p", "tcp", "-j", "REDIRECT",
             "--to-ports", str(TOR_TRANSPORT_PORT)])
        run(["iptables", "-t", "nat", "-A", "PREROUTING",
             "-s", ip, "-p", "udp", "--dport", "53", "-j", "REDIRECT",
             "--to-ports", str(TOR_DNS_PORT)])

    elif mode == "full_privacy":
        run(["iptables", "-t", "nat", "-A", "PREROUTING",
             "-s", ip, "-d", WG_SUBNET, "-j", "RETURN"])
        run(["iptables", "-t", "nat", "-A", "PREROUTING",
             "-s", ip, "-p", "udp", "--dport", "53", "-j", "REDIRECT",
             "--to-ports", str(TOR_DNS_PORT)])
    
    # "panic" mode requires NO nat rules. Traffic goes to table 104, 
    # which routes to 127.0.0.1 and dies silently.

    print("[Rules] Applied '{}' for {} (table {})".format(mode, ip, tbl))


def get_default_gw(interface):
    r = subprocess.run(["ip", "-4", "route", "show", "dev", interface],
                       capture_output=True, text=True)
    for line in r.stdout.strip().split("\n"):
        if line.startswith("default"):
            parts = line.split()
            return parts[2] if len(parts) > 2 else None
    return None


def init_base_layer():
    print("[Init] Initialising base layer...")

    r = subprocess.run(["sudo", "wg", "show", WARP_INTERFACE],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("[Init] {} is down - bringing it up...".format(WARP_INTERFACE))
        subprocess.run(["sudo", "wg-quick", "up", WARP_CONF], check=True)
    else:
        print("[Init] {} is already up.".format(WARP_INTERFACE))

    warp_gw = get_default_gw(WARP_INTERFACE)
    wg_gw   = get_default_gw(WG_INTERFACE)

    if warp_gw:
        for tbl in [TBL_VPN_ONLY, TBL_FULL_PRIVACY]:
            run(["ip", "route", "flush", "table", str(tbl)], quiet=True)
            run(["ip", "route", "add", "default", "via", warp_gw,
                 "dev", WARP_INTERFACE, "table", str(tbl)])

    if wg_gw:
        run(["ip", "route", "flush", "table", str(TBL_NO_ADS)], quiet=True)
        run(["ip", "route", "add", "default", "via", wg_gw,
             "dev", WG_INTERFACE, "table", str(TBL_NO_ADS)])

    # Blackhole tables (Fully Hidden & Panic)
    for tbl in [TBL_FULLY_HIDDEN, TBL_PANIC]:
        run(["ip", "route", "flush", "table", str(tbl)], quiet=True)
        run(["ip", "route", "add", "127.0.0.0/8", "dev", "lo",
             "table", str(tbl)])
        run(["ip", "route", "add", "default", "via", "127.0.0.1", "dev", "lo",
             "table", str(tbl)])

    run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

    run(["iptables", "-I", "FORWARD", "-i", WG_INTERFACE, "-j", "ACCEPT"], quiet=True)
    run(["iptables", "-I", "FORWARD", "-o", WG_INTERFACE, "-j", "ACCEPT"], quiet=True)
    run(["iptables", "-t", "nat", "-A", "POSTROUTING",
         "-o", WARP_INTERFACE, "-j", "MASQUERADE"], quiet=True)

    print("[Init] Base layer ready.\n")


if __name__ == "__main__":
    init_base_layer()

    for dev in load_devices():
        apply_device_rules(dev["ip"], dev["mode"])

    print("[Hub] Starting Privacy Hub Controller on 0.0.0.0:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
