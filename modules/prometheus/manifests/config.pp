class prometheus::config {

  file { '/usr/local/bin/prometheus/prometheus.yml':
    ensure  => file,
    owner   => 'prometheus',
    group   => 'prometheus',
    mode    => '0644',
    content => template('prometheus/prometheus.yml.erb'),
    notify  => Service['prometheus'],
  }

  file { '/usr/local/bin/prometheus/record_rules.yml':
    ensure  => file,
    owner   => 'prometheus',
    group   => 'prometheus',
    mode    => '0644',
    content => template('prometheus/record_rules.yml.erb'),
    notify  => Service['prometheus'],
  }

  file { '/usr/local/bin/prometheus/alert_rules.yml':
    ensure  => file,
    owner   => 'prometheus',
    group   => 'prometheus',
    mode    => '0644',
    content => template('prometheus/alert_rules.yml.erb'),
    notify  => Service['prometheus'],
  }

}
