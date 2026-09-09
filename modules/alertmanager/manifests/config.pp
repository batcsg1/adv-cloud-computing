# Class: alertmanager::config
#
# Templates alertmanager.yml. The Teams webhook URL is passed in as a
# Sensitive value - source it from Hiera eyaml, not plaintext.
#
class alertmanager::config {

  file { "${alertmanager::config_dir}/alertmanager.yml":
    ensure  => file,
    content => template('alertmanager/alertmanager.yml.erb'),
    owner   => $alertmanager::user,
    mode    => '0640',
    notify  => Class['alertmanager::service'],
  }
}
