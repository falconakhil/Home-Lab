# Monitoring

Has the config files for prometheus and the json files for the grafana dashboards.

Prometheus has a retention of 30 days which is set using:
```bash
sysrc prometheus_args="--storage.tsdb.retention.time=30d"
```
