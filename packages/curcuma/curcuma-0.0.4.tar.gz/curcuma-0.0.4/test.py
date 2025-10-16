from src import curcuma


curcuma.configure_logger()

azure_obs_cluster_name = "ruv-sce-prod-azure-obs-01"


cld = curcuma.CloudClient(
    api_key="essu_VDA1NU9IazFZMEpDTTNOVFlURm5jV1JIV1RjNk1qUmxlRVl4YW5wVE1rTm9RVUkzWVU5RmIxaHlkdz09AAAAANYE0DE=",
)

cld.deployment._list_cloud_templates("aws-eu-central-1")
