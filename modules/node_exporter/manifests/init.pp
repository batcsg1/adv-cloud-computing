class node_exporter {

  contain node_exporter::install
  contain node_exporter::service

  Class['node_exporter::install']
  -> Class['node_exporter::service']

}
