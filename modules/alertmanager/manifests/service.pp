# Class: alertmanager::service
#
# Systemd unit for Alertmanager.
#
class alertmanager::service {

  file { '/etc/systemd/system/alertmanager.service':
    ensure  => file,
    content => template('alertmanager/alertmanager.service.erb'),
    notify  => Exec['alertmanager-systemd-reload'],
  }

  exec { 'alertmanager-systemd-reload':
    command     => '/bin/systemctl daemon-reload',
    refreshonly => true,
  }

  service { 'alertmanager':
    ensure    => running,
    enable    => true,
    subscribe => File['/etc/systemd/system/alertmanager.service'],
    require   => Exec['alertmanager-systemd-reload'],
  }
}
