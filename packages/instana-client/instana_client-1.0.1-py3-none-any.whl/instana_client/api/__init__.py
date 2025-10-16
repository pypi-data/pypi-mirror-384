# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from instana_client.api.ai_management_api import AIManagementApi
    from instana_client.api.api_token_api import APITokenApi
    from instana_client.api.action_catalog_api import ActionCatalogApi
    from instana_client.api.action_history_api import ActionHistoryApi
    from instana_client.api.apdex_report_api import ApdexReportApi
    from instana_client.api.apdex_settings_api import ApdexSettingsApi
    from instana_client.api.application_alert_configuration_api import ApplicationAlertConfigurationApi
    from instana_client.api.application_analyze_api import ApplicationAnalyzeApi
    from instana_client.api.application_catalog_api import ApplicationCatalogApi
    from instana_client.api.application_metrics_api import ApplicationMetricsApi
    from instana_client.api.application_resources_api import ApplicationResourcesApi
    from instana_client.api.application_settings_api import ApplicationSettingsApi
    from instana_client.api.application_topology_api import ApplicationTopologyApi
    from instana_client.api.audit_log_api import AuditLogApi
    from instana_client.api.authentication_api import AuthenticationApi
    from instana_client.api.business_monitoring_api import BusinessMonitoringApi
    from instana_client.api.custom_dashboards_api import CustomDashboardsApi
    from instana_client.api.custom_entities_api import CustomEntitiesApi
    from instana_client.api.end_user_monitoring_api import EndUserMonitoringApi
    from instana_client.api.event_settings_api import EventSettingsApi
    from instana_client.api.events_api import EventsApi
    from instana_client.api.global_application_alert_configuration_api import GlobalApplicationAlertConfigurationApi
    from instana_client.api.groups_api import GroupsApi
    from instana_client.api.health_api import HealthApi
    from instana_client.api.host_agent_api import HostAgentApi
    from instana_client.api.infrastructure_alert_configuration_api import InfrastructureAlertConfigurationApi
    from instana_client.api.infrastructure_analyze_api import InfrastructureAnalyzeApi
    from instana_client.api.infrastructure_catalog_api import InfrastructureCatalogApi
    from instana_client.api.infrastructure_metrics_api import InfrastructureMetricsApi
    from instana_client.api.infrastructure_resources_api import InfrastructureResourcesApi
    from instana_client.api.infrastructure_topology_api import InfrastructureTopologyApi
    from instana_client.api.log_alert_configuration_api import LogAlertConfigurationApi
    from instana_client.api.logging_analyze_api import LoggingAnalyzeApi
    from instana_client.api.maintenance_configuration_api import MaintenanceConfigurationApi
    from instana_client.api.mobile_app_analyze_api import MobileAppAnalyzeApi
    from instana_client.api.mobile_app_catalog_api import MobileAppCatalogApi
    from instana_client.api.mobile_app_configuration_api import MobileAppConfigurationApi
    from instana_client.api.mobile_app_metrics_api import MobileAppMetricsApi
    from instana_client.api.policies_api import PoliciesApi
    from instana_client.api.releases_api import ReleasesApi
    from instana_client.api.roles_api import RolesApi
    from instana_client.api.sli_report_api import SLIReportApi
    from instana_client.api.sli_settings_api import SLISettingsApi
    from instana_client.api.slo_correction_configurations_api import SLOCorrectionConfigurationsApi
    from instana_client.api.slo_correction_windows_api import SLOCorrectionWindowsApi
    from instana_client.api.service_levels_alert_configuration_api import ServiceLevelsAlertConfigurationApi
    from instana_client.api.service_levels_objective_slo_configurations_api import ServiceLevelsObjectiveSLOConfigurationsApi
    from instana_client.api.service_levels_objective_slo_report_api import ServiceLevelsObjectiveSLOReportApi
    from instana_client.api.session_settings_api import SessionSettingsApi
    from instana_client.api.synthetic_alert_configuration_api import SyntheticAlertConfigurationApi
    from instana_client.api.synthetic_calls_api import SyntheticCallsApi
    from instana_client.api.synthetic_catalog_api import SyntheticCatalogApi
    from instana_client.api.synthetic_metrics_api import SyntheticMetricsApi
    from instana_client.api.synthetic_settings_api import SyntheticSettingsApi
    from instana_client.api.synthetic_test_playback_results_api import SyntheticTestPlaybackResultsApi
    from instana_client.api.teams_api import TeamsApi
    from instana_client.api.usage_api import UsageApi
    from instana_client.api.user_api import UserApi
    from instana_client.api.website_analyze_api import WebsiteAnalyzeApi
    from instana_client.api.website_catalog_api import WebsiteCatalogApi
    from instana_client.api.website_configuration_api import WebsiteConfigurationApi
    from instana_client.api.website_metrics_api import WebsiteMetricsApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from instana_client.api.ai_management_api import AIManagementApi
from instana_client.api.api_token_api import APITokenApi
from instana_client.api.action_catalog_api import ActionCatalogApi
from instana_client.api.action_history_api import ActionHistoryApi
from instana_client.api.apdex_report_api import ApdexReportApi
from instana_client.api.apdex_settings_api import ApdexSettingsApi
from instana_client.api.application_alert_configuration_api import ApplicationAlertConfigurationApi
from instana_client.api.application_analyze_api import ApplicationAnalyzeApi
from instana_client.api.application_catalog_api import ApplicationCatalogApi
from instana_client.api.application_metrics_api import ApplicationMetricsApi
from instana_client.api.application_resources_api import ApplicationResourcesApi
from instana_client.api.application_settings_api import ApplicationSettingsApi
from instana_client.api.application_topology_api import ApplicationTopologyApi
from instana_client.api.audit_log_api import AuditLogApi
from instana_client.api.authentication_api import AuthenticationApi
from instana_client.api.business_monitoring_api import BusinessMonitoringApi
from instana_client.api.custom_dashboards_api import CustomDashboardsApi
from instana_client.api.custom_entities_api import CustomEntitiesApi
from instana_client.api.end_user_monitoring_api import EndUserMonitoringApi
from instana_client.api.event_settings_api import EventSettingsApi
from instana_client.api.events_api import EventsApi
from instana_client.api.global_application_alert_configuration_api import GlobalApplicationAlertConfigurationApi
from instana_client.api.groups_api import GroupsApi
from instana_client.api.health_api import HealthApi
from instana_client.api.host_agent_api import HostAgentApi
from instana_client.api.infrastructure_alert_configuration_api import InfrastructureAlertConfigurationApi
from instana_client.api.infrastructure_analyze_api import InfrastructureAnalyzeApi
from instana_client.api.infrastructure_catalog_api import InfrastructureCatalogApi
from instana_client.api.infrastructure_metrics_api import InfrastructureMetricsApi
from instana_client.api.infrastructure_resources_api import InfrastructureResourcesApi
from instana_client.api.infrastructure_topology_api import InfrastructureTopologyApi
from instana_client.api.log_alert_configuration_api import LogAlertConfigurationApi
from instana_client.api.logging_analyze_api import LoggingAnalyzeApi
from instana_client.api.maintenance_configuration_api import MaintenanceConfigurationApi
from instana_client.api.mobile_app_analyze_api import MobileAppAnalyzeApi
from instana_client.api.mobile_app_catalog_api import MobileAppCatalogApi
from instana_client.api.mobile_app_configuration_api import MobileAppConfigurationApi
from instana_client.api.mobile_app_metrics_api import MobileAppMetricsApi
from instana_client.api.policies_api import PoliciesApi
from instana_client.api.releases_api import ReleasesApi
from instana_client.api.roles_api import RolesApi
from instana_client.api.sli_report_api import SLIReportApi
from instana_client.api.sli_settings_api import SLISettingsApi
from instana_client.api.slo_correction_configurations_api import SLOCorrectionConfigurationsApi
from instana_client.api.slo_correction_windows_api import SLOCorrectionWindowsApi
from instana_client.api.service_levels_alert_configuration_api import ServiceLevelsAlertConfigurationApi
from instana_client.api.service_levels_objective_slo_configurations_api import ServiceLevelsObjectiveSLOConfigurationsApi
from instana_client.api.service_levels_objective_slo_report_api import ServiceLevelsObjectiveSLOReportApi
from instana_client.api.session_settings_api import SessionSettingsApi
from instana_client.api.synthetic_alert_configuration_api import SyntheticAlertConfigurationApi
from instana_client.api.synthetic_calls_api import SyntheticCallsApi
from instana_client.api.synthetic_catalog_api import SyntheticCatalogApi
from instana_client.api.synthetic_metrics_api import SyntheticMetricsApi
from instana_client.api.synthetic_settings_api import SyntheticSettingsApi
from instana_client.api.synthetic_test_playback_results_api import SyntheticTestPlaybackResultsApi
from instana_client.api.teams_api import TeamsApi
from instana_client.api.usage_api import UsageApi
from instana_client.api.user_api import UserApi
from instana_client.api.website_analyze_api import WebsiteAnalyzeApi
from instana_client.api.website_catalog_api import WebsiteCatalogApi
from instana_client.api.website_configuration_api import WebsiteConfigurationApi
from instana_client.api.website_metrics_api import WebsiteMetricsApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
