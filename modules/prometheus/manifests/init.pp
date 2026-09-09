class prometheus {

  contain prometheus::install
  contain prometheus::config
  contain prometheus::targets
  contain prometheus::service

  # Enforce application order
  Class['prometheus::install']
  -> Class['prometheus::config']
  -> Class['prometheus::targets']
  ~> Class['prometheus::service']

}
