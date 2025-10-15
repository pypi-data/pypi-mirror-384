# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from iparapheur_provisioning.api.admin_all_users_api import AdminAllUsersApi
    from iparapheur_provisioning.api.admin_desk_api import AdminDeskApi
    from iparapheur_provisioning.api.admin_external_signature_api import AdminExternalSignatureApi
    from iparapheur_provisioning.api.admin_folder_api import AdminFolderApi
    from iparapheur_provisioning.api.admin_metadata_api import AdminMetadataApi
    from iparapheur_provisioning.api.admin_seal_certificate_api import AdminSealCertificateApi
    from iparapheur_provisioning.api.admin_template_api import AdminTemplateApi
    from iparapheur_provisioning.api.admin_tenant_api import AdminTenantApi
    from iparapheur_provisioning.api.admin_tenant_user_api import AdminTenantUserApi
    from iparapheur_provisioning.api.admin_typology_api import AdminTypologyApi
    from iparapheur_provisioning.api.admin_workflow_definition_api import AdminWorkflowDefinitionApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from iparapheur_provisioning.api.admin_all_users_api import AdminAllUsersApi
from iparapheur_provisioning.api.admin_desk_api import AdminDeskApi
from iparapheur_provisioning.api.admin_external_signature_api import AdminExternalSignatureApi
from iparapheur_provisioning.api.admin_folder_api import AdminFolderApi
from iparapheur_provisioning.api.admin_metadata_api import AdminMetadataApi
from iparapheur_provisioning.api.admin_seal_certificate_api import AdminSealCertificateApi
from iparapheur_provisioning.api.admin_template_api import AdminTemplateApi
from iparapheur_provisioning.api.admin_tenant_api import AdminTenantApi
from iparapheur_provisioning.api.admin_tenant_user_api import AdminTenantUserApi
from iparapheur_provisioning.api.admin_typology_api import AdminTypologyApi
from iparapheur_provisioning.api.admin_workflow_definition_api import AdminWorkflowDefinitionApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
