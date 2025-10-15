# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from iparapheur_internal.api.admin_advanced_config_api import AdminAdvancedConfigApi
    from iparapheur_internal.api.admin_all_users_api import AdminAllUsersApi
    from iparapheur_internal.api.admin_desk_api import AdminDeskApi
    from iparapheur_internal.api.admin_external_signature_api import AdminExternalSignatureApi
    from iparapheur_internal.api.admin_folder_api import AdminFolderApi
    from iparapheur_internal.api.admin_layer_api import AdminLayerApi
    from iparapheur_internal.api.admin_seal_certificate_api import AdminSealCertificateApi
    from iparapheur_internal.api.admin_template_api import AdminTemplateApi
    from iparapheur_internal.api.admin_trash_bin_api import AdminTrashBinApi
    from iparapheur_internal.api.admin_typology_api import AdminTypologyApi
    from iparapheur_internal.api.admin_workflow_definition_api import AdminWorkflowDefinitionApi
    from iparapheur_internal.api.current_user_api import CurrentUserApi
    from iparapheur_internal.api.desk_api import DeskApi
    from iparapheur_internal.api.document_api import DocumentApi
    from iparapheur_internal.api.folder_api import FolderApi
    from iparapheur_internal.api.secure_mail_api import SecureMailApi
    from iparapheur_internal.api.server_info_api import ServerInfoApi
    from iparapheur_internal.api.template_api import TemplateApi
    from iparapheur_internal.api.tenant_api import TenantApi
    from iparapheur_internal.api.typology_api import TypologyApi
    from iparapheur_internal.api.workflow_api import WorkflowApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from iparapheur_internal.api.admin_advanced_config_api import AdminAdvancedConfigApi
from iparapheur_internal.api.admin_all_users_api import AdminAllUsersApi
from iparapheur_internal.api.admin_desk_api import AdminDeskApi
from iparapheur_internal.api.admin_external_signature_api import AdminExternalSignatureApi
from iparapheur_internal.api.admin_folder_api import AdminFolderApi
from iparapheur_internal.api.admin_layer_api import AdminLayerApi
from iparapheur_internal.api.admin_seal_certificate_api import AdminSealCertificateApi
from iparapheur_internal.api.admin_template_api import AdminTemplateApi
from iparapheur_internal.api.admin_trash_bin_api import AdminTrashBinApi
from iparapheur_internal.api.admin_typology_api import AdminTypologyApi
from iparapheur_internal.api.admin_workflow_definition_api import AdminWorkflowDefinitionApi
from iparapheur_internal.api.current_user_api import CurrentUserApi
from iparapheur_internal.api.desk_api import DeskApi
from iparapheur_internal.api.document_api import DocumentApi
from iparapheur_internal.api.folder_api import FolderApi
from iparapheur_internal.api.secure_mail_api import SecureMailApi
from iparapheur_internal.api.server_info_api import ServerInfoApi
from iparapheur_internal.api.template_api import TemplateApi
from iparapheur_internal.api.tenant_api import TenantApi
from iparapheur_internal.api.typology_api import TypologyApi
from iparapheur_internal.api.workflow_api import WorkflowApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
