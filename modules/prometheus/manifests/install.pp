class prometheus::install {

  $version = '2.53.4'
  $install_dir = '/usr/local/bin/prometheus'

  user { 'prometheus':
    ensure     => present,
    managehome => false,
    shell      => '/usr/sbin/nologin',
    system     => true,
  }

  exec { 'download_prometheus':
    command => "wget https://github.com/prometheus/prometheus/releases/download/v${version}/prometheus-${version}.linux-amd64.tar.gz",
    cwd     => '/opt',
    creates => "/opt/prometheus-${version}.linux-amd64.tar.gz",
    path    => ['/usr/bin', '/bin'],
  }

  exec { 'extract_prometheus':
    command => "tar -xvf prometheus-${version}.linux-amd64.tar.gz",
    cwd     => '/opt',
    creates => "/opt/prometheus-${version}.linux-amd64/prometheus",
    path    => ['/usr/bin', '/bin'],
    require => Exec['download_prometheus'],
  }

  file { $install_dir:
    ensure  => directory,
    owner   => 'prometheus',
    group   => 'prometheus',
    mode    => '0755',
    require => User['prometheus'],
  }

  exec { 'copy_prometheus_tree':
    command  => "cp -r /opt/prometheus-${version}.linux-amd64/* ${install_dir}/",
    creates  => "${install_dir}/prometheus",
    path     => ['/usr/bin', '/bin'],
    provider => shell,
    require  => [Exec['extract_prometheus'], File[$install_dir]],
  }

  file { '/var/lib/prometheus':
    ensure  => directory,
    owner   => 'prometheus',
    group   => 'prometheus',
    mode    => '0755',
    require => User['prometheus'],
  }

  file { '/var/lib/prometheus/data':
    ensure  => directory,
    owner   => 'prometheus',
    group   => 'prometheus',
    mode    => '0755',
    require => File['/var/lib/prometheus'],
  }

  exec { 'fix_prometheus_permissions':
    command     => "chown -R prometheus:prometheus ${install_dir}",
    path        => ['/usr/bin', '/bin'],
    refreshonly => true,
    subscribe   => Exec['copy_prometheus_tree'],
    require     => User['prometheus'],
  }

}
