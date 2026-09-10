# Class: alertmanager
#
# Installs and configures Prometheus Alertmanager. Microsoft Teams notifications
# are delivered by Alertmanager's native msteamsv2 receiver, which POSTs an
# Adaptive Card to a Power Automate ("Workflows") webhook URL - no separate
# prometheus-msteams bridge.
# Structured to mirror the openmpi/immich modules: install -> config -> service.
#
class alertmanager (
  String  $version            = '0.28.1',
  String  $install_dir        = '/usr/local/bin',
  String  $config_dir         = '/etc/alertmanager',
  String  $data_dir           = '/var/lib/alertmanager',
  String  $user                = 'root',
  Integer $group_wait_seconds  = 30,
  String  $group_interval      = '5m',
  String  $repeat_interval     = '5m',
  Array[String] $group_by     = ['alertname', 'severity', 'cluster'],
  # Teams delivery. msteamsv2 needs Alertmanager >= 0.28. Source the URL from
  # Hiera eyaml, not plaintext - it is a bearer credential.
  Boolean $manage_teams       = true,
  # Do not hardcode the real webhook URL here - it is a bearer credential.
  # Source it from Hiera eyaml (e.g. alertmanager::teams_webhook_url in
  # secrets.eyaml) so the signed URL never lands in plaintext in git.
  String $teams_webhook_url = 'https://default450e682488ab4ad2914db0f385da60.0c.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/20/workflows/df59a0d53acc46c3a4e0b946505f2431/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=PlhrbicAx02FeeH2rebB1r7G_30w1PPT6UL2IWclaUo',
) {

  contain alertmanager::install
  contain alertmanager::config
  contain alertmanager::service

  Class['alertmanager::install']
  -> Class['alertmanager::config']
  ~> Class['alertmanager::service']
}
