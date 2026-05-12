@echo off
echo Starting Nexus Billing Sandbox Portal on http://127.0.0.1:8080
cd ..\sandbox_portal
python -m http.server 8080 --bind 127.0.0.1
