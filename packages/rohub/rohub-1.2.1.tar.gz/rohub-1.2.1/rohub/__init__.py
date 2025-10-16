# Let users know if they're missing any of our hard dependencies
hard_dependencies = (["requests", "pandas"])
missing_dependencies = []

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append(f"{dependency}: {e}")

if missing_dependencies:
    raise ImportError(
        "Unable to import required dependencies:\n" + "\n".join(missing_dependencies)
    )
del hard_dependencies, dependency, missing_dependencies

# MAIN IMPORTS
from rohub.admin import admin
from rohub.rohub import login
from rohub.rohub import whoami
from rohub.rohub import version
from rohub.rohub import set_retries
from rohub.rohub import set_sleep_time
from rohub.rohub import list_my_ros
from rohub.rohub import is_job_success
from rohub.rohub import show_my_user_profile_details
# ROS MAIN IMPORTS
from rohub.rohub import ros_find
from rohub.rohub import ros_search_using_id
from rohub.rohub import ros_create
from rohub.rohub import ros_load
from rohub.rohub import ros_content
from rohub.rohub import ros_full_metadata
from rohub.rohub import ros_fork
from rohub.rohub import ros_snapshot
from rohub.rohub import ros_archive
from rohub.rohub import ros_list_publications
from rohub.rohub import ros_triple_details
from rohub.rohub import ros_list_annotations
from rohub.rohub import ros_list_triples
from rohub.rohub import ros_list_authors
from rohub.rohub import ros_list_contributors
from rohub.rohub import ros_list_publishers
from rohub.rohub import ros_list_copyright_holders
from rohub.rohub import ros_list_fundings
from rohub.rohub import ros_list_license
from rohub.rohub import ros_export_to_rocrate
from rohub.rohub import ros_list_resources
from rohub.rohub import ros_list_folders
from rohub.rohub import ros_assess_completeness
from rohub.rohub import ros_enrich
from rohub.rohub import ros_list_keywords
from rohub.rohub import ros_list_communities
from rohub.rohub import ros_list_main_entity
from rohub.rohub import ros_list_sketch
from rohub.rohub import ros_read_completeness
from rohub.rohub import ros_read_enrichment
from rohub.rohub import ros_assess_fairness
from rohub.rohub import ros_read_fairness
from rohub.rohub import ros_read_stability
from rohub.rohub import ros_assess_stability
from rohub.rohub import ros_read_extended_analytics
from rohub.rohub import ros_assess_extended_analytics
from rohub.rohub import ros_show_activities
from rohub.rohub import ros_find_using_geoshape
from rohub.rohub import ros_recommend
from rohub.rohub import ros_show_rating
from rohub.rohub import ros_create_permission_link
from rohub.rohub import ros_show_details_using_permission_id
# ROS ADD IMPORTS
from rohub.rohub import ros_add_geolocation
from rohub.rohub import ros_add_folders
from rohub.rohub import ros_add_annotations
from rohub.rohub import ros_add_internal_resource
from rohub.rohub import ros_add_external_resource
from rohub.rohub import ros_add_triple
from rohub.rohub import ros_set_authors
from rohub.rohub import ros_set_contributors
from rohub.rohub import ros_set_publishers
from rohub.rohub import ros_set_copyright_holders
from rohub.rohub import ros_add_funding
from rohub.rohub import ros_set_license
from rohub.rohub import ros_add_keywords
from rohub.rohub import ros_set_keywords
from rohub.rohub import ros_make_golden
from rohub.rohub import ros_aggregate_datacube
from rohub.rohub import ros_add_community
from rohub.rohub import ros_set_community
from rohub.rohub import ros_add_main_entity
from rohub.rohub import ros_add_sketch
# ROS UPLOAD IMPORTS
from rohub.rohub import ros_upload
from rohub.rohub import ros_upload_resources
# ROS DELETE IMPORTS
from rohub.rohub import ros_delete
from rohub.rohub import ros_delete_funding
from rohub.rohub import ros_delete_license
from rohub.rohub import ros_delete_keywords
from rohub.rohub import ros_undo_golden
from rohub.rohub import ros_delete_communities
from rohub.rohub import ros_delete_main_entity
from rohub.rohub import ros_delete_editors
from rohub.rohub import ros_delete_readers
from rohub.rohub import ros_delete_authors
from rohub.rohub import ros_delete_contributors
from rohub.rohub import ros_delete_publishers
from rohub.rohub import ros_delete_copyright_holders
# ROS UPDATE IMPORTS
from rohub.rohub import ros_update
from rohub.rohub import ros_update_funding
# RESOURCE MAIN IMPORTS
from rohub.rohub import resource_find
from rohub.rohub import resource_search_using_id
from rohub.rohub import resource_load
from rohub.rohub import resource_assign_doi
from rohub.rohub import resource_download
from rohub.rohub import resource_set_license
from rohub.rohub import resource_list_license
from rohub.rohub import resource_list_keywords
from rohub.rohub import resource_add_keywords
from rohub.rohub import resource_set_keywords
# RESOURCE DELETE IMPORTS
from rohub.rohub import resource_delete
from rohub.rohub import resource_delete_license
from rohub.rohub import resource_delete_keywords
# RESOURCE UPDATE IMPORTS
from rohub.rohub import resource_update_metadata
from rohub.rohub import resource_update_content
# FOLDER IMPORTS
from rohub.rohub import folder_delete
from rohub.rohub import folder_search_using_id
from rohub.rohub import folder_load
from rohub.rohub import folder_update
# ANNOTATION IMPORTS
from rohub.rohub import annotation_delete
# USERS IMPORTS
from rohub.rohub import users_find
from rohub.rohub import show_user_id
# EXTERNAL USERS IMPORTS
from rohub.rohub import external_user_add
# ORGANIZATIONS IMPORTS
from rohub.rohub import organization_add
from rohub.rohub import organizations_find
# AUXILIARY
from rohub.rohub import zenodo_list_funders
from rohub.rohub import zenodo_list_grants
from rohub.rohub import list_available_licenses
from rohub.rohub import list_valid_research_areas
from rohub.rohub import list_valid_publication_services
from rohub.rohub import list_valid_ros_types
from rohub.rohub import list_valid_templates
from rohub.rohub import list_valid_resource_types
from rohub.rohub import list_valid_creation_modes
from rohub.rohub import list_valid_access_modes
from rohub.rohub import list_triple_object_classes
from rohub.rohub import list_custom_licenses
from rohub.rohub import list_valid_license_status
from rohub.rohub import add_custom_license
from rohub.rohub import show_valid_type_matching_for_ros
from rohub.rohub import list_communities
from rohub.rohub import create_community
from rohub.rohub import adam_platform_metadata_find
from rohub.rohub import list_accepted_dmp_templates
from rohub.rohub import process_dmp_template
from rohub.rohub import show_dmp_mapping
from rohub.rohub import import_dmp
from rohub.rohub import show_relations
from rohub.rohub import ontologies_find
from rohub.rohub import comments_find
from rohub.rohub import comments_create
from rohub.rohub import metadata_flatten
from rohub.rohub import query_sparql_endpoint

__all__ = [
    "login",
    "whoami",
    "version",
    "set_retries",
    "set_sleep_time",
    "list_my_ros",
    "is_job_success",
    "ros_search_using_id",
    "ros_create",
    "ros_load",
    "ros_content",
    "ros_full_metadata",
    "ros_fork",
    "ros_archive",
    "ros_list_publications",
    "ros_add_geolocation",
    "ros_add_folders",
    "ros_add_annotations",
    "ros_add_internal_resource",
    "ros_add_external_resource",
    "ros_upload",
    "ros_upload_resources",
    "ros_delete",
    "folder_delete",
    "annotation_delete",
    "ros_update",
    "ros_add_triple",
    "ros_triple_details",
    "ros_list_annotations",
    "ros_list_triples",
    "ros_export_to_rocrate",
    "ros_set_authors",
    "show_user_id",
    "ros_list_authors",
    "ros_set_contributors",
    "ros_list_contributors",
    "ros_list_copyright_holders",
    "ros_set_copyright_holders",
    "ros_list_fundings",
    "ros_add_funding",
    "zenodo_list_funders",
    "zenodo_list_grants",
    "ros_set_license",
    "list_available_licenses",
    "list_valid_research_areas",
    "list_valid_publication_services",
    "list_valid_ros_types",
    "list_valid_templates",
    "list_valid_resource_types",
    "list_valid_creation_modes",
    "list_valid_access_modes",
    "ros_list_resources",
    "resource_search_using_id",
    "resource_update_metadata",
    "resource_delete",
    "resource_assign_doi",
    "resource_load",
    "list_triple_object_classes",
    "list_custom_licenses",
    "list_valid_license_status",
    "add_custom_license",
    "ros_find",
    "resource_update_content",
    "resource_download",
    "users_find",
    "ros_set_publishers",
    "show_valid_type_matching_for_ros",
    "ros_list_folders",
    "external_user_add",
    "organization_add",
    "organizations_find",
    "ros_delete_funding",
    "ros_update_funding",
    "ros_delete_license",
    "admin",
    "show_my_user_profile_details",
    "resource_set_license",
    "resource_list_license",
    "resource_delete_license",
    "ros_assess_completeness",
    "ros_enrich",
    "ros_list_keywords",
    "ros_add_keywords",
    "ros_delete_keywords",
    "ros_set_keywords",
    "ros_make_golden",
    "ros_undo_golden",
    "ros_snapshot",
    "resource_find",
    "resource_list_keywords",
    "resource_add_keywords",
    "resource_set_keywords",
    "resource_delete_keywords",
    "ros_aggregate_datacube",
    "list_communities",
    "create_community",
    "ros_list_communities",
    "ros_add_community",
    "ros_set_community",
    "ros_delete_communities",
    "ros_list_main_entity",
    "ros_delete_main_entity",
    "ros_add_main_entity",
    "ros_list_sketch",
    "ros_add_sketch",
    "ros_delete_editors",
    "ros_delete_readers",
    "adam_platform_metadata_find",
    "ros_assess_fairness",
    "ros_read_fairness",
    "list_accepted_dmp_templates",
    "process_dmp_template",
    "show_dmp_mapping",
    "import_dmp",
    "ros_read_completeness",
    "ros_read_enrichment",
    "ros_read_stability",
    "ros_assess_stability",
    "ros_read_extended_analytics",
    "ros_assess_extended_analytics",
    "ros_show_activities",
    "show_relations",
    "ros_find_using_geoshape",
    "ros_recommend",
    "ontologies_find",
    "comments_find",
    "comments_create",
    "ros_show_rating",
    "metadata_flatten",
    "folder_search_using_id",
    "folder_load",
    "folder_update",
    "ros_create_permission_link",
    "ros_show_details_using_permission_id",
    "query_sparql_endpoint",
    "ros_delete_authors",
    "ros_delete_contributors",
    "ros_list_publishers",
    "ros_delete_publishers",
    "ros_delete_copyright_holders",
]
