# Class: alertmanager::install
#
# Downloads the Alertmanager release tarball and installs the binaries.
#
class alertmanager::install {

  $tarball  = "alertmanager-${alertmanager::version}.linux-amd64"
  $download_url = "https://github.com/prometheus/alertmanager/releases/download/v${alertmanager::version}/${tarball}.tar.gz"

  file { [$alertmanager::config_dir, $alertmanager::data_dir]:
    ensure => directory,
    owner  => $alertmanager::user,
    group  => $alertmanager::user,
  }

  file { '/opt/alertmanager-src':
    ensure => directory,
  }

  exec { 'download-alertmanager':
    command => "/usr/bin/wget -q ${download_url} -O /opt/alertmanager-src/${tarball}.tar.gz",
    creates => "/opt/alertmanager-src/${tarball}.tar.gz",
    require => File['/opt/alertmanager-src'],
  }

  exec { 'extract-alertmanager':
    command => "/bin/tar -xzf /opt/alertmanager-src/${tarball}.tar.gz -C /opt/alertmanager-src",
    creates => "/opt/alertmanager-src/${tarball}/alertmanager",
    require => Exec['download-alertmanager'],
  }

  file { "${alertmanager::install_dir}/alertmanager":
    ensure  => file,
    source  => "/opt/alertmanager-src/${tarball}/alertmanager",
    mode    => '0755',
    require => Exec['extract-alertmanager'],
  }

  file { "${alertmanager::install_dir}/amtool":
    ensure  => file,
    source  => "/opt/alertmanager-src/${tarball}/amtool",
    mode    => '0755',
    require => Exec['extract-alertmanager'],
  }
}
