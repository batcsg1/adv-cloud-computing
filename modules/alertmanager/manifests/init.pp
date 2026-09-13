# Class: alertmanager
#
# Installs and configures Prometheus Alertmanager. Microsoft Teams notifications
# are delivered by Alertmanager's native msteamsv2 receiver, which POSTs an
# Adaptive Card to a Power Automate ("Workflows") webhook URL - no separate
# prometheus-msteams bridge.
# Structured to mirror the openmpi/immich modules: install -> config -> service.
#
# All parameter values are sourced from Hiera (common.yaml for plain config,
# secrets.eyaml for the Teams webhook URL) - no literal defaults here.
#
class alertmanager (
  String        $version,
  String        $install_dir,
  String        $config_dir,
  String        $data_dir,
  String        $user,
  Integer        $group_wait_seconds,
  String        $group_interval,
  String        $repeat_interval,
  Array[String] $group_by,
  Boolean       $manage_teams,
  # Sourced from secrets.eyaml (alertmanager::teams_webhook_url). Left
  # Optional/undef here only so hosts with manage_teams: false compile
  # without needing an entry in secrets.eyaml.
  Optional[String] $teams_webhook_url = undef,
) {

  contain alertmanager::install
  contain alertmanager::config
  contain alertmanager::service

  Class['alertmanager::install']
  -> Class['alertmanager::config']
  ~> Class['alertmanager::service']
}