# -*- coding: utf-8 -*-
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from ks.api import GenericApi
from ks.models import KnowledgeServer, License, Organization, ModelMetadata, StructureNode, DataSetStructure, DataSet, \
    Workflow, WorkflowStatus

logger = logging.getLogger(__name__)


def initial_datasets(db_alias):
    """
    In oks1 ho creato datasets anche per i singoli record, es: la singola licenza.
    Deve esserci un modo lazy per cui se ti do un UKCL di una licenza ti creo il dataset "shallow"
    automaticamente; per questo credo che l'attributo shallow debba scomparire.
    Analogamente partendo da un Model cerco il ModelMetadata che abbia dataset_structure not null e creo il relativo
    dataset; devo evitare quello che ho fatto in oks1 in cui ho creato montagne di dss e ds banali
    """

    c4k_it = Organization.objects.get(name='C4K it')
    # DATASETSTRUCTURE DataSetStructure-StructureNode
    mm_dataset_structure = ModelMetadata()
    mm_dataset_structure.content_type = ContentType.objects.get_for_model(DataSetStructure)
    mm_dataset_structure.save(using=db_alias)

    mm_structure_node = ModelMetadata()
    mm_structure_node.content_type = ContentType.objects.get_for_model(StructureNode)
    mm_structure_node.name_of_field_name = "attribute"
    mm_structure_node.save(using=db_alias)

    mm_model_metadata = ModelMetadata()
    #    mm_model_metadata.UKCL=the_koa_org_ks.url() TODO CHECK ?????????
    mm_model_metadata.content_type = ContentType.objects.get_for_model(ModelMetadata)
    mm_model_metadata.save(using=db_alias)

    en4 = StructureNode()
    en4.model_metadata = mm_dataset_structure
    en4.save(using=db_alias)
    en5 = StructureNode()
    en5.model_metadata = mm_structure_node
    en5.attribute = "root_node"
    en5.save(using=db_alias)
    en4.child_nodes.add(en5);
    en4.save(using=db_alias)
    en6 = StructureNode()
    en6.model_metadata = mm_model_metadata
    en6.attribute = "model_metadata"
    en6.external_reference = True
    en6.save(using=db_alias)
    en7 = StructureNode()
    en7.model_metadata = mm_structure_node
    en7.attribute = "child_nodes"
    en7.is_many = True;
    en7.save(using=db_alias)
    en5.child_nodes.add(en6);
    en5.child_nodes.add(en7);
    en5.save(using=db_alias)
    en7.child_nodes.add(en6);
    en7.child_nodes.add(en7);
    en7.save(using=db_alias)

    dss_dataset_structure2structure_node = DataSetStructure(multiple_releases=False,
                                                            root_node=en4,
                                                            name=DataSetStructure.dataset_structure_dsn,
                                                            description="A graph of simple entities that have "
                                                                        "relationships with one another and whose "
                                                                        "instances share the same version, status, ...")
    dss_dataset_structure2structure_node.save(using=db_alias)

    # DATASETSTRUCTURE  License
    mm_license = ModelMetadata()
    mm_license.content_type = ContentType.objects.get_for_model(License)
    mm_license.save(using=db_alias)

    en20 = StructureNode()
    en20.model_metadata = mm_license
    en20.save(using=db_alias)

    dss_license = DataSetStructure()
    dss_license.multiple_releases = True
    dss_license.is_shallow = True  # è necessario ?
    dss_license.root_node = en20
    dss_license.name = DataSetStructure.license_dsn
    dss_license.description = "License information"
    dss_license.save(using=db_alias)

    mm_license.dataset_structure = dss_license
    mm_license.save(using=db_alias)

    # DataSetStructure "view" for the list of licenses
    en21 = StructureNode()
    en21.model_metadata = mm_license
    en21.save(using=db_alias)
    dss_license_list = DataSetStructure()
    dss_license_list.is_a_view = True
    dss_license_list.root_node = en21
    dss_license_list.name = DataSetStructure.license_dsn
    dss_license_list.description = "List of all released licenses"
    dss_license_list.save(using=db_alias)

    c4k_it_ks = KnowledgeServer.objects.get(netloc="root.c4k.it")
    default_wf = Workflow.objects.get(name="Default workflow")
    wf_status_released = WorkflowStatus.objects.get(name="Released")
    ds = DataSet(knowledge_server=c4k_it_ks,
                 dataset_structure=dss_dataset_structure2structure_node,
                 owner_organization=c4k_it,
                 root=dss_license_list,
                 description="DataSet structure of List of licenses",
                 version_major=0,
                 version_minor=1,
                 version_patch=0,
                 version_description="",
                 version_released=True,
                 workflow=default_wf,
                 current_status=wf_status_released)
    ds.save(using=db_alias)
    # ds.set_dataset_on_instances()

    # DataSetStructure "view" for the list of licenses
    en21 = StructureNode()
    en21.model_metadata = mm_license
    en21.save(using=db_alias)
    dss_license_list = DataSetStructure()
    dss_license_list.is_a_view = True
    dss_license_list.root_node = en21
    dss_license_list.name = "List of licenses"
    dss_license_list.description = "List of all released licenses"
    dss_license_list.save(using=db_alias)
    ds = DataSet(knowledge_server=c4k_it_ks,
                 dataset_structure=dss_dataset_structure2structure_node,
                 owner_organization=c4k_it,
                 root=dss_license_list,
                 description="DataSet structure of List of licenses",
                 version_major=0,
                 version_minor=1,
                 version_patch=0,
                 version_description="",
                 version_released=True,
                 workflow=default_wf,
                 current_status=wf_status_released)
    ds.save(using=db_alias)
    # ds.set_dataset_on_instances()


def licenses(db_alias):
    ga = GenericApi(url='https://licenses.opendefinition.org/licenses/groups/od.json')
    ga.invoke()
    for license_name in ga.decoded_response:
        if License.objects.filter(short_name=license_name).exists():
            l = License.objects.filter(short_name=license_name).get()
        else:
            l = License.objects.create(short_name=license_name)
        license_data = ga.decoded_response[license_name]
        if 'domain_content' in license_data:
            l.domain_content = license_data['domain_content']
        if 'domain_data' in license_data:
            l.domain_data = license_data['domain_data']
        if 'domain_software' in license_data:
            l.domain_software = license_data['domain_software']
        if 'id' in license_data:
            l.legacy_id = license_data['id']
        if 'maintainer' in license_data:
            l.maintainer = license_data['maintainer']
        if 'od_conformance' in license_data:
            l.conformance_od = (license_data['od_conformance'] == 'approved')
        if 'osd_conformance' in license_data:
            l.conformance_osd = (license_data['osd_conformance'] == 'approved')
        if 'status' in license_data:
            l.active = (license_data['status'] == 'active')
        if 'title' in license_data:
            l.name = license_data['title']
        if 'url' in license_data:
            l.url = license_data['url']
        l.save(using=db_alias)


def default_workflow(db_alias):
    # Default Workflow
    default_wf = Workflow()
    default_wf.name = "Default workflow"
    default_wf.description = "This is the default workflow. It can be applied to any type of dataset. It has operations to perform the creation of a new version and the release."
    # TODO: add operations to perform the creation of a new version and the release
    default_wf.save(using=db_alias)

    # WorkflowStatus(es)
    # There are common statuses: "New" and "Released"
    # "New" is a newly created dataset; if the workflow is the default it will stay "New" until it gets released
    # "Released" means that editing is finished and the content of the dataset is frozen
    # Method DatasSet.new_version creates a DateSet and sets its state to "New"
    # Method DatasSet.set_released creates a DateSet and sets its state to "Released"
    wf_status_new = WorkflowStatus()
    wf_status_new.name = "New"
    wf_status_new.initial = True
    wf_status_new.create_dataset = True
    wf_status_new.description = ""
    wf_status_new.save(using=db_alias)
    wf_status_new.workflows.add(default_wf)
    wf_status_new.save(using=db_alias)

    wf_status_released = WorkflowStatus()
    wf_status_released.name = "Released"
    wf_status_released.initial = True
    wf_status_released.create_dataset = True
    wf_status_released.description = ""
    wf_status_released.save(using=db_alias)
    wf_status_released.workflows.add(default_wf)
    wf_status_released.save(using=db_alias)


def c4k_oks(db_alias):
    # this data must be created on the root ks but also on any other as it is essential for basic ks operation
    c4k_it = Organization()
    c4k_it.id = 1
    c4k_it.name = "C4K it"
    c4k_it.UKCL = "-"
    c4k_it.website = 'https://www.c4k.it'
    c4k_it.logo = 'https://www.c4k.it/logoc4kit.png'

    c4k_it.description = "The Knowledge Oriented Architecture organization."
    c4k_it.save(using=db_alias)

    c4k_it_ks = KnowledgeServer(pk=1, name="Root Open Knowledge Server", scheme="http",
                                netloc="root.c4k.it",
                                stage_netloc="root.stage.c4k.it",
                                description="The Open Knowledge Server serving the structures and datasets used by any other Knowledge Server.",
                                organization=c4k_it, this_ks=True, html_home="root html_home",
                                html_disclaimer="root html_disclaimer")
    c4k_it_ks.save(using=db_alias)


class Command(BaseCommand):
    help = ''' Some fixture oks_root specific???? '''

    def add_arguments(self, parser):
        parser.add_argument(
            'db_alias', nargs='?',
            help="db_alias",
        )
        parser.add_argument(
            'root', nargs='?',
            help="1 for rootoks.c4k.org, any other value or no value not root",
        )

    def handle(self, *args, **options):
        db_alias = 'default'
        if db_alias in options:
            db_alias = options['db_alias']
        c4k_oks(db_alias)
        default_workflow(db_alias)
        licenses(db_alias)
        initial_datasets(db_alias)
        print("END END END fixture END END END")
        logger.info("END END END fixture END END END")
