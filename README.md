# uptime-watch

Monitor ringan untuk **status, latency, dan masa berlaku SSL** banyak URL sekaligus. Python stdlib, tanpa `pip install`.

```bash
python3 main.py https://barlve.com https://cpns.barlve.com
python3 main.py --file urls.txt --json hasil.json
python3 main.py https://barlve.com --fail-on down     # cocok untuk cron/CI
```

Cron tiap 5 menit:
```
*/5 * * * * python3 /path/main.py --file /path/urls.txt --fail-on down >> /var/log/uptime.log 2>&1
```

Output: daftar `UP/DOWN`, latency ms, sisa hari SSL, dan ringkasan jumlah yang bermasalah.
