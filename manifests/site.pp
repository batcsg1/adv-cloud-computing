## Puppet master + web server
node 'batcsg1-web.op.ac.nz' {
  include prometheus
  include grafana
  include node_exporter
  include alertmanager
}

## Application server
node 'batcsg1-app.op.ac.nz' {
  include node_exporter
}

## Database server
node 'batcsg1-db.op.ac.nz' {
  include node_exporter
}