"""utils module for building entities from python objects dict|list."""

from ulid import ULID

from cmem_plugin_base.dataintegration.entity import Entities, Entity, EntityPath, EntitySchema


def merge_path_values(paths_map1: dict, paths_map2: dict) -> dict:
    """Merge two dictionaries representing paths and values.

    This function takes two dictionaries, `paths_map1` and `paths_map2`,
    each representing paths and corresponding values. It merges these dictionaries
    by combining values for common paths and returns the merged dictionary.

    Args:
        paths_map1 (dict): The first dictionary containing paths and values.
        paths_map2 (dict): The second dictionary containing paths and values.

    Returns:
        dict: A merged dictionary containing combined values for common paths.

    """
    for key, value in paths_map2.items():
        current_path_map = {}
        if paths_map1.get(key) is not None:
            current_path_map = paths_map1[key]
        current_path_map = current_path_map | value
        paths_map1[key] = current_path_map
    return paths_map1


def generate_paths_from_data(data: dict | list, path: str | None = "root") -> dict:
    """Generate a dictionary representing paths and data types from a nested JSON structure.

    This function recursively traverses a nested JSON structure ('data') and builds
    a dictionary ('paths_map') where keys are paths and values are dictionaries
    containing keys and their corresponding data types.

    Args:
        data (dict or list): The nested JSON structure to traverse.
        path (str, optional): The current path (used for recursion). Default is 'root'.

    Returns:
        dict: A dictionary representing paths and data types.

    """
    paths_map: dict = {}
    if isinstance(data, list):
        for _ in data:
            paths_map = merge_path_values(paths_map, generate_paths_from_data(_, path=path))
    if isinstance(data, dict):
        key_to_type_map = {}
        for key, value in data.items():
            key_to_type_map[key] = type(value).__name__
            if key_to_type_map[key] == "dict":
                sub_path = f"{path}/{key}"
                paths_map = merge_path_values(
                    paths_map, generate_paths_from_data(data=value, path=sub_path)
                )
            if key_to_type_map[key] == "list":
                for _ in value:
                    if isinstance(_, dict):
                        key_to_type_map[key] = "list_dict"
                        sub_path = f"{path}/{key}"
                        paths_map = merge_path_values(
                            paths_map, generate_paths_from_data(data=_, path=sub_path)
                        )
        paths_map[path] = key_to_type_map
    return paths_map


def _get_schema(data: dict | list) -> dict[str, EntitySchema] | None:
    """Get the schema of an entity."""
    if not data:
        return None
    paths_map = generate_paths_from_data(data=data)
    path_to_schema_map = {}
    for path, key_to_type_map in paths_map.items():
        schema_paths = []
        for _key, _type in key_to_type_map.items():
            schema_paths.append(
                EntityPath(
                    path=_key,
                    is_relation=_type in ("dict", "list_dict"),
                    is_single_value=_type not in ("list", "list_dict"),
                )
            )
        schema = EntitySchema(
            type_uri="",
            paths=schema_paths,
        )
        path_to_schema_map[path] = schema
    return path_to_schema_map


def extend_path_list(path_to_entities: dict, sub_path_to_entities: dict) -> None:
    """Extend a dictionary of paths to entities by merging with another.

    This function takes two dictionaries, `path_to_entities` and `sub_path_to_entities`,
    representing paths and lists of entities. It extends the lists of entities for each
    path in `path_to_entities` by combining them with corresponding lists in
    `sub_path_to_entities`.

    Args:
        path_to_entities (dict): The main dictionary of paths to entities.
        sub_path_to_entities (dict): The dictionary of additional paths to entities.

    Returns:
        None: The result is modified in-place. `path_to_entities` is extended with
        entities from `sub_path_to_entities`.

    """
    for key, sub_entities in sub_path_to_entities.items():
        entities = path_to_entities.get(key, [])
        entities.extend(sub_entities)
        path_to_entities[key] = entities


def _get_entity(
    path_from_root: str,
    path_to_schema_map: dict,
    data: dict,
) -> dict:
    """Get an entity based on the schema and data."""
    path_to_entities: dict = {}
    entity_uri = f"urn:x-ulid:{ULID()}"
    values = []
    schema = path_to_schema_map[path_from_root]
    for _ in schema.paths:
        if data.get(_.path) is None:
            values.append([""])
        elif not _.is_relation:
            values.append(
                [f"{data.get(_.path)}"]
                if _.is_single_value
                else [f"{_v}" for _v in data.get(_.path)]  # type: ignore[union-attr]
            )
        else:
            _data: list[dict] = [data.get(_.path)] if _.is_single_value else data.get(_.path)  # type: ignore[assignment,list-item]
            sub_entities_uri = []
            for _v in _data:
                sub_entity_path = f"{path_from_root}/{_.path}"
                sub_path_to_entities = _get_entity(
                    path_from_root=sub_entity_path,
                    path_to_schema_map=path_to_schema_map,
                    data=_v,
                )
                sub_entity = sub_path_to_entities[sub_entity_path].pop()
                sub_entities_uri.append(sub_entity.uri)
                sub_path_to_entities[sub_entity_path].append(sub_entity)
                extend_path_list(path_to_entities, sub_path_to_entities)
            values.append(sub_entities_uri)
    entity = Entity(uri=entity_uri, values=values)
    entities = path_to_entities.get(path_from_root, [])
    entities.append(entity)
    path_to_entities[path_from_root] = entities
    return path_to_entities


def _get_entities(
    data: dict | list,
    path_to_schema_map: dict[str, EntitySchema],
) -> dict[str, list[Entity]]:
    """Get entities based on the schema, data, and sub-entities."""
    path_to_entities: dict[str, list[Entity]] = {}
    if isinstance(data, list):
        for _ in data:
            sub_path_to_entities = _get_entity(
                path_from_root="root", path_to_schema_map=path_to_schema_map, data=_
            )
            extend_path_list(path_to_entities, sub_path_to_entities)
    else:
        path_to_entities = _get_entity(
            path_from_root="root",
            path_to_schema_map=path_to_schema_map,
            data=data,
        )
    return path_to_entities


def build_entities_from_data(data: dict | list) -> Entities | None:
    """Get entities from a data object."""
    path_to_schema_map = _get_schema(data)
    if not path_to_schema_map:
        return None
    path_to_entities = _get_entities(
        data=data,
        path_to_schema_map=path_to_schema_map,
    )
    return Entities(
        entities=iter(path_to_entities.get("root")),  # type: ignore[arg-type]
        schema=path_to_schema_map["root"],
        sub_entities=[
            Entities(entities=iter(value), schema=path_to_schema_map[key])
            for key, value in path_to_entities.items()
            if key != "root"
        ],
    )
