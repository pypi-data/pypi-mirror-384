# SecOps API Endpoint and SDK Wrapper Module Mapping

Following shows mapping between SecOps [REST Resource](https://cloud.google.com/chronicle/docs/reference/rest) and SDK wrapper module and its respective CLI command (if available).

**Note:** All the REST resources mentioned have suffix `projects.locations.instances`.

|REST Resource                                                                 |Version|secops-wrapper module                                       |CLI Command                            |
|------------------------------------------------------------------------------|-------|------------------------------------------------------------|---------------------------------------|
|dataAccessLabels.create                                                       |v1     |                                                            |                                       |
|dataAccessLabels.delete                                                       |v1     |                                                            |                                       |
|dataAccessLabels.get                                                          |v1     |                                                            |                                       |
|dataAccessLabels.list                                                         |v1     |                                                            |                                       |
|dataAccessLabels.patch                                                        |v1     |                                                            |                                       |
|dataAccessScopes.create                                                       |v1     |                                                            |                                       |
|dataAccessScopes.delete                                                       |v1     |                                                            |                                       |
|dataAccessScopes.get                                                          |v1     |                                                            |                                       |
|dataAccessScopes.list                                                         |v1     |                                                            |                                       |
|dataAccessScopes.patch                                                        |v1     |                                                            |                                       |
|get                                                                           |v1     |                                                            |                                       |
|operations.cancel                                                             |v1     |                                                            |                                       |
|operations.delete                                                             |v1     |                                                            |                                       |
|operations.get                                                                |v1     |                                                            |                                       |
|operations.list                                                               |v1     |                                                            |                                       |
|referenceLists.create                                                         |v1     |chronicle.reference_list.create_reference_list                                                            |secops reference-list create                                       |
|referenceLists.get                                                            |v1     |chronicle.reference_list.get_reference_list                                                            |secops reference-list get                                       |
|referenceLists.list                                                           |v1     |chronicle.reference_list.list_reference_lists               |secops reference-list list                                       |
|referenceLists.patch                                                          |v1     |chronicle.reference_list.update_reference_list              |secops reference-list update                                       |
|rules.create                                                                  |v1     |chronicle.rule.create_rule                                  |secops rule create                                       |
|rules.delete                                                                  |v1     |chronicle.rule.delete_rule                                  |secops rule delete                                       |
|rules.deployments.list                                                        |v1     |                                                            |                                       |
|rules.get                                                                     |v1     |chronicle.rule.get_rule                                     |secops rule get                                       |
|rules.getDeployment                                                           |v1     |                                                            |                                       |
|rules.list                                                                    |v1     |chronicle.rule.list_rules                                   |secops rule list                                       |
|rules.listRevisions                                                           |v1     |                                                            |                                       |
|rules.patch                                                                   |v1     |chronicle.rule.update_rule                                  |secops rule update                                       |
|rules.retrohunts.create                                                       |v1     |chronicle.rule_retrohunt.create_retrohunt                                                            |                                       |
|rules.retrohunts.get                                                          |v1     |chronicle.rule_retrohunt.get_retrohunt                                                            |                                       |
|rules.retrohunts.list                                                         |v1     |                                                            |                                       |
|rules.updateDeployment                                                        |v1     |chronicle.rule.enable_rule                                  |secops rule enable                                       |
|watchlists.create                                                             |v1     |                                                            |                                       |
|watchlists.delete                                                             |v1     |                                                            |                                       |
|watchlists.get                                                                |v1     |                                                            |                                       |
|watchlists.list                                                               |v1     |                                                            |                                       |
|watchlists.patch                                                              |v1     |                                                            |                                       |
|dataAccessLabels.create                                                       |v1beta |                                                            |                                       |
|dataAccessLabels.delete                                                       |v1beta |                                                            |                                       |
|dataAccessLabels.get                                                          |v1beta |                                                            |                                       |
|dataAccessLabels.list                                                         |v1beta |                                                            |                                       |
|dataAccessLabels.patch                                                        |v1beta |                                                            |                                       |
|dataAccessScopes.create                                                       |v1beta |                                                            |                                       |
|dataAccessScopes.delete                                                       |v1beta |                                                            |                                       |
|dataAccessScopes.get                                                          |v1beta |                                                            |                                       |
|dataAccessScopes.list                                                         |v1beta |                                                            |                                       |
|dataAccessScopes.patch                                                        |v1beta |                                                            |                                       |
|get                                                                           |v1beta |                                                            |                                       |
|operations.cancel                                                             |v1beta |                                                            |                                       |
|operations.delete                                                             |v1beta |                                                            |                                       |
|operations.get                                                                |v1beta |                                                            |                                       |
|operations.list                                                               |v1beta |                                                            |                                       |
|referenceLists.create                                                         |v1beta |                                                            |                                       |
|referenceLists.get                                                            |v1beta |                                                            |                                       |
|referenceLists.list                                                           |v1beta |                                                            |                                       |
|referenceLists.patch                                                          |v1beta |                                                            |                                       |
|rules.create                                                                  |v1beta |                                                            |                                       |
|rules.delete                                                                  |v1beta |                                                            |                                       |
|rules.deployments.list                                                        |v1beta |                                                            |                                       |
|rules.get                                                                     |v1beta |                                                            |                                       |
|rules.getDeployment                                                           |v1beta |                                                            |                                       |
|rules.list                                                                    |v1beta |                                                            |                                       |
|rules.listRevisions                                                           |v1beta |                                                            |                                       |
|rules.patch                                                                   |v1beta |                                                            |                                       |
|rules.retrohunts.create                                                       |v1beta |                                                            |                                       |
|rules.retrohunts.get                                                          |v1beta |                                                            |                                       |
|rules.retrohunts.list                                                         |v1beta |                                                            |                                       |
|rules.updateDeployment                                                        |v1beta |                                                            |                                       |
|watchlists.create                                                             |v1beta |                                                            |                                       |
|watchlists.delete                                                             |v1beta |                                                            |                                       |
|watchlists.get                                                                |v1beta |                                                            |                                       |
|watchlists.list                                                               |v1beta |                                                            |                                       |
|watchlists.patch                                                              |v1beta |                                                            |                                       |
|analytics.entities.analyticValues.list                                        |v1alpha|                                                            |                                       |
|analytics.list                                                                |v1alpha|                                                            |                                       |
|batchValidateWatchlistEntities                                                |v1alpha|                                                            |                                       |
|bigQueryAccess.provide                                                        |v1alpha|                                                            |                                       |
|bigQueryExport.provision                                                      |v1alpha|                                                            |                                       |
|cases.countPriorities                                                         |v1alpha|                                                            |                                       |
|curatedRuleSetCategories.curatedRuleSets.curatedRuleSetDeployments.batchUpdate|v1alpha|chronicle.rule_set.batch_update_curated_rule_set_deployments|                                       |
|curatedRuleSetCategories.curatedRuleSets.curatedRuleSetDeployments.patch      |v1alpha|                                                            |                                       |
|curatedRuleSetCategories.curatedRuleSets.get                                  |v1alpha|                                                            |                                       |
|curatedRuleSetCategories.curatedRuleSets.list                                 |v1alpha|                                                            |                                       |
|curatedRuleSetCategories.get                                                  |v1alpha|                                                            |                                       |
|curatedRuleSetCategories.list                                                 |v1alpha|                                                            |                                       |
|curatedRules.get                                                              |v1alpha|                                                            |                                       |
|curatedRules.list                                                             |v1alpha|                                                            |                                       |
|dashboardCharts.batchGet                                                      |v1alpha|                                                            |                                       |
|dashboardCharts.get                                                |v1alpha|chronicle.dashboard.get_chart                                                              |secops dashboard get-chart                                       |
|dashboardQueries.execute                                                      |v1alpha|chronicle.dashboard_query.execute_query                                                            |secops dashboard-query execute                                       |
|dashboardQueries.get                                                          |v1alpha|chronicle.dashboard_query.get_execute_query                                                            |secops dashboard-query get                                       |
|dashboards.copy                                                               |v1alpha|                                                            |                                       |
|dashboards.create                                                             |v1alpha|                                                            |                                       |
|dashboards.delete                                                             |v1alpha|                                                            |                                       |
|dashboards.get                                                                |v1alpha|                                                            |                                       |
|dashboards.list                                                               |v1alpha|                                                            |                                       |
|dataAccessLabels.create                                                       |v1alpha|                                                            |                                       |
|dataAccessLabels.delete                                                       |v1alpha|                                                            |                                       |
|dataAccessLabels.get                                                          |v1alpha|                                                            |                                       |
|dataAccessLabels.list                                                         |v1alpha|                                                            |                                       |
|dataAccessLabels.patch                                                        |v1alpha|                                                            |                                       |
|dataAccessScopes.create                                                       |v1alpha|                                                            |                                       |
|dataAccessScopes.delete                                                       |v1alpha|                                                            |                                       |
|dataAccessScopes.get                                                          |v1alpha|                                                            |                                       |
|dataAccessScopes.list                                                         |v1alpha|                                                            |                                       |
|dataAccessScopes.patch                                                        |v1alpha|                                                            |                                       |
|dataExports.cancel                                                            |v1alpha|chronicle.data_export.cancel_data_export                    |secops export cancel                   |
|dataExports.create                                                            |v1alpha|chronicle.data_export.create_data_export                    |secops export create                   |
|dataExports.fetchavailablelogtypes                                            |v1alpha|chronicle.data_export.fetch_available_log_types             |secops export log-types                |
|dataExports.get                                                               |v1alpha|chronicle.data_export.get_data_export                       |secops export status                   |
|dataExports.list                                                               |v1alpha|chronicle.data_export.list_data_export                       |secops export list                   |
|dataExports.patch                                                               |v1alpha|chronicle.data_export.update_data_export                       |secops export update                   |
|dataTableOperationErrors.get                                                  |v1alpha|                                                            |                                       |
|dataTables.create                                                             |v1alpha|chronicle.data_table.create_data_table                      |secops data-table create               |
|dataTables.dataTableRows.bulkCreate                                           |v1alpha|chronicle.data_table.create_data_table_rows                 |secops data-table add-rows             |
|dataTables.dataTableRows.bulkCreateAsync                                      |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.bulkGet                                              |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.bulkReplace                                          |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.bulkReplaceAsync                                     |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.bulkUpdate                                           |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.bulkUpdateAsync                                      |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.create                                               |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.delete                                               |v1alpha|chronicle.data_table.delete_data_table_rows                 |secops data-table delete-rows          |
|dataTables.dataTableRows.get                                                  |v1alpha|                                                            |                                       |
|dataTables.dataTableRows.list                                                 |v1alpha|chronicle.data_table.list_data_table_rows                   |secops data-table list-rows            |
|dataTables.dataTableRows.patch                                                |v1alpha|                                                            |                                       |
|dataTables.delete                                                             |v1alpha|chronicle.data_table.delete_data_table                      |secops data-table delete               |
|dataTables.get                                                                |v1alpha|chronicle.data_table.get_data_table                         |secops data-table get                  |
|dataTables.list                                                               |v1alpha|chronicle.data_table.list_data_tables                       |secops data-table list                 |
|dataTables.patch                                                              |v1alpha|                                                            |                                       |
|dataTables.upload                                                             |v1alpha|                                                            |                                       |
|dataTaps.create                                                               |v1alpha|                                                            |                                       |
|dataTaps.delete                                                               |v1alpha|                                                            |                                       |
|dataTaps.get                                                                  |v1alpha|                                                            |                                       |
|dataTaps.list                                                                 |v1alpha|                                                            |                                       |
|dataTaps.patch                                                                |v1alpha|                                                            |                                       |
|delete                                                                        |v1alpha|                                                            |                                       |
|enrichmentControls.create                                                     |v1alpha|                                                            |                                       |
|enrichmentControls.delete                                                     |v1alpha|                                                            |                                       |
|enrichmentControls.get                                                        |v1alpha|                                                            |                                       |
|enrichmentControls.list                                                       |v1alpha|                                                            |                                       |
|entities.get                                                                  |v1alpha|                                                            |                                       |
|entities.import                                                               |v1alpha|                                                            |                                       |
|entities.modifyEntityRiskScore                                                |v1alpha|                                                            |                                       |
|entities.queryEntityRiskScoreModifications                                    |v1alpha|                                                            |                                       |
|entityRiskScores.query                                                        |v1alpha|                                                            |                                       |
|errorNotificationConfigs.create                                               |v1alpha|                                                            |                                       |
|errorNotificationConfigs.delete                                               |v1alpha|                                                            |                                       |
|errorNotificationConfigs.get                                                  |v1alpha|                                                            |                                       |
|errorNotificationConfigs.list                                                 |v1alpha|                                                            |                                       |
|errorNotificationConfigs.patch                                                |v1alpha|                                                            |                                       |
|events.batchGet                                                               |v1alpha|                                                            |                                       |
|events.get                                                                    |v1alpha|                                                            |                                       |
|events.import                                                                 |v1alpha|chronicle.log_ingest.ingest_udm                             |secops log ingest-udm                  |
|extractSyslog                                                                 |v1alpha|                                                            |                                       |
|federationGroups.create                                                       |v1alpha|                                                            |                                       |
|federationGroups.delete                                                       |v1alpha|                                                            |                                       |
|federationGroups.get                                                          |v1alpha|                                                            |                                       |
|federationGroups.list                                                         |v1alpha|                                                            |                                       |
|federationGroups.patch                                                        |v1alpha|                                                            |                                       |
|feedPacks.get                                                                 |v1alpha|                                                            |                                       |
|feedPacks.list                                                                |v1alpha|                                                            |                                       |
|feedServiceAccounts.fetchServiceAccountForCustomer                            |v1alpha|                                                            |                                       |
|feedSourceTypeSchemas.list                                                    |v1alpha|                                                            |                                       |
|feedSourceTypeSchemas.logTypeSchemas.list                                     |v1alpha|                                                            |                                       |
|feeds.create                                                                  |v1alpha|chronicle.feeds.create_feed                                 |secops feed create                     |
|feeds.delete                                                                  |v1alpha|chronicle.feeds.delete_feed                                 |secops feed delete                     |
|feeds.disable                                                                 |v1alpha|chronicle.feeds.disable_feed                                |secops feed disable                    |
|feeds.enable                                                                  |v1alpha|chronicle.feeds.enable_feed                                 |secops feed enable                     |
|feeds.generateSecret                                                          |v1alpha|chronicle.feeds.generate_secret                             |secops feed secret                     |
|feeds.get                                                                     |v1alpha|chronicle.feeds.get_feed                                    |secops feed get                        |
|feeds.importPushLogs                                                          |v1alpha|                                                            |                                       |
|feeds.list                                                                    |v1alpha|chronicle.feeds.list_feeds                                  |secops feed list                       |
|feeds.patch                                                                   |v1alpha|chronicle.feeds.update_feed                                 |secops feed update                     |
|feeds.scheduleTransfer                                                        |v1alpha|                                                            |                                       |
|fetchFederationAccess                                                         |v1alpha|                                                            |                                       |
|findEntity                                                                    |v1alpha|                                                            |                                       |
|findEntityAlerts                                                              |v1alpha|                                                            |                                       |
|findRelatedEntities                                                           |v1alpha|                                                            |                                       |
|findUdmFieldValues                                                            |v1alpha|                                                            |                                       |
|findingsGraph.exploreNode                                                     |v1alpha|                                                            |                                       |
|findingsGraph.initializeGraph                                                 |v1alpha|                                                            |                                       |
|findingsRefinements.computeFindingsRefinementActivity                         |v1alpha|chronicle.rule_exclusion.compute_rule_exclusion_activity    |secops rule-exclusion compute-activity |
|findingsRefinements.create                                                    |v1alpha|chronicle.rule_exclusion.create_rule_exclusion              |secops rule-exclusion create           |
|findingsRefinements.get                                                       |v1alpha|chronicle.rule_exclusion.get_rule_exclusion                 |secops rule-exclusion get              |
|findingsRefinements.getDeployment                                             |v1alpha|chronicle.rule_exclusion.get_rule_exclusion_deployment      |secops rule-exclusion get-deployment   |
|findingsRefinements.list                                                      |v1alpha|chronicle.rule_exclusion.list_rule_exclusions               |secops rule-exclusion list             |
|findingsRefinements.patch                                                     |v1alpha|chronicle.rule_exclusion.patch_rule_exclusion               |secops rule-exclusion update           |
|findingsRefinements.updateDeployment                                          |v1alpha|chronicle.rule_exclusion.update_rule_exclusion_deployment   |secops rule-exclusion update-deployment|
|forwarders.collectors.create                                                  |v1alpha|                                                            |                                       |
|forwarders.collectors.delete                                                  |v1alpha|                                                            |                                       |
|forwarders.collectors.get                                                     |v1alpha|                                                            |                                       |
|forwarders.collectors.list                                                    |v1alpha|                                                            |                                       |
|forwarders.collectors.patch                                                   |v1alpha|                                                            |                                       |
|forwarders.create                                                             |v1alpha|chronicle.log_ingest.create_forwarder                       |secops forwarder create                                       |
|forwarders.delete                                                             |v1alpha|chronicle.log_ingest.delete_forwarder                       |secops forwarder delete                                       |
|forwarders.generateForwarderFiles                                             |v1alpha|                                                            |                                       |
|forwarders.get                                                                |v1alpha|chronicle.log_ingest.get_forwarder                       |secops forwarder get                                       |
|forwarders.importStatsEvents                                                  |v1alpha|                                                            |                                       |
|forwarders.list                                                               |v1alpha|chronicle.log_ingest.list_forwarder                       |secops forwarder list                                       |
|forwarders.patch                                                              |v1alpha|chronicle.log_ingest.update_forwarder                       |secops forwarder update                                       |
|generateCollectionAgentAuth                                                   |v1alpha|                                                            |                                       |
|generateSoarAuthJwt                                                           |v1alpha|                                                            |                                       |
|generateUdmKeyValueMappings                                                   |v1alpha|                                                            |                                       |
|generateWorkspaceConnectionToken                                              |v1alpha|                                                            |                                       |
|get                                                                           |v1alpha|                                                            |                                       |
|getBigQueryExport                                                             |v1alpha|                                                            |                                       |
|getMultitenantDirectory                                                       |v1alpha|                                                            |                                       |
|getRiskConfig                                                                 |v1alpha|                                                            |                                       |
|ingestionLogLabels.get                                                        |v1alpha|                                                            |                                       |
|ingestionLogLabels.list                                                       |v1alpha|                                                            |                                       |
|ingestionLogNamespaces.get                                                    |v1alpha|                                                            |                                       |
|ingestionLogNamespaces.list                                                   |v1alpha|                                                            |                                       |
|iocs.batchGet                                                                 |v1alpha|                                                            |                                       |
|iocs.findFirstAndLastSeen                                                     |v1alpha|                                                            |                                       |
|iocs.get                                                                      |v1alpha|                                                            |                                       |
|iocs.getIocState                                                              |v1alpha|                                                            |                                       |
|iocs.searchCuratedDetectionsForIoc                                            |v1alpha|                                                            |                                       |
|iocs.updateIocState                                                           |v1alpha|                                                            |                                       |
|legacy.legacyBatchGetCases                                                    |v1alpha|chronicle.case.get_cases_from_list                          |secops case                            |
|legacy.legacyBatchGetCollections                                              |v1alpha|                                                            |                                       |
|legacy.legacyCreateOrUpdateCase                                               |v1alpha|                                                            |                                       |
|legacy.legacyCreateSoarAlert                                                  |v1alpha|                                                            |                                       |
|legacy.legacyFetchAlertsView                                                  |v1alpha|chronicle.alert.get_alerts                                  |secops alert                           |
|legacy.legacyFetchUdmSearchCsv                                                |v1alpha|chronicle.udm_search.fetch_udm_search_csv                   |secops search --csv                    |
|legacy.legacyFetchUdmSearchView                                               |v1alpha|chronicle.udm_search.fetch_udm_search_view                                                            |secops udm-search-view                                       |
|legacy.legacyFindAssetEvents                                                  |v1alpha|                                                            |                                       |
|legacy.legacyFindRawLogs                                                      |v1alpha|                                                            |                                       |
|legacy.legacyFindUdmEvents                                                    |v1alpha|                                                            |                                       |
|legacy.legacyGetAlert                                                         |v1alpha|chronicle.rule_alert.get_alert                              |                                       |
|legacy.legacyGetCuratedRulesTrends                                            |v1alpha|                                                            |                                       |
|legacy.legacyGetDetection                                                     |v1alpha|                                                            |                                       |
|legacy.legacyGetEventForDetection                                             |v1alpha|                                                            |                                       |
|legacy.legacyGetRuleCounts                                                    |v1alpha|                                                            |                                       |
|legacy.legacyGetRulesTrends                                                   |v1alpha|                                                            |                                       |
|legacy.legacyListCases                                                        |v1alpha|chronicle.case.get_cases                                    |secops case --ids                      |
|legacy.legacyRunTestRule                                                      |v1alpha|chronicle.rule.run_rule_test                                |secops rule validate                   |
|legacy.legacySearchArtifactEvents                                             |v1alpha|                                                            |                                       |
|legacy.legacySearchArtifactIoCDetails                                         |v1alpha|                                                            |                                       |
|legacy.legacySearchAssetEvents                                                |v1alpha|                                                            |                                       |
|legacy.legacySearchCuratedDetections                                          |v1alpha|                                                            |                                       |
|legacy.legacySearchCustomerStats                                              |v1alpha|                                                            |                                       |
|legacy.legacySearchDetections                                                 |v1alpha|chronicle.rule_detection.list_detections                    |                                       |
|legacy.legacySearchDomainsRecentlyRegistered                                  |v1alpha|                                                            |                                       |
|legacy.legacySearchDomainsTimingStats                                         |v1alpha|                                                            |                                       |
|legacy.legacySearchEnterpriseWideAlerts                                       |v1alpha|                                                            |                                       |
|legacy.legacySearchEnterpriseWideIoCs                                         |v1alpha|chronicle.ioc.list_iocs                                     |secops iocs                            |
|legacy.legacySearchFindings                                                   |v1alpha|                                                            |                                       |
|legacy.legacySearchIngestionStats                                             |v1alpha|                                                            |                                       |
|legacy.legacySearchIoCInsights                                                |v1alpha|                                                            |                                       |
|legacy.legacySearchRawLogs                                                    |v1alpha|                                                            |                                       |
|legacy.legacySearchRuleDetectionCountBuckets                                  |v1alpha|                                                            |                                       |
|legacy.legacySearchRuleDetectionEvents                                        |v1alpha|                                                            |                                       |
|legacy.legacySearchRuleResults                                                |v1alpha|                                                            |                                       |
|legacy.legacySearchRulesAlerts                                                |v1alpha|chronicle.rule_alert.search_rule_alerts                     |                                       |
|legacy.legacySearchUserEvents                                                 |v1alpha|                                                            |                                       |
|legacy.legacyStreamDetectionAlerts                                            |v1alpha|                                                            |                                       |
|legacy.legacyTestRuleStreaming                                                |v1alpha|                                                            |                                       |
|legacy.legacyUpdateAlert                                                      |v1alpha|chronicle.rule_alert.update_alert                           |                                       |
|listAllFindingsRefinementDeployments                                          |v1alpha|                                                            |                                       |
|logTypes.create                                                               |v1alpha|                                                            |                                       |
|logTypes.generateEventTypesSuggestions                                        |v1alpha|                                                            |                                       |
|logTypes.get                                                                  |v1alpha|                                                            |                                       |
|logTypes.getLogTypeSetting                                                    |v1alpha|                                                            |                                       |
|logTypes.legacySubmitParserExtension                                          |v1alpha|                                                            |                                       |
|logTypes.list                                                                 |v1alpha|                                                            |                                       |
|logTypes.logs.export                                                          |v1alpha|                                                            |                                       |
|logTypes.logs.get                                                             |v1alpha|                                                            |                                       |
|logTypes.logs.import                                                          |v1alpha|chronicle.log_ingest.ingest_log                             |secops log ingest                      |
|logTypes.logs.list                                                            |v1alpha|                                                            |                                       |
|logTypes.parserExtensions.activate                                            |v1alpha|chronicle.parser_extension.activate_parser_extension                                                            |secops parser-extension activate                                       |
|logTypes.parserExtensions.create                                              |v1alpha|chronicle.parser_extension.create_parser_extension                                                            |secops parser-extension create                                       |
|logTypes.parserExtensions.delete                                              |v1alpha|chronicle.parser_extension.delete_parser_extension                                                            |secops parser-extension delete                                       |
|logTypes.parserExtensions.extensionValidationReports.get                      |v1alpha|                                                            |                                       |
|logTypes.parserExtensions.extensionValidationReports.list                     |v1alpha|                                                            |                                       |
|logTypes.parserExtensions.extensionValidationReports.validationErrors.list    |v1alpha|                                                            |                                       |
|logTypes.parserExtensions.get                                                 |v1alpha|chronicle.parser_extension.get_parser_extension                                                            |secops parser-extension get                                       |
|logTypes.parserExtensions.list                                                |v1alpha|chronicle.parser_extension.list_parser_extensions                                                            |secops parser-extension list                                       |
|logTypes.parserExtensions.validationReports.get                               |v1alpha|                                                            |                                       |
|logTypes.parserExtensions.validationReports.parsingErrors.list                |v1alpha|                                                            |                                       |
|logTypes.parsers.activate                                                     |v1alpha|chronicle.parser.activate_parser                            |secops parser activate                 |
|logTypes.parsers.activateReleaseCandidateParser                               |v1alpha|chronicle.parser.activate_release_candidate                 |secops parser activate-rc              |
|logTypes.parsers.copy                                                         |v1alpha|chronicle.parser.copy_parser                                |secops parser copy                     |
|logTypes.parsers.create                                                       |v1alpha|chronicle.parser.create_parser                              |secops parser create                   |
|logTypes.parsers.deactivate                                                   |v1alpha|chronicle.parser.deactivate_parser                          |secops parser deactivate               |
|logTypes.parsers.delete                                                       |v1alpha|chronicle.parser.delete_parser                              |secops parser delete                   |
|logTypes.parsers.get                                                          |v1alpha|chronicle.parser.get_parser                                 |secops parser get                      |
|logTypes.parsers.list                                                         |v1alpha|chronicle.parser.list_parsers                               |secops parser list                     |
|logTypes.parsers.validationReports.get                                        |v1alpha|                                                            |                                       |
|logTypes.parsers.validationReports.parsingErrors.list                         |v1alpha|                                                            |                                       |
|logTypes.patch                                                                |v1alpha|                                                            |                                       |
|logTypes.runParser                                                            |v1alpha|chronicle.parser.run_parser                                 |secops parser run                      |
|logTypes.updateLogTypeSetting                                                 |v1alpha|                                                            |                                       |
|logs.classify                                                                 |v1alpha|                                                            |                                       |
| nativeDashboards.addChart                                                      | v1alpha |chronicle.dashboard.add_chart                                                              |secops dashboard add-chart                                         |
| nativeDashboards.create                                                        | v1alpha |chronicle.dashboard.create_dashboard                                                              |secops dashboard create                                         |
| nativeDashboards.delete                                                        | v1alpha |chronicle.dashboard.delete_dashboard                                                              |secops dashboard delete                                         |
| nativeDashboards.duplicate                                                     | v1alpha |chronicle.dashboard.duplicate_dashboard                                                              |secops dashboard duplicate                                         |
| nativeDashboards.duplicateChart                                                | v1alpha |                                                              |                                         |
| nativeDashboards.editChart                                                     | v1alpha |chronicle.dashboard.edit_chart                                                              |secops dashboard edit-chart                                         |
| nativeDashboards.export                                                        | v1alpha |chronicle.dashboard.export_dashboard                                                              |secops dashboard export                                         |
| nativeDashboards.get                                                           | v1alpha |chronicle.dashboard.get_dashboard                                                              |secops dashboard get                                         |
| nativeDashboards.import                                                        | v1alpha |chronicle.dashboard.import_dashboard                                                              |secops dashboard import                                         |
| nativeDashboards.list                                                          | v1alpha |chronicle.dashboard.list_dashboards                                                              |secops dashboard list                                         |
| nativeDashboards.patch                                                         | v1alpha |chronicle.dashboard.update_dashboard                                                              |secops dashboard update                                         |
| nativeDashboards.removeChart                                                   | v1alpha |chronicle.dashboard.remove_chart                                                              |secops dashboard remove-chart                                         |
|operations.cancel                                                             |v1alpha|                                                            |                                       |
|operations.delete                                                             |v1alpha|                                                            |                                       |
|operations.get                                                                |v1alpha|                                                            |                                       |
|operations.list                                                               |v1alpha|                                                            |                                       |
|operations.streamSearch                                                       |v1alpha|                                                            |                                       |
|queryProductSourceStats                                                       |v1alpha|                                                            |                                       |
|referenceLists.create                                                         |v1alpha|              |           |
|referenceLists.get                                                            |v1alpha|                 |              |
|referenceLists.list                                                           |v1alpha|                    |                                       |
|referenceLists.patch                                                          |v1alpha|                    |           |
|report                                                                        |v1alpha|                                                            |                                       |
|ruleExecutionErrors.list                                                      |v1alpha|chronicle.rule_detection.list_errors                        |                                       |
|rules.create                                                                  |v1alpha|                    |                     |
|rules.delete                                                                  |v1alpha|                    |                     |
|rules.deployments.list                                                        |v1alpha|                                                            |                                       |
|rules.get                                                                     |v1alpha|                    |                        |
|rules.getDeployment                                                           |v1alpha|                                                            |                                       |
|rules.list                                                                    |v1alpha|                    |                       |
|rules.listRevisions                                                           |v1alpha|                                                            |                                       |
|rules.patch                                                                   |v1alpha|                    |                     |
|rules.retrohunts.create                                                       |v1alpha|                   |                                       |
|rules.retrohunts.get                                                          |v1alpha|                      |                                       |
|rules.retrohunts.list                                                         |v1alpha|                                                            |                                       |
|rules.updateDeployment                                                        |v1alpha|                    |                     |
|searchEntities                                                                |v1alpha|                                                            |                                       |
|searchRawLogs                                                                 |v1alpha|                                                            |                                       |
|summarizeEntitiesFromQuery                                                    |v1alpha|chronicle.entity.summarize_entity                           |secops entity                          |
|summarizeEntity                                                               |v1alpha|chronicle.entity.summarize_entity                           |                                       |
|testFindingsRefinement                                                        |v1alpha|                                                            |                                       |
|translateUdmQuery                                                             |v1alpha|chronicle.nl_search.translate_nl_to_udm                     |                                       |
|translateYlRule                                                               |v1alpha|                                                            |                                       |
|udmSearch                                                                     |v1alpha|chronicle.search.search_udm                                 |secops search                          |
|undelete                                                                      |v1alpha|                                                            |                                       |
|updateBigQueryExport                                                          |v1alpha|                                                            |                                       |
|updateRiskConfig                                                              |v1alpha|                                                            |                                       |
|users.clearConversationHistory                                                |v1alpha|                                                            |                                       |
|users.conversations.create                                                    |v1alpha|chronicle.gemini.create_conversation                        |                                       |
|users.conversations.delete                                                    |v1alpha|                                                            |                                       |
|users.conversations.get                                                       |v1alpha|                                                            |                                       |
|users.conversations.list                                                      |v1alpha|                                                            |                                       |
|users.conversations.messages.create                                           |v1alpha|chronicle.gemini.query_gemini                               |secops gemini                          |
|users.conversations.messages.delete                                           |v1alpha|                                                            |                                       |
|users.conversations.messages.get                                              |v1alpha|                                                            |                                       |
|users.conversations.messages.list                                             |v1alpha|                                                            |                                       |
|users.conversations.messages.patch                                            |v1alpha|                                                            |                                       |
|users.conversations.patch                                                     |v1alpha|                                                            |                                       |
|users.getPreferenceSet                                                        |v1alpha|chronicle.gemini.opt_in_to_gemini                           |secops gemini --opt-in                 |
|users.searchQueries.create                                                    |v1alpha|                                                            |                                       |
|users.searchQueries.delete                                                    |v1alpha|                                                            |                                       |
|users.searchQueries.get                                                       |v1alpha|                                                            |                                       |
|users.searchQueries.list                                                      |v1alpha|                                                            |                                       |
|users.searchQueries.patch                                                     |v1alpha|                                                            |                                       |
|users.updatePreferenceSet                                                     |v1alpha|                                                            |                                       |
|validateQuery                                                                 |v1alpha|chronicle.validate.validate_query                           |                                       |
|verifyReferenceList                                                           |v1alpha|                                                            |                                       |
|verifyRuleText                                                                |v1alpha|chronicle.rule_validation.validate_rule                     |secops rule validate                   |
|watchlists.create                                                             |v1alpha|                                                            |                                       |
|watchlists.delete                                                             |v1alpha|                                                            |                                       |
|watchlists.entities.add                                                       |v1alpha|                                                            |                                       |
|watchlists.entities.batchAdd                                                  |v1alpha|                                                            |                                       |
|watchlists.entities.batchRemove                                               |v1alpha|                                                            |                                       |
|watchlists.entities.remove                                                    |v1alpha|                                                            |                                       |
|watchlists.get                                                                |v1alpha|                                                            |                                       |
|watchlists.list                                                               |v1alpha|                                                            |                                       |
|watchlists.listEntities                                                       |v1alpha|                                                            |                                       |
|watchlists.patch                                                              |v1alpha|                                                            |                                       |
