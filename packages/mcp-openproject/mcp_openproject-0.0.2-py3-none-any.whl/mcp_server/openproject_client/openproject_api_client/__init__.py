# coding: utf-8

# flake8: noqa

"""
    OpenProject API V3 (Stable)

    You're looking at the current **stable** documentation of the OpenProject APIv3. If you're interested in the current development version, please go to [github.com/opf](https://github.com/opf/openproject/tree/dev/docs/api/apiv3).  ## Introduction  The documentation for the APIv3 is written according to the [OpenAPI 3.1 Specification](https://swagger.io/specification/). You can either view the static version of this documentation on the [website](https://www.openproject.org/docs/api/introduction/) or the interactive version, rendered with [OpenAPI Explorer](https://github.com/Rhosys/openapi-explorer/blob/main/README.md), in your OpenProject installation under `/api/docs`. In the latter you can try out the various API endpoints directly interacting with our OpenProject data. Moreover you can access the specification source itself under `/api/v3/spec.json` and `/api/v3/spec.yml` (e.g. [here](https://community.openproject.org/api/v3/spec.yml)).  The APIv3 is a hypermedia REST API, a shorthand for \"Hypermedia As The Engine Of Application State\" (HATEOAS). This means that each endpoint of this API will have links to other resources or actions defined in the resulting body.  These related resources and actions for any given resource will be context sensitive. For example, only actions that the authenticated user can take are being rendered. This can be used to dynamically identify actions that the user might take for any given response.  As an example, if you fetch a work package through the [Work Package endpoint](https://www.openproject.org/docs/api/endpoints/work-packages/), the `update` link will only be present when the user you authenticated has been granted a permission to update the work package in the assigned project.  ## HAL+JSON  HAL is a simple format that gives a consistent and easy way to hyperlink between resources in your API. Read more in the following specification: [https://tools.ietf.org/html/draft-kelly-json-hal-08](https://tools.ietf.org/html/draft-kelly-json-hal-08)  **OpenProject API implementation of HAL+JSON format** enriches JSON and introduces a few meta properties:  - `_type` - specifies the type of the resource (e.g.: WorkPackage, Project) - `_links` - contains all related resource and action links available for the resource - `_embedded` - contains all embedded objects  HAL does not guarantee that embedded resources are embedded in their full representation, they might as well be partially represented (e.g. some properties can be left out). However in this API you have the guarantee that whenever a resource is **embedded**, it is embedded in its **full representation**.  ## API response structure  All API responses contain a single HAL+JSON object, even collections of objects are technically represented by a single HAL+JSON object that itself contains its members. More details on collections can be found in the [Collections Section](https://www.openproject.org/docs/api/collections/).  ## Authentication  The API supports the following authentication schemes: OAuth2, session based authentication, and basic auth.  Depending on the settings of the OpenProject instance many resources can be accessed without being authenticated. In case the instance requires authentication on all requests the client will receive an **HTTP 401** status code in response to any request.  Otherwise unauthenticated clients have all the permissions of the anonymous user.  ### Session-based Authentication  This means you have to login to OpenProject via the Web-Interface to be authenticated in the API. This method is well-suited for clients acting within the browser, like the Angular-Client built into OpenProject.  In this case, you always need to pass the HTTP header `X-Requested-With \"XMLHttpRequest\"` for authentication.  ### API Key through Basic Auth  Users can authenticate towards the API v3 using basic auth with the user name `apikey` (NOT your login) and the API key as the password. Users can find their API key on their account page.  Example:  ```shell API_KEY=2519132cdf62dcf5a66fd96394672079f9e9cad1 curl -u apikey:$API_KEY https://community.openproject.org/api/v3/users/42 ```  ### OAuth2.0 authentication  OpenProject allows authentication and authorization with OAuth2 with *Authorization code flow*, as well as *Client credentials* operation modes.  To get started, you first need to register an application in the OpenProject OAuth administration section of your installation. This will save an entry for your application with a client unique identifier (`client_id`) and an accompanying secret key (`client_secret`).  You can then use one the following guides to perform the supported OAuth 2.0 flows:  - [Authorization code flow](https://oauth.net/2/grant-types/authorization-code)  - [Authorization code flow with PKCE](https://doorkeeper.gitbook.io/guides/ruby-on-rails/pkce-flow), recommended for clients unable to keep the client_secret confidential  - [Client credentials](https://oauth.net/2/grant-types/client-credentials/) - Requires an application to be bound to an impersonating user for non-public access  ### OIDC provider generated JWT as a Bearer token  There is a possibility to use JSON Web Tokens (JWT) generated by an OIDC provider configured in OpenProject as a bearer token to do authenticated requests against the API. The following requirements must be met:  - OIDC provider must be configured in OpenProject with **jwks_uri** - JWT must be signed using RSA algorithm - JWT **iss** claim must be equal to OIDC provider **issuer** - JWT **aud** claim must contain the OpenProject **client ID** used at the OIDC provider - JWT **scope** claim must include a valid scope to access the desired API (e.g. `api_v3` for APIv3) - JWT must be actual (neither expired or too early to be used) - JWT must be passed in Authorization header like: `Authorization: Bearer {jwt}` - User from **sub** claim must be logged in OpenProject before otherwise it will be not authenticated  In more general terms, OpenProject should be compliant to [RFC 9068](https://www.rfc-editor.org/rfc/rfc9068) when validating access tokens.  ### Why not username and password?  The simplest way to do basic auth would be to use a user's username and password naturally. However, OpenProject already has supported API keys in the past for the API v2, though not through basic auth.  Using **username and password** directly would have some advantages:  * It is intuitive for the user who then just has to provide those just as they would when logging into OpenProject.  * No extra logic for token management necessary.  On the other hand using **API keys** has some advantages too, which is why we went for that:  * If compromised while saved on an insecure client the user only has to regenerate the API key instead of changing their password, too.  * They are naturally long and random which makes them invulnerable to dictionary attacks and harder to crack in general.  Most importantly users may not actually have a password to begin with. Specifically when they have registered through an OpenID Connect provider.  ## Cross-Origin Resource Sharing (CORS)  By default, the OpenProject API is _not_ responding with any CORS headers. If you want to allow cross-domain AJAX calls against your OpenProject instance, you need to enable CORS headers being returned.  Please see [our API settings documentation](https://www.openproject.org/docs/system-admin-guide/api-and-webhooks/) on how to selectively enable CORS.  ## Allowed HTTP methods  - `GET` - Get a single resource or collection of resources  - `POST` - Create a new resource or perform  - `PATCH` - Update a resource  - `DELETE` - Delete a resource  ## Compression  Responses are compressed if requested by the client. Currently [gzip](https://www.gzip.org/) and [deflate](https://tools.ietf.org/html/rfc1951) are supported. The client signals the desired compression by setting the [`Accept-Encoding` header](https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.3). If no `Accept-Encoding` header is send, `Accept-Encoding: identity` is assumed which will result in the API responding uncompressed.

    The version of the OpenAPI document: 3
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


__version__ = "1.0.0"

# Define package exports
__all__ = [
    "ActionsCapabilitiesApi",
    "ActivitiesApi",
    "AttachmentsApi",
    "BudgetsApi",
    "CategoriesApi",
    "CollectionsApi",
    "ConfigurationApi",
    "CustomOptionsApi",
    "CustomActionsApi",
    "DocumentsApi",
    "EmojiReactionsApi",
    "FavoritesApi",
    "FileLinksApi",
    "FileLinksApi",
    "FormsApi",
    "GridsApi",
    "GroupsApi",
    "HelpTextsApi",
    "MeetingsApi",
    "MembershipsApi",
    "NewsApi",
    "NotificationsApi",
    "OAuth2Api",
    "PostsApi",
    "PreviewingApi",
    "PrincipalsApi",
    "PrioritiesApi",
    "ProjectPhaseDefinitionsApi",
    "ProjectPhasesApi",
    "ProjectsApi",
    "QueriesApi",
    "QueryColumnsApi",
    "QueryFilterInstanceSchemaApi",
    "QueryFiltersApi",
    "QueryOperatorsApi",
    "QuerySortBysApi",
    "RelationsApi",
    "RemindersApi",
    "RevisionsApi",
    "RolesApi",
    "RootApi",
    "SchemasApi",
    "StatusesApi",
    "TimeEntriesApi",
    "TimeEntriesApi",
    "TimeEntryActivitiesApi",
    "TypesApi",
    "UserPreferencesApi",
    "UsersApi",
    "ValuesPropertyApi",
    "VersionsApi",
    "ViewsApi",
    "WikiPagesApi",
    "WorkPackagesApi",
    "WorkPackagesApi",
    "WorkScheduleApi",
    "DefaultApi",
    "ApiResponse",
    "ApiClient",
    "Configuration",
    "OpenApiException",
    "ApiTypeError",
    "ApiValueError",
    "ApiKeyError",
    "ApiAttributeError",
    "ApiException",
    "ActivityCommentWriteModel",
    "ActivityCommentWriteModelComment",
    "ActivityModel",
    "ActivityModelEmbedded",
    "ActivityModelLinks",
    "AddWatcherRequest",
    "AttachmentModel",
    "AttachmentModelLinks",
    "AttachmentsModel",
    "AttachmentsModelAllOfEmbedded",
    "AttachmentsModelAllOfEmbeddedElements",
    "AttachmentsModelAllOfLinks",
    "AvailableAssigneesModel",
    "AvailableAssigneesModelAllOfEmbedded",
    "AvailableAssigneesModelAllOfEmbeddedElements",
    "AvailableAssigneesModelAllOfLinks",
    "BudgetModel",
    "BudgetModelLinks",
    "CategoriesByProjectModel",
    "CategoriesByProjectModelAllOfEmbedded",
    "CategoriesByProjectModelAllOfEmbeddedElements",
    "CategoriesByProjectModelAllOfLinks",
    "CategoryModel",
    "CategoryModelLinks",
    "CollectionLinks",
    "CollectionModel",
    "ConfigurationModel",
    "CreateViewsRequest",
    "CreateViewsRequestLinks",
    "CreateViewsRequestLinksQuery",
    "CreateWorkPackageReminderRequest",
    "CustomActionModel",
    "CustomActionModelLinks",
    "CustomOptionModel",
    "CustomOptionModelLinks",
    "DayCollectionModel",
    "DayCollectionModelAllOfEmbedded",
    "DayCollectionModelAllOfLinks",
    "DayModel",
    "DayModelLinks",
    "DocumentModel",
    "DocumentModelLinks",
    "EmojiReactionModel",
    "EmojiReactionModelLinks",
    "EmojiReactionsModel",
    "EmojiReactionsModelEmbedded",
    "EmojiReactionsModelLinks",
    "ErrorResponse",
    "ErrorResponseEmbedded",
    "ErrorResponseEmbeddedDetails",
    "ExecuteCustomActionRequest",
    "ExecuteCustomActionRequestLinks",
    "ExecuteCustomActionRequestLinksWorkPackage",
    "FileLinkCollectionReadModel",
    "FileLinkCollectionReadModelAllOfEmbedded",
    "FileLinkCollectionReadModelAllOfLinks",
    "FileLinkCollectionWriteModel",
    "FileLinkCollectionWriteModelAllOfEmbedded",
    "FileLinkOriginDataModel",
    "FileLinkReadModel",
    "FileLinkReadModelEmbedded",
    "FileLinkReadModelLinks",
    "FileLinkWriteModel",
    "FileLinkWriteModelLinks",
    "FileLinkWriteModelLinksOneOf",
    "FileLinkWriteModelLinksOneOf1",
    "FileUploadFormMetadata",
    "Formattable",
    "GridCollectionModel",
    "GridCollectionModelAllOfEmbedded",
    "GridReadModel",
    "GridReadModelLinks",
    "GridWidgetModel",
    "GridWriteModel",
    "GridWriteModelLinks",
    "GroupCollectionModel",
    "GroupCollectionModelAllOfEmbedded",
    "GroupCollectionModelAllOfLinks",
    "GroupModel",
    "GroupModelAllOfEmbedded",
    "GroupModelAllOfLinks",
    "GroupModelAllOfLinksMembers",
    "GroupWriteModel",
    "GroupWriteModelLinks",
    "HelpTextCollectionModel",
    "HelpTextCollectionModelAllOfEmbedded",
    "HelpTextCollectionModelAllOfLinks",
    "HelpTextModel",
    "HelpTextModelLinks",
    "HierarchyItemCollectionModel",
    "HierarchyItemCollectionModelAllOfEmbedded",
    "HierarchyItemCollectionModelAllOfLinks",
    "HierarchyItemReadModel",
    "HierarchyItemReadModelLinks",
    "Link",
    "ListAvailableParentProjectCandidatesModel",
    "ListAvailableParentProjectCandidatesModelAllOfEmbedded",
    "ListAvailableParentProjectCandidatesModelAllOfEmbeddedElements",
    "ListAvailableParentProjectCandidatesModelAllOfLinks",
    "ListReminders200Response",
    "ListReminders200ResponseEmbedded",
    "MeetingModel",
    "MeetingModelLinks",
    "MembershipCollectionModel",
    "MembershipCollectionModelAllOfEmbedded",
    "MembershipFormModel",
    "MembershipFormModelEmbedded",
    "MembershipFormModelEmbeddedValidationError",
    "MembershipFormModelLinks",
    "MembershipReadModel",
    "MembershipReadModelEmbedded",
    "MembershipReadModelEmbeddedPrincipal",
    "MembershipReadModelLinks",
    "MembershipSchemaModel",
    "MembershipWriteModel",
    "MembershipWriteModelLinks",
    "MembershipWriteModelMeta",
    "NewsCreateModel",
    "NewsCreateModelLinks",
    "NewsModel",
    "NewsModelLinks",
    "NonWorkingDayCollectionModel",
    "NonWorkingDayCollectionModelAllOfEmbedded",
    "NonWorkingDayCollectionModelAllOfLinks",
    "NonWorkingDayModel",
    "NonWorkingDayModelLinks",
    "NotificationCollectionModel",
    "NotificationCollectionModelAllOfEmbedded",
    "NotificationCollectionModelAllOfLinks",
    "NotificationModel",
    "NotificationModelEmbedded",
    "NotificationModelLinks",
    "OAuthApplicationReadModel",
    "OAuthApplicationReadModelLinks",
    "OAuthClientCredentialsReadModel",
    "OAuthClientCredentialsReadModelLinks",
    "OAuthClientCredentialsWriteModel",
    "OffsetPaginatedCollectionLinks",
    "OffsetPaginatedCollectionModel",
    "PaginatedCollectionModel",
    "PaginatedCollectionModelAllOfLinks",
    "PlaceholderUserCollectionModel",
    "PlaceholderUserCollectionModelAllOfEmbedded",
    "PlaceholderUserCollectionModelAllOfLinks",
    "PlaceholderUserCreateModel",
    "PlaceholderUserModel",
    "PlaceholderUserModelAllOfLinks",
    "PostModel",
    "PostModelLinks",
    "PrincipalCollectionModel",
    "PrincipalCollectionModelAllOfEmbedded",
    "PrincipalCollectionModelAllOfEmbeddedElements",
    "PrincipalModel",
    "PrincipalModelLinks",
    "PriorityCollectionModel",
    "PriorityCollectionModelAllOfEmbedded",
    "PriorityCollectionModelAllOfLinks",
    "PriorityCollectionModelAllOfLinksSelf",
    "PriorityModel",
    "PriorityModelLinks",
    "ProjectCollectionModel",
    "ProjectCollectionModelAllOfEmbedded",
    "ProjectCollectionModelAllOfLinks",
    "ProjectModel",
    "ProjectModelLinks",
    "ProjectPhaseDefinitionCollectionModel",
    "ProjectPhaseDefinitionCollectionModelAllOfEmbedded",
    "ProjectPhaseDefinitionCollectionModelAllOfLinks",
    "ProjectPhaseDefinitionModel",
    "ProjectPhaseDefinitionModelLinks",
    "ProjectPhaseModel",
    "ProjectPhaseModelLinks",
    "ProjectStorageCollectionModel",
    "ProjectStorageCollectionModelAllOfEmbedded",
    "ProjectStorageCollectionModelAllOfLinks",
    "ProjectStorageModel",
    "ProjectStorageModelLinks",
    "ProjectsSchemaModel",
    "ProjectsSchemaModelAttributeGroupsInner",
    "ProjectsSchemaModelLinks",
    "ProjectsSchemaModelLinksSelf",
    "QueryColumnModel",
    "QueryCreateForm",
    "QueryFilterInstanceSchemaModel",
    "QueryFilterInstanceSchemaModelLinks",
    "QueryFilterModel",
    "QueryModel",
    "QueryModelLinks",
    "QueryOperatorModel",
    "QuerySortByModel",
    "QueryUpdateForm",
    "RelationCollectionModel",
    "RelationCollectionModelAllOfEmbedded",
    "RelationCollectionModelAllOfLinks",
    "RelationReadModel",
    "RelationReadModelEmbedded",
    "RelationReadModelLinks",
    "RelationWriteModel",
    "RelationWriteModelLinks",
    "ReminderModel",
    "ReminderModelLinks",
    "RevisionModel",
    "RevisionModelLinks",
    "RoleModel",
    "RoleModelLinks",
    "RootModel",
    "RootModelLinks",
    "SchemaModel",
    "SchemaModelLinks",
    "SchemaPropertyModel",
    "ShowOrValidateFormRequest",
    "StatusCollectionModel",
    "StatusCollectionModelAllOfEmbedded",
    "StatusModel",
    "StatusModelLinks",
    "StorageCollectionModel",
    "StorageCollectionModelAllOfEmbedded",
    "StorageCollectionModelAllOfLinks",
    "StorageFileModel",
    "StorageFileModelAllOfLinks",
    "StorageFileUploadLinkModel",
    "StorageFileUploadLinkModelLinks",
    "StorageFileUploadPreparationModel",
    "StorageFilesModel",
    "StorageFolderWriteModel",
    "StorageReadModel",
    "StorageReadModelEmbedded",
    "StorageReadModelLinks",
    "StorageWriteModel",
    "StorageWriteModelLinks",
    "TimeEntryActivityModel",
    "TimeEntryActivityModelEmbedded",
    "TimeEntryActivityModelLinks",
    "TimeEntryCollectionModel",
    "TimeEntryCollectionModelAllOfEmbedded",
    "TimeEntryCollectionModelAllOfLinks",
    "TimeEntryModel",
    "TimeEntryModelLinks",
    "ToggleActivityEmojiReactionRequest",
    "TypeModel",
    "TypeModelLinks",
    "TypesByProjectModel",
    "TypesByProjectModelAllOfEmbedded",
    "TypesByProjectModelAllOfEmbeddedElements",
    "TypesByProjectModelAllOfLinks",
    "UpdateReminderRequest",
    "UpdateUserPreferencesRequest",
    "UserCollectionModel",
    "UserCollectionModelAllOfEmbedded",
    "UserCollectionModelAllOfLinks",
    "UserCreateModel",
    "UserModel",
    "UserModelAllOfLinks",
    "ValuesPropertyModel",
    "ValuesPropertyModelLinks",
    "VersionModel",
    "VersionModelLinks",
    "VersionsByProjectModel",
    "VersionsByProjectModelAllOfEmbedded",
    "VersionsByProjectModelAllOfEmbeddedElements",
    "VersionsByProjectModelAllOfLinks",
    "WatchersModel",
    "WatchersModelAllOfEmbedded",
    "WatchersModelAllOfEmbeddedElements",
    "WatchersModelAllOfLinks",
    "WeekDayCollectionModel",
    "WeekDayCollectionModelAllOfEmbedded",
    "WeekDayCollectionModelAllOfLinks",
    "WeekDayCollectionWriteModel",
    "WeekDayCollectionWriteModelEmbedded",
    "WeekDayCollectionWriteModelEmbeddedElementsInner",
    "WeekDayModel",
    "WeekDaySelfLinkModel",
    "WeekDayWriteModel",
    "WikiPageModel",
    "WikiPageModelLinks",
    "WorkPackageFormModel",
    "WorkPackageFormModelEmbedded",
    "WorkPackageFormModelLinks",
    "WorkPackageModel",
    "WorkPackageModelLinks",
    "WorkPackagePatchModel",
    "WorkPackageSchemaModel",
    "WorkPackageSchemaModelLinks",
    "WorkPackageWriteModel",
    "WorkPackageWriteModelLinks",
    "WorkPackagesModel",
    "WorkPackagesModelAllOfEmbedded",
    "WorkPackagesModelAllOfLinks",
]

# import apis into sdk package
from openproject_api_client.api.actions_capabilities_api import ActionsCapabilitiesApi as ActionsCapabilitiesApi
from openproject_api_client.api.activities_api import ActivitiesApi as ActivitiesApi
from openproject_api_client.api.attachments_api import AttachmentsApi as AttachmentsApi
from openproject_api_client.api.budgets_api import BudgetsApi as BudgetsApi
from openproject_api_client.api.categories_api import CategoriesApi as CategoriesApi
from openproject_api_client.api.collections_api import CollectionsApi as CollectionsApi
from openproject_api_client.api.configuration_api import ConfigurationApi as ConfigurationApi
from openproject_api_client.api.custom_options_api import CustomOptionsApi as CustomOptionsApi
from openproject_api_client.api.custom_actions_api import CustomActionsApi as CustomActionsApi
from openproject_api_client.api.documents_api import DocumentsApi as DocumentsApi
from openproject_api_client.api.emoji_reactions_api import EmojiReactionsApi as EmojiReactionsApi
from openproject_api_client.api.favorites_api import FavoritesApi as FavoritesApi
from openproject_api_client.api.file_links_api import FileLinksApi as FileLinksApi
from openproject_api_client.api.file_links_api import FileLinksApi as FileLinksApi
from openproject_api_client.api.forms_api import FormsApi as FormsApi
from openproject_api_client.api.grids_api import GridsApi as GridsApi
from openproject_api_client.api.groups_api import GroupsApi as GroupsApi
from openproject_api_client.api.help_texts_api import HelpTextsApi as HelpTextsApi
from openproject_api_client.api.meetings_api import MeetingsApi as MeetingsApi
from openproject_api_client.api.memberships_api import MembershipsApi as MembershipsApi
from openproject_api_client.api.news_api import NewsApi as NewsApi
from openproject_api_client.api.notifications_api import NotificationsApi as NotificationsApi
from openproject_api_client.api.o_auth2_api import OAuth2Api as OAuth2Api
from openproject_api_client.api.posts_api import PostsApi as PostsApi
from openproject_api_client.api.previewing_api import PreviewingApi as PreviewingApi
from openproject_api_client.api.principals_api import PrincipalsApi as PrincipalsApi
from openproject_api_client.api.priorities_api import PrioritiesApi as PrioritiesApi
from openproject_api_client.api.project_phase_definitions_api import ProjectPhaseDefinitionsApi as ProjectPhaseDefinitionsApi
from openproject_api_client.api.project_phases_api import ProjectPhasesApi as ProjectPhasesApi
from openproject_api_client.api.projects_api import ProjectsApi as ProjectsApi
from openproject_api_client.api.queries_api import QueriesApi as QueriesApi
from openproject_api_client.api.query_columns_api import QueryColumnsApi as QueryColumnsApi
from openproject_api_client.api.query_filter_instance_schema_api import QueryFilterInstanceSchemaApi as QueryFilterInstanceSchemaApi
from openproject_api_client.api.query_filters_api import QueryFiltersApi as QueryFiltersApi
from openproject_api_client.api.query_operators_api import QueryOperatorsApi as QueryOperatorsApi
from openproject_api_client.api.query_sort_bys_api import QuerySortBysApi as QuerySortBysApi
from openproject_api_client.api.relations_api import RelationsApi as RelationsApi
from openproject_api_client.api.reminders_api import RemindersApi as RemindersApi
from openproject_api_client.api.revisions_api import RevisionsApi as RevisionsApi
from openproject_api_client.api.roles_api import RolesApi as RolesApi
from openproject_api_client.api.root_api import RootApi as RootApi
from openproject_api_client.api.schemas_api import SchemasApi as SchemasApi
from openproject_api_client.api.statuses_api import StatusesApi as StatusesApi
from openproject_api_client.api.time_entries_api import TimeEntriesApi as TimeEntriesApi
from openproject_api_client.api.time_entries_api import TimeEntriesApi as TimeEntriesApi
from openproject_api_client.api.time_entry_activities_api import TimeEntryActivitiesApi as TimeEntryActivitiesApi
from openproject_api_client.api.types_api import TypesApi as TypesApi
from openproject_api_client.api.user_preferences_api import UserPreferencesApi as UserPreferencesApi
from openproject_api_client.api.users_api import UsersApi as UsersApi
from openproject_api_client.api.values_property_api import ValuesPropertyApi as ValuesPropertyApi
from openproject_api_client.api.versions_api import VersionsApi as VersionsApi
from openproject_api_client.api.views_api import ViewsApi as ViewsApi
from openproject_api_client.api.wiki_pages_api import WikiPagesApi as WikiPagesApi
from openproject_api_client.api.work_packages_api import WorkPackagesApi as WorkPackagesApi
from openproject_api_client.api.work_packages_api import WorkPackagesApi as WorkPackagesApi
from openproject_api_client.api.work_schedule_api import WorkScheduleApi as WorkScheduleApi
from openproject_api_client.api.default_api import DefaultApi as DefaultApi

# import ApiClient
from openproject_api_client.api_response import ApiResponse as ApiResponse
from openproject_api_client.api_client import ApiClient as ApiClient
from openproject_api_client.configuration import Configuration as Configuration
from openproject_api_client.exceptions import OpenApiException as OpenApiException
from openproject_api_client.exceptions import ApiTypeError as ApiTypeError
from openproject_api_client.exceptions import ApiValueError as ApiValueError
from openproject_api_client.exceptions import ApiKeyError as ApiKeyError
from openproject_api_client.exceptions import ApiAttributeError as ApiAttributeError
from openproject_api_client.exceptions import ApiException as ApiException

# import models into sdk package
from openproject_api_client.models.activity_comment_write_model import ActivityCommentWriteModel as ActivityCommentWriteModel
from openproject_api_client.models.activity_comment_write_model_comment import ActivityCommentWriteModelComment as ActivityCommentWriteModelComment
from openproject_api_client.models.activity_model import ActivityModel as ActivityModel
from openproject_api_client.models.activity_model_embedded import ActivityModelEmbedded as ActivityModelEmbedded
from openproject_api_client.models.activity_model_links import ActivityModelLinks as ActivityModelLinks
from openproject_api_client.models.add_watcher_request import AddWatcherRequest as AddWatcherRequest
from openproject_api_client.models.attachment_model import AttachmentModel as AttachmentModel
from openproject_api_client.models.attachment_model_links import AttachmentModelLinks as AttachmentModelLinks
from openproject_api_client.models.attachments_model import AttachmentsModel as AttachmentsModel
from openproject_api_client.models.attachments_model_all_of_embedded import AttachmentsModelAllOfEmbedded as AttachmentsModelAllOfEmbedded
from openproject_api_client.models.attachments_model_all_of_embedded_elements import AttachmentsModelAllOfEmbeddedElements as AttachmentsModelAllOfEmbeddedElements
from openproject_api_client.models.attachments_model_all_of_links import AttachmentsModelAllOfLinks as AttachmentsModelAllOfLinks
from openproject_api_client.models.available_assignees_model import AvailableAssigneesModel as AvailableAssigneesModel
from openproject_api_client.models.available_assignees_model_all_of_embedded import AvailableAssigneesModelAllOfEmbedded as AvailableAssigneesModelAllOfEmbedded
from openproject_api_client.models.available_assignees_model_all_of_embedded_elements import AvailableAssigneesModelAllOfEmbeddedElements as AvailableAssigneesModelAllOfEmbeddedElements
from openproject_api_client.models.available_assignees_model_all_of_links import AvailableAssigneesModelAllOfLinks as AvailableAssigneesModelAllOfLinks
from openproject_api_client.models.budget_model import BudgetModel as BudgetModel
from openproject_api_client.models.budget_model_links import BudgetModelLinks as BudgetModelLinks
from openproject_api_client.models.categories_by_project_model import CategoriesByProjectModel as CategoriesByProjectModel
from openproject_api_client.models.categories_by_project_model_all_of_embedded import CategoriesByProjectModelAllOfEmbedded as CategoriesByProjectModelAllOfEmbedded
from openproject_api_client.models.categories_by_project_model_all_of_embedded_elements import CategoriesByProjectModelAllOfEmbeddedElements as CategoriesByProjectModelAllOfEmbeddedElements
from openproject_api_client.models.categories_by_project_model_all_of_links import CategoriesByProjectModelAllOfLinks as CategoriesByProjectModelAllOfLinks
from openproject_api_client.models.category_model import CategoryModel as CategoryModel
from openproject_api_client.models.category_model_links import CategoryModelLinks as CategoryModelLinks
from openproject_api_client.models.collection_links import CollectionLinks as CollectionLinks
from openproject_api_client.models.collection_model import CollectionModel as CollectionModel
from openproject_api_client.models.configuration_model import ConfigurationModel as ConfigurationModel
from openproject_api_client.models.create_views_request import CreateViewsRequest as CreateViewsRequest
from openproject_api_client.models.create_views_request_links import CreateViewsRequestLinks as CreateViewsRequestLinks
from openproject_api_client.models.create_views_request_links_query import CreateViewsRequestLinksQuery as CreateViewsRequestLinksQuery
from openproject_api_client.models.create_work_package_reminder_request import CreateWorkPackageReminderRequest as CreateWorkPackageReminderRequest
from openproject_api_client.models.custom_action_model import CustomActionModel as CustomActionModel
from openproject_api_client.models.custom_action_model_links import CustomActionModelLinks as CustomActionModelLinks
from openproject_api_client.models.custom_option_model import CustomOptionModel as CustomOptionModel
from openproject_api_client.models.custom_option_model_links import CustomOptionModelLinks as CustomOptionModelLinks
from openproject_api_client.models.day_collection_model import DayCollectionModel as DayCollectionModel
from openproject_api_client.models.day_collection_model_all_of_embedded import DayCollectionModelAllOfEmbedded as DayCollectionModelAllOfEmbedded
from openproject_api_client.models.day_collection_model_all_of_links import DayCollectionModelAllOfLinks as DayCollectionModelAllOfLinks
from openproject_api_client.models.day_model import DayModel as DayModel
from openproject_api_client.models.day_model_links import DayModelLinks as DayModelLinks
from openproject_api_client.models.document_model import DocumentModel as DocumentModel
from openproject_api_client.models.document_model_links import DocumentModelLinks as DocumentModelLinks
from openproject_api_client.models.emoji_reaction_model import EmojiReactionModel as EmojiReactionModel
from openproject_api_client.models.emoji_reaction_model_links import EmojiReactionModelLinks as EmojiReactionModelLinks
from openproject_api_client.models.emoji_reactions_model import EmojiReactionsModel as EmojiReactionsModel
from openproject_api_client.models.emoji_reactions_model_embedded import EmojiReactionsModelEmbedded as EmojiReactionsModelEmbedded
from openproject_api_client.models.emoji_reactions_model_links import EmojiReactionsModelLinks as EmojiReactionsModelLinks
from openproject_api_client.models.error_response import ErrorResponse as ErrorResponse
from openproject_api_client.models.error_response_embedded import ErrorResponseEmbedded as ErrorResponseEmbedded
from openproject_api_client.models.error_response_embedded_details import ErrorResponseEmbeddedDetails as ErrorResponseEmbeddedDetails
from openproject_api_client.models.execute_custom_action_request import ExecuteCustomActionRequest as ExecuteCustomActionRequest
from openproject_api_client.models.execute_custom_action_request_links import ExecuteCustomActionRequestLinks as ExecuteCustomActionRequestLinks
from openproject_api_client.models.execute_custom_action_request_links_work_package import ExecuteCustomActionRequestLinksWorkPackage as ExecuteCustomActionRequestLinksWorkPackage
from openproject_api_client.models.file_link_collection_read_model import FileLinkCollectionReadModel as FileLinkCollectionReadModel
from openproject_api_client.models.file_link_collection_read_model_all_of_embedded import FileLinkCollectionReadModelAllOfEmbedded as FileLinkCollectionReadModelAllOfEmbedded
from openproject_api_client.models.file_link_collection_read_model_all_of_links import FileLinkCollectionReadModelAllOfLinks as FileLinkCollectionReadModelAllOfLinks
from openproject_api_client.models.file_link_collection_write_model import FileLinkCollectionWriteModel as FileLinkCollectionWriteModel
from openproject_api_client.models.file_link_collection_write_model_all_of_embedded import FileLinkCollectionWriteModelAllOfEmbedded as FileLinkCollectionWriteModelAllOfEmbedded
from openproject_api_client.models.file_link_origin_data_model import FileLinkOriginDataModel as FileLinkOriginDataModel
from openproject_api_client.models.file_link_read_model import FileLinkReadModel as FileLinkReadModel
from openproject_api_client.models.file_link_read_model_embedded import FileLinkReadModelEmbedded as FileLinkReadModelEmbedded
from openproject_api_client.models.file_link_read_model_links import FileLinkReadModelLinks as FileLinkReadModelLinks
from openproject_api_client.models.file_link_write_model import FileLinkWriteModel as FileLinkWriteModel
from openproject_api_client.models.file_link_write_model_links import FileLinkWriteModelLinks as FileLinkWriteModelLinks
from openproject_api_client.models.file_link_write_model_links_one_of import FileLinkWriteModelLinksOneOf as FileLinkWriteModelLinksOneOf
from openproject_api_client.models.file_link_write_model_links_one_of1 import FileLinkWriteModelLinksOneOf1 as FileLinkWriteModelLinksOneOf1
from openproject_api_client.models.file_upload_form_metadata import FileUploadFormMetadata as FileUploadFormMetadata
from openproject_api_client.models.formattable import Formattable as Formattable
from openproject_api_client.models.grid_collection_model import GridCollectionModel as GridCollectionModel
from openproject_api_client.models.grid_collection_model_all_of_embedded import GridCollectionModelAllOfEmbedded as GridCollectionModelAllOfEmbedded
from openproject_api_client.models.grid_read_model import GridReadModel as GridReadModel
from openproject_api_client.models.grid_read_model_links import GridReadModelLinks as GridReadModelLinks
from openproject_api_client.models.grid_widget_model import GridWidgetModel as GridWidgetModel
from openproject_api_client.models.grid_write_model import GridWriteModel as GridWriteModel
from openproject_api_client.models.grid_write_model_links import GridWriteModelLinks as GridWriteModelLinks
from openproject_api_client.models.group_collection_model import GroupCollectionModel as GroupCollectionModel
from openproject_api_client.models.group_collection_model_all_of_embedded import GroupCollectionModelAllOfEmbedded as GroupCollectionModelAllOfEmbedded
from openproject_api_client.models.group_collection_model_all_of_links import GroupCollectionModelAllOfLinks as GroupCollectionModelAllOfLinks
from openproject_api_client.models.group_model import GroupModel as GroupModel
from openproject_api_client.models.group_model_all_of_embedded import GroupModelAllOfEmbedded as GroupModelAllOfEmbedded
from openproject_api_client.models.group_model_all_of_links import GroupModelAllOfLinks as GroupModelAllOfLinks
from openproject_api_client.models.group_model_all_of_links_members import GroupModelAllOfLinksMembers as GroupModelAllOfLinksMembers
from openproject_api_client.models.group_write_model import GroupWriteModel as GroupWriteModel
from openproject_api_client.models.group_write_model_links import GroupWriteModelLinks as GroupWriteModelLinks
from openproject_api_client.models.help_text_collection_model import HelpTextCollectionModel as HelpTextCollectionModel
from openproject_api_client.models.help_text_collection_model_all_of_embedded import HelpTextCollectionModelAllOfEmbedded as HelpTextCollectionModelAllOfEmbedded
from openproject_api_client.models.help_text_collection_model_all_of_links import HelpTextCollectionModelAllOfLinks as HelpTextCollectionModelAllOfLinks
from openproject_api_client.models.help_text_model import HelpTextModel as HelpTextModel
from openproject_api_client.models.help_text_model_links import HelpTextModelLinks as HelpTextModelLinks
from openproject_api_client.models.hierarchy_item_collection_model import HierarchyItemCollectionModel as HierarchyItemCollectionModel
from openproject_api_client.models.hierarchy_item_collection_model_all_of_embedded import HierarchyItemCollectionModelAllOfEmbedded as HierarchyItemCollectionModelAllOfEmbedded
from openproject_api_client.models.hierarchy_item_collection_model_all_of_links import HierarchyItemCollectionModelAllOfLinks as HierarchyItemCollectionModelAllOfLinks
from openproject_api_client.models.hierarchy_item_read_model import HierarchyItemReadModel as HierarchyItemReadModel
from openproject_api_client.models.hierarchy_item_read_model_links import HierarchyItemReadModelLinks as HierarchyItemReadModelLinks
from openproject_api_client.models.link import Link as Link
from openproject_api_client.models.list_available_parent_project_candidates_model import ListAvailableParentProjectCandidatesModel as ListAvailableParentProjectCandidatesModel
from openproject_api_client.models.list_available_parent_project_candidates_model_all_of_embedded import ListAvailableParentProjectCandidatesModelAllOfEmbedded as ListAvailableParentProjectCandidatesModelAllOfEmbedded
from openproject_api_client.models.list_available_parent_project_candidates_model_all_of_embedded_elements import ListAvailableParentProjectCandidatesModelAllOfEmbeddedElements as ListAvailableParentProjectCandidatesModelAllOfEmbeddedElements
from openproject_api_client.models.list_available_parent_project_candidates_model_all_of_links import ListAvailableParentProjectCandidatesModelAllOfLinks as ListAvailableParentProjectCandidatesModelAllOfLinks
from openproject_api_client.models.list_reminders200_response import ListReminders200Response as ListReminders200Response
from openproject_api_client.models.list_reminders200_response_embedded import ListReminders200ResponseEmbedded as ListReminders200ResponseEmbedded
from openproject_api_client.models.meeting_model import MeetingModel as MeetingModel
from openproject_api_client.models.meeting_model_links import MeetingModelLinks as MeetingModelLinks
from openproject_api_client.models.membership_collection_model import MembershipCollectionModel as MembershipCollectionModel
from openproject_api_client.models.membership_collection_model_all_of_embedded import MembershipCollectionModelAllOfEmbedded as MembershipCollectionModelAllOfEmbedded
from openproject_api_client.models.membership_form_model import MembershipFormModel as MembershipFormModel
from openproject_api_client.models.membership_form_model_embedded import MembershipFormModelEmbedded as MembershipFormModelEmbedded
from openproject_api_client.models.membership_form_model_embedded_validation_error import MembershipFormModelEmbeddedValidationError as MembershipFormModelEmbeddedValidationError
from openproject_api_client.models.membership_form_model_links import MembershipFormModelLinks as MembershipFormModelLinks
from openproject_api_client.models.membership_read_model import MembershipReadModel as MembershipReadModel
from openproject_api_client.models.membership_read_model_embedded import MembershipReadModelEmbedded as MembershipReadModelEmbedded
from openproject_api_client.models.membership_read_model_embedded_principal import MembershipReadModelEmbeddedPrincipal as MembershipReadModelEmbeddedPrincipal
from openproject_api_client.models.membership_read_model_links import MembershipReadModelLinks as MembershipReadModelLinks
from openproject_api_client.models.membership_schema_model import MembershipSchemaModel as MembershipSchemaModel
from openproject_api_client.models.membership_write_model import MembershipWriteModel as MembershipWriteModel
from openproject_api_client.models.membership_write_model_links import MembershipWriteModelLinks as MembershipWriteModelLinks
from openproject_api_client.models.membership_write_model_meta import MembershipWriteModelMeta as MembershipWriteModelMeta
from openproject_api_client.models.news_create_model import NewsCreateModel as NewsCreateModel
from openproject_api_client.models.news_create_model_links import NewsCreateModelLinks as NewsCreateModelLinks
from openproject_api_client.models.news_model import NewsModel as NewsModel
from openproject_api_client.models.news_model_links import NewsModelLinks as NewsModelLinks
from openproject_api_client.models.non_working_day_collection_model import NonWorkingDayCollectionModel as NonWorkingDayCollectionModel
from openproject_api_client.models.non_working_day_collection_model_all_of_embedded import NonWorkingDayCollectionModelAllOfEmbedded as NonWorkingDayCollectionModelAllOfEmbedded
from openproject_api_client.models.non_working_day_collection_model_all_of_links import NonWorkingDayCollectionModelAllOfLinks as NonWorkingDayCollectionModelAllOfLinks
from openproject_api_client.models.non_working_day_model import NonWorkingDayModel as NonWorkingDayModel
from openproject_api_client.models.non_working_day_model_links import NonWorkingDayModelLinks as NonWorkingDayModelLinks
from openproject_api_client.models.notification_collection_model import NotificationCollectionModel as NotificationCollectionModel
from openproject_api_client.models.notification_collection_model_all_of_embedded import NotificationCollectionModelAllOfEmbedded as NotificationCollectionModelAllOfEmbedded
from openproject_api_client.models.notification_collection_model_all_of_links import NotificationCollectionModelAllOfLinks as NotificationCollectionModelAllOfLinks
from openproject_api_client.models.notification_model import NotificationModel as NotificationModel
from openproject_api_client.models.notification_model_embedded import NotificationModelEmbedded as NotificationModelEmbedded
from openproject_api_client.models.notification_model_links import NotificationModelLinks as NotificationModelLinks
from openproject_api_client.models.o_auth_application_read_model import OAuthApplicationReadModel as OAuthApplicationReadModel
from openproject_api_client.models.o_auth_application_read_model_links import OAuthApplicationReadModelLinks as OAuthApplicationReadModelLinks
from openproject_api_client.models.o_auth_client_credentials_read_model import OAuthClientCredentialsReadModel as OAuthClientCredentialsReadModel
from openproject_api_client.models.o_auth_client_credentials_read_model_links import OAuthClientCredentialsReadModelLinks as OAuthClientCredentialsReadModelLinks
from openproject_api_client.models.o_auth_client_credentials_write_model import OAuthClientCredentialsWriteModel as OAuthClientCredentialsWriteModel
from openproject_api_client.models.offset_paginated_collection_links import OffsetPaginatedCollectionLinks as OffsetPaginatedCollectionLinks
from openproject_api_client.models.offset_paginated_collection_model import OffsetPaginatedCollectionModel as OffsetPaginatedCollectionModel
from openproject_api_client.models.paginated_collection_model import PaginatedCollectionModel as PaginatedCollectionModel
from openproject_api_client.models.paginated_collection_model_all_of_links import PaginatedCollectionModelAllOfLinks as PaginatedCollectionModelAllOfLinks
from openproject_api_client.models.placeholder_user_collection_model import PlaceholderUserCollectionModel as PlaceholderUserCollectionModel
from openproject_api_client.models.placeholder_user_collection_model_all_of_embedded import PlaceholderUserCollectionModelAllOfEmbedded as PlaceholderUserCollectionModelAllOfEmbedded
from openproject_api_client.models.placeholder_user_collection_model_all_of_links import PlaceholderUserCollectionModelAllOfLinks as PlaceholderUserCollectionModelAllOfLinks
from openproject_api_client.models.placeholder_user_create_model import PlaceholderUserCreateModel as PlaceholderUserCreateModel
from openproject_api_client.models.placeholder_user_model import PlaceholderUserModel as PlaceholderUserModel
from openproject_api_client.models.placeholder_user_model_all_of_links import PlaceholderUserModelAllOfLinks as PlaceholderUserModelAllOfLinks
from openproject_api_client.models.post_model import PostModel as PostModel
from openproject_api_client.models.post_model_links import PostModelLinks as PostModelLinks
from openproject_api_client.models.principal_collection_model import PrincipalCollectionModel as PrincipalCollectionModel
from openproject_api_client.models.principal_collection_model_all_of_embedded import PrincipalCollectionModelAllOfEmbedded as PrincipalCollectionModelAllOfEmbedded
from openproject_api_client.models.principal_collection_model_all_of_embedded_elements import PrincipalCollectionModelAllOfEmbeddedElements as PrincipalCollectionModelAllOfEmbeddedElements
from openproject_api_client.models.principal_model import PrincipalModel as PrincipalModel
from openproject_api_client.models.principal_model_links import PrincipalModelLinks as PrincipalModelLinks
from openproject_api_client.models.priority_collection_model import PriorityCollectionModel as PriorityCollectionModel
from openproject_api_client.models.priority_collection_model_all_of_embedded import PriorityCollectionModelAllOfEmbedded as PriorityCollectionModelAllOfEmbedded
from openproject_api_client.models.priority_collection_model_all_of_links import PriorityCollectionModelAllOfLinks as PriorityCollectionModelAllOfLinks
from openproject_api_client.models.priority_collection_model_all_of_links_self import PriorityCollectionModelAllOfLinksSelf as PriorityCollectionModelAllOfLinksSelf
from openproject_api_client.models.priority_model import PriorityModel as PriorityModel
from openproject_api_client.models.priority_model_links import PriorityModelLinks as PriorityModelLinks
from openproject_api_client.models.project_collection_model import ProjectCollectionModel as ProjectCollectionModel
from openproject_api_client.models.project_collection_model_all_of_embedded import ProjectCollectionModelAllOfEmbedded as ProjectCollectionModelAllOfEmbedded
from openproject_api_client.models.project_collection_model_all_of_links import ProjectCollectionModelAllOfLinks as ProjectCollectionModelAllOfLinks
from openproject_api_client.models.project_model import ProjectModel as ProjectModel
from openproject_api_client.models.project_model_links import ProjectModelLinks as ProjectModelLinks
from openproject_api_client.models.project_phase_definition_collection_model import ProjectPhaseDefinitionCollectionModel as ProjectPhaseDefinitionCollectionModel
from openproject_api_client.models.project_phase_definition_collection_model_all_of_embedded import ProjectPhaseDefinitionCollectionModelAllOfEmbedded as ProjectPhaseDefinitionCollectionModelAllOfEmbedded
from openproject_api_client.models.project_phase_definition_collection_model_all_of_links import ProjectPhaseDefinitionCollectionModelAllOfLinks as ProjectPhaseDefinitionCollectionModelAllOfLinks
from openproject_api_client.models.project_phase_definition_model import ProjectPhaseDefinitionModel as ProjectPhaseDefinitionModel
from openproject_api_client.models.project_phase_definition_model_links import ProjectPhaseDefinitionModelLinks as ProjectPhaseDefinitionModelLinks
from openproject_api_client.models.project_phase_model import ProjectPhaseModel as ProjectPhaseModel
from openproject_api_client.models.project_phase_model_links import ProjectPhaseModelLinks as ProjectPhaseModelLinks
from openproject_api_client.models.project_storage_collection_model import ProjectStorageCollectionModel as ProjectStorageCollectionModel
from openproject_api_client.models.project_storage_collection_model_all_of_embedded import ProjectStorageCollectionModelAllOfEmbedded as ProjectStorageCollectionModelAllOfEmbedded
from openproject_api_client.models.project_storage_collection_model_all_of_links import ProjectStorageCollectionModelAllOfLinks as ProjectStorageCollectionModelAllOfLinks
from openproject_api_client.models.project_storage_model import ProjectStorageModel as ProjectStorageModel
from openproject_api_client.models.project_storage_model_links import ProjectStorageModelLinks as ProjectStorageModelLinks
from openproject_api_client.models.projects_schema_model import ProjectsSchemaModel as ProjectsSchemaModel
from openproject_api_client.models.projects_schema_model_attribute_groups_inner import ProjectsSchemaModelAttributeGroupsInner as ProjectsSchemaModelAttributeGroupsInner
from openproject_api_client.models.projects_schema_model_links import ProjectsSchemaModelLinks as ProjectsSchemaModelLinks
from openproject_api_client.models.projects_schema_model_links_self import ProjectsSchemaModelLinksSelf as ProjectsSchemaModelLinksSelf
from openproject_api_client.models.query_column_model import QueryColumnModel as QueryColumnModel
from openproject_api_client.models.query_create_form import QueryCreateForm as QueryCreateForm
from openproject_api_client.models.query_filter_instance_schema_model import QueryFilterInstanceSchemaModel as QueryFilterInstanceSchemaModel
from openproject_api_client.models.query_filter_instance_schema_model_links import QueryFilterInstanceSchemaModelLinks as QueryFilterInstanceSchemaModelLinks
from openproject_api_client.models.query_filter_model import QueryFilterModel as QueryFilterModel
from openproject_api_client.models.query_model import QueryModel as QueryModel
from openproject_api_client.models.query_model_links import QueryModelLinks as QueryModelLinks
from openproject_api_client.models.query_operator_model import QueryOperatorModel as QueryOperatorModel
from openproject_api_client.models.query_sort_by_model import QuerySortByModel as QuerySortByModel
from openproject_api_client.models.query_update_form import QueryUpdateForm as QueryUpdateForm
from openproject_api_client.models.relation_collection_model import RelationCollectionModel as RelationCollectionModel
from openproject_api_client.models.relation_collection_model_all_of_embedded import RelationCollectionModelAllOfEmbedded as RelationCollectionModelAllOfEmbedded
from openproject_api_client.models.relation_collection_model_all_of_links import RelationCollectionModelAllOfLinks as RelationCollectionModelAllOfLinks
from openproject_api_client.models.relation_read_model import RelationReadModel as RelationReadModel
from openproject_api_client.models.relation_read_model_embedded import RelationReadModelEmbedded as RelationReadModelEmbedded
from openproject_api_client.models.relation_read_model_links import RelationReadModelLinks as RelationReadModelLinks
from openproject_api_client.models.relation_write_model import RelationWriteModel as RelationWriteModel
from openproject_api_client.models.relation_write_model_links import RelationWriteModelLinks as RelationWriteModelLinks
from openproject_api_client.models.reminder_model import ReminderModel as ReminderModel
from openproject_api_client.models.reminder_model_links import ReminderModelLinks as ReminderModelLinks
from openproject_api_client.models.revision_model import RevisionModel as RevisionModel
from openproject_api_client.models.revision_model_links import RevisionModelLinks as RevisionModelLinks
from openproject_api_client.models.role_model import RoleModel as RoleModel
from openproject_api_client.models.role_model_links import RoleModelLinks as RoleModelLinks
from openproject_api_client.models.root_model import RootModel as RootModel
from openproject_api_client.models.root_model_links import RootModelLinks as RootModelLinks
from openproject_api_client.models.schema_model import SchemaModel as SchemaModel
from openproject_api_client.models.schema_model_links import SchemaModelLinks as SchemaModelLinks
from openproject_api_client.models.schema_property_model import SchemaPropertyModel as SchemaPropertyModel
from openproject_api_client.models.show_or_validate_form_request import ShowOrValidateFormRequest as ShowOrValidateFormRequest
from openproject_api_client.models.status_collection_model import StatusCollectionModel as StatusCollectionModel
from openproject_api_client.models.status_collection_model_all_of_embedded import StatusCollectionModelAllOfEmbedded as StatusCollectionModelAllOfEmbedded
from openproject_api_client.models.status_model import StatusModel as StatusModel
from openproject_api_client.models.status_model_links import StatusModelLinks as StatusModelLinks
from openproject_api_client.models.storage_collection_model import StorageCollectionModel as StorageCollectionModel
from openproject_api_client.models.storage_collection_model_all_of_embedded import StorageCollectionModelAllOfEmbedded as StorageCollectionModelAllOfEmbedded
from openproject_api_client.models.storage_collection_model_all_of_links import StorageCollectionModelAllOfLinks as StorageCollectionModelAllOfLinks
from openproject_api_client.models.storage_file_model import StorageFileModel as StorageFileModel
from openproject_api_client.models.storage_file_model_all_of_links import StorageFileModelAllOfLinks as StorageFileModelAllOfLinks
from openproject_api_client.models.storage_file_upload_link_model import StorageFileUploadLinkModel as StorageFileUploadLinkModel
from openproject_api_client.models.storage_file_upload_link_model_links import StorageFileUploadLinkModelLinks as StorageFileUploadLinkModelLinks
from openproject_api_client.models.storage_file_upload_preparation_model import StorageFileUploadPreparationModel as StorageFileUploadPreparationModel
from openproject_api_client.models.storage_files_model import StorageFilesModel as StorageFilesModel
from openproject_api_client.models.storage_folder_write_model import StorageFolderWriteModel as StorageFolderWriteModel
from openproject_api_client.models.storage_read_model import StorageReadModel as StorageReadModel
from openproject_api_client.models.storage_read_model_embedded import StorageReadModelEmbedded as StorageReadModelEmbedded
from openproject_api_client.models.storage_read_model_links import StorageReadModelLinks as StorageReadModelLinks
from openproject_api_client.models.storage_write_model import StorageWriteModel as StorageWriteModel
from openproject_api_client.models.storage_write_model_links import StorageWriteModelLinks as StorageWriteModelLinks
from openproject_api_client.models.time_entry_activity_model import TimeEntryActivityModel as TimeEntryActivityModel
from openproject_api_client.models.time_entry_activity_model_embedded import TimeEntryActivityModelEmbedded as TimeEntryActivityModelEmbedded
from openproject_api_client.models.time_entry_activity_model_links import TimeEntryActivityModelLinks as TimeEntryActivityModelLinks
from openproject_api_client.models.time_entry_collection_model import TimeEntryCollectionModel as TimeEntryCollectionModel
from openproject_api_client.models.time_entry_collection_model_all_of_embedded import TimeEntryCollectionModelAllOfEmbedded as TimeEntryCollectionModelAllOfEmbedded
from openproject_api_client.models.time_entry_collection_model_all_of_links import TimeEntryCollectionModelAllOfLinks as TimeEntryCollectionModelAllOfLinks
from openproject_api_client.models.time_entry_model import TimeEntryModel as TimeEntryModel
from openproject_api_client.models.time_entry_model_links import TimeEntryModelLinks as TimeEntryModelLinks
from openproject_api_client.models.toggle_activity_emoji_reaction_request import ToggleActivityEmojiReactionRequest as ToggleActivityEmojiReactionRequest
from openproject_api_client.models.type_model import TypeModel as TypeModel
from openproject_api_client.models.type_model_links import TypeModelLinks as TypeModelLinks
from openproject_api_client.models.types_by_project_model import TypesByProjectModel as TypesByProjectModel
from openproject_api_client.models.types_by_project_model_all_of_embedded import TypesByProjectModelAllOfEmbedded as TypesByProjectModelAllOfEmbedded
from openproject_api_client.models.types_by_project_model_all_of_embedded_elements import TypesByProjectModelAllOfEmbeddedElements as TypesByProjectModelAllOfEmbeddedElements
from openproject_api_client.models.types_by_project_model_all_of_links import TypesByProjectModelAllOfLinks as TypesByProjectModelAllOfLinks
from openproject_api_client.models.update_reminder_request import UpdateReminderRequest as UpdateReminderRequest
from openproject_api_client.models.update_user_preferences_request import UpdateUserPreferencesRequest as UpdateUserPreferencesRequest
from openproject_api_client.models.user_collection_model import UserCollectionModel as UserCollectionModel
from openproject_api_client.models.user_collection_model_all_of_embedded import UserCollectionModelAllOfEmbedded as UserCollectionModelAllOfEmbedded
from openproject_api_client.models.user_collection_model_all_of_links import UserCollectionModelAllOfLinks as UserCollectionModelAllOfLinks
from openproject_api_client.models.user_create_model import UserCreateModel as UserCreateModel
from openproject_api_client.models.user_model import UserModel as UserModel
from openproject_api_client.models.user_model_all_of_links import UserModelAllOfLinks as UserModelAllOfLinks
from openproject_api_client.models.values_property_model import ValuesPropertyModel as ValuesPropertyModel
from openproject_api_client.models.values_property_model_links import ValuesPropertyModelLinks as ValuesPropertyModelLinks
from openproject_api_client.models.version_model import VersionModel as VersionModel
from openproject_api_client.models.version_model_links import VersionModelLinks as VersionModelLinks
from openproject_api_client.models.versions_by_project_model import VersionsByProjectModel as VersionsByProjectModel
from openproject_api_client.models.versions_by_project_model_all_of_embedded import VersionsByProjectModelAllOfEmbedded as VersionsByProjectModelAllOfEmbedded
from openproject_api_client.models.versions_by_project_model_all_of_embedded_elements import VersionsByProjectModelAllOfEmbeddedElements as VersionsByProjectModelAllOfEmbeddedElements
from openproject_api_client.models.versions_by_project_model_all_of_links import VersionsByProjectModelAllOfLinks as VersionsByProjectModelAllOfLinks
from openproject_api_client.models.watchers_model import WatchersModel as WatchersModel
from openproject_api_client.models.watchers_model_all_of_embedded import WatchersModelAllOfEmbedded as WatchersModelAllOfEmbedded
from openproject_api_client.models.watchers_model_all_of_embedded_elements import WatchersModelAllOfEmbeddedElements as WatchersModelAllOfEmbeddedElements
from openproject_api_client.models.watchers_model_all_of_links import WatchersModelAllOfLinks as WatchersModelAllOfLinks
from openproject_api_client.models.week_day_collection_model import WeekDayCollectionModel as WeekDayCollectionModel
from openproject_api_client.models.week_day_collection_model_all_of_embedded import WeekDayCollectionModelAllOfEmbedded as WeekDayCollectionModelAllOfEmbedded
from openproject_api_client.models.week_day_collection_model_all_of_links import WeekDayCollectionModelAllOfLinks as WeekDayCollectionModelAllOfLinks
from openproject_api_client.models.week_day_collection_write_model import WeekDayCollectionWriteModel as WeekDayCollectionWriteModel
from openproject_api_client.models.week_day_collection_write_model_embedded import WeekDayCollectionWriteModelEmbedded as WeekDayCollectionWriteModelEmbedded
from openproject_api_client.models.week_day_collection_write_model_embedded_elements_inner import WeekDayCollectionWriteModelEmbeddedElementsInner as WeekDayCollectionWriteModelEmbeddedElementsInner
from openproject_api_client.models.week_day_model import WeekDayModel as WeekDayModel
from openproject_api_client.models.week_day_self_link_model import WeekDaySelfLinkModel as WeekDaySelfLinkModel
from openproject_api_client.models.week_day_write_model import WeekDayWriteModel as WeekDayWriteModel
from openproject_api_client.models.wiki_page_model import WikiPageModel as WikiPageModel
from openproject_api_client.models.wiki_page_model_links import WikiPageModelLinks as WikiPageModelLinks
from openproject_api_client.models.work_package_form_model import WorkPackageFormModel as WorkPackageFormModel
from openproject_api_client.models.work_package_form_model_embedded import WorkPackageFormModelEmbedded as WorkPackageFormModelEmbedded
from openproject_api_client.models.work_package_form_model_links import WorkPackageFormModelLinks as WorkPackageFormModelLinks
from openproject_api_client.models.work_package_model import WorkPackageModel as WorkPackageModel
from openproject_api_client.models.work_package_model_links import WorkPackageModelLinks as WorkPackageModelLinks
from openproject_api_client.models.work_package_patch_model import WorkPackagePatchModel as WorkPackagePatchModel
from openproject_api_client.models.work_package_schema_model import WorkPackageSchemaModel as WorkPackageSchemaModel
from openproject_api_client.models.work_package_schema_model_links import WorkPackageSchemaModelLinks as WorkPackageSchemaModelLinks
from openproject_api_client.models.work_package_write_model import WorkPackageWriteModel as WorkPackageWriteModel
from openproject_api_client.models.work_package_write_model_links import WorkPackageWriteModelLinks as WorkPackageWriteModelLinks
from openproject_api_client.models.work_packages_model import WorkPackagesModel as WorkPackagesModel
from openproject_api_client.models.work_packages_model_all_of_embedded import WorkPackagesModelAllOfEmbedded as WorkPackagesModelAllOfEmbedded
from openproject_api_client.models.work_packages_model_all_of_links import WorkPackagesModelAllOfLinks as WorkPackagesModelAllOfLinks

