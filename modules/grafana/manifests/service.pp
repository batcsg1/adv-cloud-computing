class grafana::service {
  service { 'grafana-server':
    ensure => running,
    enable => true,
  }
}
