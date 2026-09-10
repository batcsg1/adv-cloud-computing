class prometheus::targets (
  Hash            $groups,
  Integer         $port   = 9100,
  String          $domain = 'op.ac.nz',
) {
  file { ['/etc/prometheus', '/etc/prometheus/targets']:
    ensure => directory,
    owner  => 'root',
    group  => 'prometheus',
    mode   => '0750',
  }

  file { '/etc/prometheus/targets/targets.yml':
    ensure  => file,
    owner   => 'root',
    group   => 'prometheus',
    mode    => '0640',
    content => epp('prometheus/targets.yml.epp', {
      'groups' => $groups,
      'port'   => $port,
      'domain' => $domain,
    }),
    require => File['/etc/prometheus/targets'],
  }
}