class node_exporter::service {

  file { '/etc/systemd/system/node_exporter.service':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('node_exporter/node_exporter.service.erb'),
    notify  => Exec['node_exporter_daemon_reload'],
  }

  exec { 'node_exporter_daemon_reload':
    command     => '/bin/systemctl daemon-reload',
    refreshonly => true,
  }

  service { 'node_exporter':
    ensure    => running,
    enable    => true,
    subscribe => File['/etc/systemd/system/node_exporter.service'],
  }

}
