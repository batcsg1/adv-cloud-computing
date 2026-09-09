class prometheus::targets {
  file { '/etc/prometheus':
    ensure => directory,
    owner  => 'root',
    group  => 'root',
    mode   => '0755',
  }

  file { '/etc/prometheus/targets':
    ensure => directory,
    owner  => 'root',
    group  => 'root',
    mode   => '0755',
  }

  file { '/usr/local/bin/generate-prometheus-targets.sh':
    ensure => file,
    source => 'puppet:///modules/prometheus/generate-prometheus-targets.sh',
    owner  => 'root',
    group  => 'root',
    mode   => '0755',
  }

  cron { 'generate-prometheus-targets':
    command => '/usr/local/bin/generate-prometheus-targets.sh',
    user    => 'root',
    minute  => '*/5',
    require => [
      File['/usr/local/bin/generate-prometheus-targets.sh'],
      File['/etc/prometheus/targets'],
    ],
  }
}
