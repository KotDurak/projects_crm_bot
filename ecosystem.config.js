module.exports = {
  apps: [{
    name: "crm-bot",
    script: "C:\\projects_crm_bot\\projects_crm_bot\\venv\\Scripts\\python.exe",
    args: "main.py",
    cwd: "C:\projects_crm_bot\projects_crm_bot",
    autorestart: true,
    max_restarts: 10,
    min_uptime: "10s",
    error_file: "C:\\Users\\maksim\\python\\crm_bot\\logs\\err.log",
    out_file: "C:\\Users\\maksim\\python\\crm_bot\\logs\\out.log",
    merge_logs: true,
    env: {
      PYTHONUNBUFFERED: "1" // Чтобы логи в PM2 обновлялись в реальном времени
    }
  }]
};