class node_exporter::install {

  exec { 'download_node_exporter':
    command => 'wget https://github.com/prometheus/node_exporter/releases/download/v1.9.1/node_exporter-1.9.1.linux-amd64.tar.gz',
    cwd     => '/opt',
    creates => '/opt/node_exporter-1.9.1.linux-amd64.tar.gz',
    path    => ['/usr/bin', '/bin'],
  }

  exec { 'extract_node_exporter':
    command => 'tar -xvf node_exporter-1.9.1.linux-amd64.tar.gz',
    cwd     => '/opt',
    creates => '/opt/node_exporter-1.9.1.linux-amd64/node_exporter',
    path    => ['/usr/bin', '/bin'],
    require => Exec['download_node_exporter'],
  }

  user { 'node_exporter':
    ensure     => present,
    managehome => false,
    shell      => '/usr/sbin/nologin',
  }
  
  # Install the binary into the directory
  file { '/usr/local/bin/node_exporter':
    ensure  => file,
    owner   => 'node_exporter',
    group   => 'node_exporter',
    mode    => '0755',
    source  => '/opt/node_exporter-1.9.1.linux-amd64/node_exporter',
    require => Exec['extract_node_exporter'],
  }

}
