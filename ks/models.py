# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
import logging, urllib

from django.apps.registry import apps as global_apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from ks.orm_wrapper import OrmWrapper
from ks.utils import KsUrl

logger = logging.getLogger(__name__)


class KCModelManager(models.Manager):
    """
    KC = KnowledgeChunk
    Created to be used by KnowledgeChunk/ShareableModel so that all classes that inherit
    will get the post_save signal bound to model_post_save. The following decorator

    @receiver(post_save, sender=KnowledgeChunk)
    def model_post_save(sender, **kwargs):

    wouldn't work at all while it would work specifying the class name that inherits e.g. Workflow

    @receiver(post_save, sender=Workflow)
    def model_post_save(sender, **kwargs):
    """

    def contribute_to_class(self, model, name):
        super(KCModelManager, self).contribute_to_class(model, name)
        self._bind_post_save_signal(model)

    def _bind_post_save_signal(self, model):
        models.signals.post_save.connect(model_post_save, model)


def model_post_save(sender, **kwargs):
    # TODO CHECK PERCHE' NON PRE_SAVE???
    if kwargs['instance'].UKCL == "":
        try:
            kwargs['instance'].UKCL = kwargs['instance'].generate_UKCL()
            if kwargs['instance'].UKCL != "":
                kwargs['instance'].save()
        except Exception as e:
            logger.error("model_post_save kwargs['instance'].UKCL: " + kwargs['instance'].UKCL + "  -  " + str(e))
    if isinstance(kwargs['instance'], DataSet):
        if kwargs['instance'].first_version_id == None:
            kwargs['instance'].first_version_id = kwargs['instance'].pk
            kwargs['instance'].save()


class KnowledgeChunk(models.Model):
    '''
    KnowledgeChunk (it was ShareableModel) is the superclass of all classes, including the ones you define in your
    apps, that can be shared via a KnowledgeServer
    UKCL Uniform Knowledge Chunk Locator
    UKCL is the unique identifier of this KnowledgeChunk in this KS
    When a new instance of a KnowledgeChunk is created within a dataset with the
    new_version method, a new UKCL is generated using generate_UKCL
    '''
    UKCL = models.CharField(max_length=2000, default='-', db_index=True)
    '''
    prev_UKCL = UKCL_previous_version is the UKCL of the previous version if 
    this record has been created with the new_version method.
    It is used when materializing to update the relationships from old to new records
    '''
    prev_UKCL = models.CharField(max_length=2000, null=True, blank=True, db_index=True)
    '''
    Each instance of a KnowledgeChunk Model should, sooner or later, be part of a dataset that is not a view neither 
    shallow e.g. has version information. DataSet.set_released sets this attribute for each instance in the dataset
    '''
    dataset_I_belong_to = models.ForeignKey("DataSet", on_delete=models.CASCADE, null=True, blank=True,
                                            related_name='+')

    objects = KCModelManager()

    class Meta:
        abstract = True


class Organization(KnowledgeChunk):
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=2000, blank=True)
    website = models.CharField(max_length=500, blank=True)
    logo = models.CharField(max_length=500, blank=True)


class KnowledgeServer(KnowledgeChunk):
    root_apps = ['knowledge_server', 'licenses', 'serializable']
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=2000, blank=True)
    # ASSERT: only one KnowledgeServer in each KS has this_ks = True (in materialized db); I use it to know in which KS I am
    # this is handled when importing data about an external KS; I cannot use an approach like Django's SITE_ID
    # as this_ks might change over time (it is a KnowledgeChunk itself, part of a DataSet ...)
    this_ks = models.BooleanField(default=False)
    # urlparse terminology https://docs.python.org/2/library/urlparse.html
    # scheme e.g. { "http" | "https" }
    scheme = models.CharField(max_length=50, default="http")
    # netloc e.g. "root.c4k.it"
    netloc = models.CharField(max_length=500)
    # same as netloc but for stage instance
    stage_netloc = models.CharField(max_length=500)
    #  html_home text that gets displayed at the home page
    html_home = models.TextField(default="")
    #  html_disclaimer text that gets displayed at the disclaimer page
    html_disclaimer = models.TextField(default="")
    #  html_* can include html tags
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def url(self, encode=False):
        # "http://root.beta.thekoa.org/"
        tmp_url = self.scheme + "://" + self.netloc
        if encode:
            tmp_url = urllib.parse.urlencode({'': tmp_url})[1:]
        return tmp_url


class DataSetStructure(KnowledgeChunk):
    # USATI IN OKS1 X ESTRARRE LE ISTANZE SPECIFICHE DI DSS; RENDERE LE ISTANZE VARIABILI GLOBALI DEFINITE QUI IN
    # MODEL, FARE LO STESSO PER THIS_KS
    # DSN = DataSet Structure Name
    dataset_structure_DSN = "Dataset structure"
    model_metadata_DSN = "Model meta-data"
    organization_DSN = "Organization and Open Knowledge Servers"
    # license_DSN = "License"
    """    Types of DataSetStructures
    versionable  : they are the default, used to define the structure of an DataSet
                   CONSTRAINT: if a ModelMetadata is in one of them it cannot be in another one of them
                   it has version information
    shallow      : created automatically to export a ModelMetadata
                   CONSTRAINT: only one shallow per ModelMetadata
                   it has NO version information
    view         : used for example to export a structure different from one of the above;
                   it has NO version information

    CHECK: Only versionable and view are listed on the OKS and other systems can subscribe to.
    """
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=2000, default='')
    '''
    the entry point of the structure; the class StructureNode has then child_nodes of the same class 
    hence it defines the structure/graph
    assert: the root_node is the entry point for only one structure 
    '''
    root_node = models.ForeignKey('StructureNode', on_delete=models.CASCADE, related_name='dataset_type')
    '''
    when multiple_releases is true more than one instance get materialized
    otherwise just one; it defaults to False just not to make it nullable;
    a default is indicated as shallow structures are created without specifying it
    makes no sense when is_a_view
    '''
    multiple_releases = models.BooleanField(default=False)
    '''
    TODO cacheare in un campo json la struttura che va restituita da 
    def get_spec(self):
    in modo da rendere l'operazione efficente
    '''
    json_serialization_spec = models.JSONField(blank=True, null=True)

    def get_spec(self):
        if not self.json_serialization_spec:
            pass  # TODO costruisci la struttura
        return self.json_serialization_spec

    @staticmethod
    def get_from_name(dsn_name, db_alias='default'):
        try:
            materialized = DataSetStructure.objects.using('materialized').get(name=dsn_name)
            if db_alias == 'default':
                return DataSetStructure.objects.using('default').get(UKCL=materialized.UKCL)
            else:
                return materialized
        except:
            return None


dss_dss = DataSetStructure.get_from_name(DataSetStructure.dataset_structure_DSN)
mm_dss = DataSetStructure.get_from_name(DataSetStructure.model_metadata_DSN)
org_dss = DataSetStructure.get_from_name(DataSetStructure.organization_DSN)


class ModelMetadata(KnowledgeChunk):
    '''
    A ModelMetadata roughly contains the meta-data describing a table in a database or a class if we have an ORM
    '''
    # this name corresponds to the class name
    name = models.CharField(max_length=100, db_index=True)
    '''
    The module determines the app/module name containing the class
    describing the model (e.g. the object-relational mapping). A module acts as 
    a namespace that belongs to the organization that created the model (and the 
    ModelMetadata record). Within that namespace the model names are unique. A model 
    License che be in the "licenses" namespace of an OKS but also on the "software"
    namespace of the OKS or on another namespace of another OKS.
    Along with the Organization URL netloc, it is used to create a unique
    name for the app/module so that there can be no collisions. See OrmWrapper
    for more details.
    '''
    '''
    module is Python terminology; app is Django. More generally the module is a group of models,
    shareable models in our case. It is part of the name of the namespace where each model lives.
    It is used to build the UKCL.
    For its use, it is not supposed to change over time.
    '''
    module = models.CharField(max_length=500, db_index=True)
    description = models.CharField(max_length=2000, default="")
    table_name = models.CharField(max_length=255, db_column='tableName', default="")
    id_field = models.CharField(max_length=255, db_column='idField', default="id")
    name_field = models.CharField(max_length=255, db_column='nameField', default="name")
    description_field = models.CharField(max_length=255, db_column='descriptionField', default="description")
    '''
    dataset_structure attribute is not in NORMAL FORM! When not null it tells in which DataSetStructure is this 
    ModelMetadata; a ModelMetadata must be in only one DataSetStructure for version/state purposes! 
    It can be in as many DataSetStructure-views as you need.
    '''
    dataset_structure = models.ForeignKey("DataSetStructure", on_delete=models.CASCADE, null=True, blank=True)


class StructureNode(KnowledgeChunk):
    model_metadata = models.ForeignKey(ModelMetadata, on_delete=models.CASCADE, null=True, blank=True)
    # attribute is blank for the entry point as it is available as dataset.root
    attribute = models.CharField(max_length=255, blank=True)
    # if ct and fk are not '' then it is a GenericForeignKey e.g. I do not
    # now to which ContentType the fk points to; ct_field tells me which ContentType;
    # fk tells me the pk value
    # model_metadata is None if it is a GenericForeignKey
    ct_field = models.CharField(max_length=255, default='')
    fk_field = models.CharField(max_length=255, default='')
    '''
       method_to_retrieve is a method that can be invoked to retrieve
       the value of the instance or instances corresponding to this 
       node of the structure. It is an alternative to the attribute,
       they can't be both present.
       Use case: the structure of a SerializableModel(models.Model) <<==>> ModelMetadata
       has a list of fields; there is no need to store them in the database as
       they are *somehow* available using reflection; when we serialize an instance
       of ModelMetadata we use a method of the instance (inherited from SerializableModel) 
       to retrieve the list of fields of the class corresponding to that instance.
    '''
    method_to_retrieve = models.CharField(max_length=255, null=True, blank=True)

    # there is only one parent so we should change to
    child_nodes = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="parent")
    # if not external_reference all attributes are exported, otherwise only the id
    external_reference = models.BooleanField(default=False, db_column='externalReference', db_index=True)
    # is_many is true if the attribute correspond to a list of instances of the ModelMetadata
    is_many = models.BooleanField(default=False, db_column='isMany')


class License(KnowledgeChunk):
    '''
    Licenses from the list on http://opendefinition.org/licenses/
    JUST THOSE WITH DOMAIN DATA
    '''
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50)
    # human_readable is a summary of the legal code;
    human_readable = models.TextField(null=True, blank=True)
    legalcode = models.TextField(default="")
    adaptation_shared = models.BooleanField(blank=True, null=True)
    # requires to be shared with the attribution
    attribution = models.BooleanField(blank=True, null=True)
    # requires to be shared with the same license
    share_alike = models.BooleanField(blank=True, null=True)
    commercial_use = models.BooleanField(blank=True, null=True)
    derivatives = models.BooleanField(blank=True, null=True)
    url_info = models.CharField(max_length=160, null=True, blank=True)
    reccomended_by_opendefinition = models.BooleanField(blank=True, null=True)
    conformant_for_opendefinition = models.BooleanField(blank=True, null=True)
    image = models.CharField(max_length=160, null=True, blank=True)
    image_small = models.CharField(max_length=160, null=True, blank=True)


class Workflow(KnowledgeChunk):
    '''
    Is a list of WorkflowMethods; the work-flow is somehow abstract, its methods do not specify details of
    the operation but just the statuses
    '''
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=2000, blank=True)
    # A workflow deals only with one type of dataset; any constraint on the DataSetStructure e.g. is_shallow=False? is_a_view=False? Direi entrambi ...
    type = models.ForeignKey(DataSetStructure, on_delete=models.CASCADE, blank=True, null=True)
    '''
    '    A dataset, even though its type can have more workflows, can be managed only by one workflow.
    '    When a workflow gets a new version, datasets managed by it can either migrate to the new version
    '    or continue their life within the old version. TODO: we must add metadata to define the migration
    '''


class WorkflowStatus(KnowledgeChunk):
    '''
    TODO: We need to have some statuses that are available to any entity and some just to specific entities; how?
    Maybe we can add a type to the statuses so that we can say that a status is of type "Initial" or "Closed"
    and the type can have some functional implications: e.g. "Closed" are not listed in a default view.
    Do we really need what's above??????
    '''
    # initial means the workflow can be spawned in this state
    initial = models.BooleanField(default=False)
    # if create_dataset is true an instance of the dataset is created
    create_dataset = models.BooleanField(default=False)

    final = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    workflows = models.ManyToManyField(Workflow, blank=True, related_name='statuses')
    description = models.CharField(max_length=2000, blank=True)


class DataSet(KnowledgeChunk):
    '''
    A data set / chunk of knowledge; its data structure is described by self.dataset_structure
    The only Versionable object so far
    Serializable like many others
    It has an owner KS which can be inferred by the UKCL but it is explicitly linked

    A DataSet is Versionable (if its structure is neither shallow nor a view) so there are many datasets
    that are basically different versions of the same thing; they share the same "first_version" attribute

    A DataSet has a status and a workflow; a default workflow has at least an operation for the following methods

    Relevant methods:
        new version:  create a copy of all instances starting from the root, following the nodes in the
                      structure, all but those with external_reference=True
        set_released: it sets version_released True and it sets it to False for all the other instances
                      of the same set; it materializes the dataset
    '''

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='workflow_dataset', null=True,
                                 blank=True)
    current_status = models.ForeignKey(WorkflowStatus, on_delete=models.CASCADE, null=True, blank=True)

    '''
    The knowledge server that is making this dataset available; not necessarily the
    organization that owns this knowledge server is the author of the data in the set.
    The Organization that has published the information in this dataset is 
    knowledge_server.organization.
    '''
    knowledge_server = models.ForeignKey(KnowledgeServer, on_delete=models.CASCADE)

    # if the dataset structure is intended to be a view there won't be any version information
    # assert dataset_structure.is_a_view ===> root, version, ... == None
    dataset_structure = models.ForeignKey(DataSetStructure, on_delete=models.CASCADE)

    # if it is a view a description might be useful
    description = models.CharField(max_length=2000, default="")

    root_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    root_instance_id = models.PositiveIntegerField(null=True, blank=True)
    root = GenericForeignKey('root_content_type', 'root_instance_id')

    # An alternative to the root_node_id is to have a filter to apply to the all the objects
    # of type root_content_type. Assert:
    #     filter_text != None ===> root == None
    #     root != None ===> filter_text == None
    # If root_node == None filter_text can be "" meaning that you have to take all of the
    # entries without filtering them
    filter_text = models.CharField(max_length=200, null=True, blank=True)

    # When root is None (hence the structure is a view) I still might want to refer to a version for the
    # data that will be in my view; there might be data belonging to different versions matching the
    # criteria in the filter text; to prevent this I specify a DataSet (that has its own version) so
    # that I will put in the view only those belonging to that version
    filter_dataset = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    # NOT USED YET: TODO: it should be used in get_instances

    # a dataset has one or more licenses; the organization that can assign licenses
    # to this dataset is owner_organization; in case of attribution it is the one to be credited
    owner_organization = models.ForeignKey("Organization", on_delete=models.CASCADE, null=True, blank=True)
    # creation_date when the owner organization has published the data
    creation_date = models.DateTimeField(null=True, blank=True)
    # following attributes used to be in a separate class VersionableDataSet
    '''
    An Instance belongs to a set of instances which are basically the same but with a different version.
    first_version is the first instance of this set; first_version has first_version=self so that if I filter 
    for first_version=smthng I get all of them including the first_version
    WE REFER TO SUCH SET AS THE "version set"
    '''
    first_version = models.ForeignKey('self', on_delete=models.CASCADE, related_name='versions', null=True, blank=True)
    # http://semver.org/
    version_major = models.IntegerField(null=True, blank=True, db_index=True)
    version_minor = models.IntegerField(null=True, blank=True, db_index=True)
    version_patch = models.IntegerField(null=True, blank=True, db_index=True)
    version_description = models.CharField(max_length=2000, default="")
    # release_date is the date of the release of the dataset; e.g. the date the Creative
    # Commons Attribution 1.0 license was released
    release_date = models.DateTimeField(auto_now_add=True)
    # version_date is the date this version has been released in the OKS
    version_date = models.DateTimeField(auto_now_add=True)
    '''
    Assert: If self.dataset_structure.multiple_releases==False: at most one instance in the VERSION SET
            has version_released = True
    '''
    version_released = models.BooleanField(default=False, db_index=True)
    '''
        http://www.dcc.ac.uk/resources/how-guides/license-research-data 
        "The option to multiply license a dataset is certainly available to you if you hold all the rights 
        that pertain to the dataset"
    '''
    licenses = models.ManyToManyField(License)


class DynamicModelContainer(KnowledgeChunk):
    '''
    Some apps/modules/model containers
    are imported from other OKSs; we need a list of them so that
    we can load them dynamically using
    django.core.signals.request_started
    '''
    name = models.CharField(max_length=500)





this_ks = None
try:
    this_ks = KnowledgeServer.objects.get(this_ks=True)
except:
    pass
