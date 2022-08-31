# -*- coding: utf-8 -*-
# Subject to the terms of the GNU AFFERO GENERAL PUBLIC LICENSE, v. 3.0. If a copy of the AGPL was not
# distributed with this file, You can obtain one at http://www.gnu.org/licenses/agpl.txt
#
# Author: Davide Galletti                davide   ( at )   c4k.it
from django.db import models


class KCModelManager(models.Manager):
    '''
    Created to be used by KnowledgeChunk/ShareableModel so that all classes that inherit
    will get the post_save signal bound to model_post_save. The following decorator

    @receiver(post_save, sender=ShareableModel)
    def model_post_save(sender, **kwargs):

    wouldn't work at all while it would work specifying the class name that inherits e.g. Workflow

    @receiver(post_save, sender=Workflow)
    def model_post_save(sender, **kwargs):

    '''

    def contribute_to_class(self, model, name):
        super(KCModelManager, self).contribute_to_class(model, name)
        self._bind_post_save_signal(model)

    def _bind_post_save_signal(self, model):
        models.signals.post_save.connect(model_post_save, model)


def model_post_save(sender, **kwargs):
    # CHECK PERCHE' NON PRE_SAVE???
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
    UKCL = models.CharField(max_length=750, default='', blank=True, db_index=True)
    '''
    prev_UKCL = UKCL_previous_version is the UKCL of the previous version if 
    this record has been created with the new_version method.
    It is used when materializing to update the relationships from old to new records
    '''
    prev_UKCL = models.CharField(max_length=750, null=True, blank=True, db_index=True)
    '''
    Each instance of a KnowledgeChunk Model should, sooner or later, be part of a dataset that is not a view neither 
    shallow e.g. has version information. DataSet.set_released sets this attribute for each instance in the dataset
    '''
    dataset_I_belong_to = models.ForeignKey("DataSet", on_delete=models.CASCADE, null=True, blank=True,
                                            related_name='+')

    objects = KCModelManager()


class KnowledgeServer(KnowledgeChunk):
    pass


class DataSetStructure(KnowledgeChunk):
    # USATI IN OKS1 X ESTRARRE LE ISTANZE SPECIFICHE DI DSS; RENDERE LE ISTANZE VARIABILI GLOBALI DEFINITE QUI IN
    # MODEL, FARE LO STESSO PER THIS_KS
    # # DSN = DataSet Structure Name
    # dataset_structure_DSN = "Dataset structure"
    # model_metadata_DSN = "Model meta-data"
    # organization_DSN = "Organization and Open Knowledge Servers"
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


class DataSet(KnowledgeChunk):
    pass


this_ks = None
try:
    this_ks = KnowledgeServer.objects.get(id=0)  # TODO ...
except:
    pass
