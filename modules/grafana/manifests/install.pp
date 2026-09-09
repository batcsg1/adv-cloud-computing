class grafana::install {

  exec { 'grafana_key':
    command  => 'mkdir -p /etc/apt/keyrings && curl -fsSL https://apt.grafana.com/gpg.key | gpg --dearmor -o /etc/apt/keyrings/grafana.gpg && chmod 0644 /etc/apt/keyrings/grafana.gpg',
    creates  => '/etc/apt/keyrings/grafana.gpg',
    path     => ['/usr/bin', '/bin'],
    provider => shell,
  }

  file { '/etc/apt/sources.list.d/grafana.list':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main\n",
    require => Exec['grafana_key'],
    notify  => Exec['grafana_apt_update'],
  }

  exec { 'grafana_apt_update':
    command     => 'apt-get update',
    refreshonly => true,
    path        => ['/usr/bin', '/bin'],
  }

  package { 'grafana':
    ensure  => installed,
    require => Exec['grafana_apt_update'],
  }

}
