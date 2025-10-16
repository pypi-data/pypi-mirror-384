PUT _cluster/settings
{
  "persistent": {
    "cluster": {
      "remote": {
        "dev-azure-obs-01": {
          "skip_unavailable": true,
          "mode": "proxy",
          "proxy_address": "ruv-sce-dev-azure-obs-01.kb.privatelink.northeurope.azure.elastic-cloud.com:9443",
          "proxy_socket_connections": 18,
          "server_name": "ruv-sce-dev-azure-obs-01.kb.privatelink.northeurope.azure.elastic-cloud.com",
          "seeds": null,
          "node_connections": null
        }
      }
    }
  }
}
