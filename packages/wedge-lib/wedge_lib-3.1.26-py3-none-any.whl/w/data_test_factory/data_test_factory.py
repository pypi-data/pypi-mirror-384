import copy

from django.core.exceptions import ObjectDoesNotExist, FieldDoesNotExist
from django.db import models
from factory import SubFactory

from w.django import utils
from w.services.technical.dict_service import DictService
from w.tests.helpers import date_test_helper


class DataTestFactory:
    def __init__(self, sequence_start=1):
        self.data_repository = {}
        self.snapshot_repository = {}
        self._snapshot = None
        self.factory_repository = []
        self._today_is = "2015-09-03 11:15:00"
        self.sequence_start = sequence_start

    def _factory_reset_sequence(self, facto):
        # as we cannot reset descendant factories, reset parent
        # noinspection PyProtectedMember
        facto._meta.counter_reference.factory.reset_sequence(self.sequence_start)
        for attr, dec in facto._meta.declarations.items():
            if isinstance(dec, SubFactory):
                self._check_and_reset_factory(dec.factory_wrapper.factory)

    def _check_and_reset_factory(self, factory_class):
        if factory_class not in self.factory_repository and factory_class is not None:
            self._factory_reset_sequence(factory_class)
            self.factory_repository.append(factory_class)

    @staticmethod
    def _find_direct_relation_name(fk_model, parent_model):
        return [
            f.name
            for f in parent_model._meta.fields
            if f.many_to_one is True and f.related_model == fk_model
        ][0]

    def _create_fk(self, data_def):
        # si on trouve une relation directe, on crée l'objet lié cash pistache,
        # sauf si c'est un objet existant un objet existant est référencé par le
        # mot clef _data_ref
        use_data_ref = data_def.get("data_ref", None)
        if (
            use_data_ref in self.data_repository and len(data_def) >= 2
        ):  # pragma: no cover (todo one day)
            raise RuntimeError(
                "l'entrée " + use_data_ref + " est déjà définie par ailleurs."
            )

        if use_data_ref and len(data_def) == 1:
            # si l'entrée dataref est trouvée et qu'elle est seule, on va faire
            # une recherche dans le repo de data préalablement crée.
            # @TBD : si la relation n'est pas trouvé, on pourrait déférrer la
            # création à plus tard, quand l'objet serait trouvé
            return self.get_by_ref(use_data_ref)

        created_models, snapshots = self._load_data(data_def)
        return created_models
        # on pourra ensuite passer cet objet à l'objet en cours pour création

    @staticmethod
    def _is_many2many_field(parent_model: models.Model, fieldname):
        try:
            field_class = parent_model._meta.get_field(fieldname).__class__.__name__
            return field_class in ["ManyToManyField", "ManyToManyRel"]
        except FieldDoesNotExist:  # pragma: no cover (todo one day)
            raise RuntimeError(
                f"{fieldname} not found in {parent_model.__class__.__name__}"
            )

    @staticmethod
    def _is_reverse_one2one_field(parent_model: models.Model, fieldname):
        try:
            field_class = parent_model._meta.get_field(fieldname).__class__.__name__
            return field_class in ["OneToOneRel"]
        except FieldDoesNotExist:  # pragma: no cover (todo one day)
            raise RuntimeError(
                f"{fieldname} not found in {parent_model.__class__.__name__}"
            )

    def _prepare_relations(self, data_def):
        fk_relations = {}
        one2one_relations = {}
        many2many_relations = {}
        for key, value in data_def["values"].copy().items():
            # on va examiner les relations
            if isinstance(value, dict):
                # si on a un élément de type dict, il s'agit d'une relation directe
                if self._is_reverse_one2one_field(data_def["factory"]._meta.model, key):
                    one2one_relations[key] = data_def["values"].pop(key)
                    continue
                fk_relations[key] = self._create_fk(value)
                continue

            if isinstance(value, list):
                # si on a un élément de type list, alors c'est une relation inverse ou
                # many2many. Il faut créer l'objet en cours avant de créer les objets
                # liés on pop donc la structure des enfants,
                # pour permettre la création de l'objet en cours, sans être pollué par
                # les enfants
                many2many_relations[key] = data_def["values"].pop(key)

        return fk_relations, one2one_relations, many2many_relations

    def _create_by_factory(self, data_def, fieldname=None, parent_model=None):
        factory_class = data_def.get("factory")
        self._check_and_reset_factory(factory_class)

        # prepare relations => create needed fk or delay many2many relations creation
        fk_relations, one2one_relations, many2many_relations = self._prepare_relations(
            data_def
        )
        # parent_model._meta.get_field(fieldname).field.cache_name
        create_datas = {**data_def["values"]}

        if parent_model and self._is_reverse_one2one_field(parent_model, fieldname):
            reverse_field = parent_model._meta.get_field(fieldname).field.cache_name
            create_datas[reverse_field] = parent_model

        # si on a un objet en fk, il faut l'ajouter dans les paramètres de la factory,
        # via le nom de la relation, qu'il nous faut trouver
        if (
            parent_model
            and not self._is_many2many_field(parent_model, fieldname)
            and not self._is_reverse_one2one_field(parent_model, fieldname)
        ):
            # la relation est en réalité une relation foreign key inverse
            rel_name = self._find_direct_relation_name(
                parent_model._meta.model, factory_class._meta.model
            )
            create_datas.update({rel_name: parent_model})

        if fk_relations:
            create_datas.update(**fk_relations)

        created = factory_class(**create_datas)
        snapshot = utils.model_to_dict(created)
        snapshot = snapshot if snapshot else {}

        # si on a poppé des relations inverses, il faut alors passer l'objet crée, à
        # l'étage du dessous pour création car certaines sont non nullables
        if many2many_relations:
            for fieldname, value in many2many_relations.items():
                _, many2many_snapshot = self._load_data(
                    value, fieldname=fieldname, related_object=created
                )
                snapshot[fieldname] = copy.deepcopy(many2many_snapshot)

        if one2one_relations:
            for fieldname, value in one2one_relations.items():
                _, one2one_snapshot = self._load_data(
                    value, fieldname=fieldname, related_object=created
                )
                snapshot[fieldname] = copy.deepcopy(one2one_snapshot)

        return created, snapshot

    def _parse_and_create_object(self, data_def, fieldname=None, parent_model=None):
        # si l'objet à créer est un callable, on se pose pas de question, on call
        obj_to_create = copy.deepcopy(data_def)
        use_data_ref = obj_to_create.pop("data_ref", None)

        if "factory" in obj_to_create:
            data, snapshot = self._create_by_factory(
                obj_to_create, fieldname, parent_model
            )
        elif use_data_ref:
            data = self.get_by_ref(use_data_ref)
            snapshot = self._get_snapshot_by_ref(use_data_ref)
        elif "from_db" in data_def:
            db_data = data_def.pop("from_db", None)
            data = self._get_from_db(**db_data)
            snapshot = utils.model_to_dict(data)
        else:  # pragma: no cover (todo one day)
            raise RuntimeError(
                f"factory not found for {obj_to_create} or missing data_ref"
            )

        if parent_model and self._is_many2many_field(parent_model, fieldname):
            getattr(parent_model, fieldname).add(data)
        return data, snapshot

    def _add_to_snapshot_repository(self, data_ref, snapshot):
        self.snapshot_repository.update({data_ref: snapshot})

    def _get_snapshot_by_ref(self, data_ref):
        return self.snapshot_repository.get(data_ref, None)

    def _add_to_data_repository(self, data_ref=None, data_content=None):
        self.data_repository.update({data_ref: data_content})

    def get_by_ref(self, data_ref):
        found = self.data_repository.get(data_ref, None)
        if found is None:  # pragma: no cover (todo one day)
            raise ObjectDoesNotExist(
                "dataref : '" + data_ref + "' Not previously created !"
            )
        return found

    @staticmethod
    def _get_unique_data_ref(data_ref, nb):
        # nous devons assurer l'unicité de la dataref dans le cas
        # d'instanciation multiple
        return f"{data_ref}_{nb}" if data_ref and nb > 1 else data_ref

    @staticmethod
    def _get_from_db(model, selector):
        return model.objects.get(**selector)

    def _load_data_def_context(self, data_def) -> None:
        """Load context if necessary"""
        for context_data_def in data_def.get("context", []):
            self._load_data(context_data_def)

    def _load_dict_data(self, data_def, many2many_key=None, fk_object=None):
        # load some context first if necessary
        self._load_data_def_context(data_def)

        data_occurrence = data_def.pop("nb", 1)
        data_ref = data_def.pop("ref", None)
        created_objects = []
        snapshots = []
        for cpt in range(0, data_occurrence):
            # on doit travailler sur une copie, pour pouvoir pop tranquillement les
            # valeurs spéciales, plusieurs fois.
            created_object, snapshot = self._parse_and_create_object(
                data_def, many2many_key, fk_object
            )
            if data_ref:
                unique_data_ref = self._get_unique_data_ref(data_ref, cpt + 1)
                self._add_to_data_repository(unique_data_ref, created_object)
                self._add_to_snapshot_repository(unique_data_ref, snapshot)
            created_objects.append(created_object)
            snapshots.append(snapshot)
        if data_occurrence > 1:
            return created_objects, snapshots
        return created_objects[0], snapshots[0]

    def _load_list_data(self, data_def, many2many_key, fk_object):
        created = []
        snapshots = []
        for data in data_def:
            created_object, snapshot = self._load_data(data, many2many_key, fk_object)
            created.append(created_object)
            snapshots.append(copy.deepcopy(snapshot))
        return created, snapshots

    def _load_data(self, data_def, fieldname=None, related_object=None):
        # besoin de faire une copie dans le cas ou les définitions de datas
        # sont utilisées plusieurs fois
        data_def_copy = data_def.copy()
        if isinstance(data_def_copy, list):
            return self._load_list_data(data_def_copy, fieldname, related_object)

        if "values" not in data_def_copy:
            # add missing data key
            data_def_copy["values"] = {}

        return self._load_dict_data(data_def_copy, fieldname, related_object)

    def today_is(self, today_date: str) -> "DataTestFactory":
        """
        Force today's date

        Args:
            today_date(str): YYYY-MM-DD HH:MM:SS

        Returns:
            DataTestFactory
        """
        self._today_is = today_date
        return self

    def build(self, data_def, nb=None, override_values=None):
        if override_values:
            data_def = DictService.deep_merge(data_def, {"values": override_values})

        with date_test_helper.today_is(self._today_is):
            data_def_copy = data_def.copy()
            if nb and nb > 0:
                data_def_copy["nb"] = nb
            created_objects, self._snapshot = self._load_data(data_def_copy)
        return created_objects

    def built_snapshots(self):
        return {k: v for k, v in self.snapshot_repository.items()}
