class prometheus::service {

  file { '/etc/systemd/system/prometheus.service':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('prometheus/prometheus.service.erb'),
    notify  => Exec['prometheus-daemon-reload'],
  }

  exec { 'prometheus-daemon-reload':
    command     => '/bin/systemctl daemon-reload',
    refreshonly => true,
  }

  service { 'prometheus':
    ensure    => running,
    enable    => true,
    subscribe => File['/etc/systemd/system/prometheus.service'],
  }

}
