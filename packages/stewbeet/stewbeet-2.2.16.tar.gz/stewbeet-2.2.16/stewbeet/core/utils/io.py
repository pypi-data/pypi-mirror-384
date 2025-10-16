
# Imports
import os
from typing import Any, TypeVar, cast

from beet import Function, JsonFile, NamespaceContainer, NamespaceProxy, TagFile, Texture
from beet.core.utils import JsonDict
from stouputils.collections import unique_list
from stouputils.io import super_json_dump, super_json_load

from ..__memory__ import Mem

# Constants
JsonFileT = TypeVar('JsonFileT', bound=JsonFile)

# Functions
def write_tag(path: str, tag_type: NamespaceProxy[Any] | NamespaceContainer[Any], values: list[Any] | None = None, prepend: bool = False) -> None:
	""" Write a function tag at the given path.

	Args:
		path        (str):  The path to the function tag (ex: "namespace:something" for 'data/namespace/tags/function/something.json')
		tag_type    (NamespaceProxy[TagFile]): The tag type to write to (ex: ctx.data.function_tags)
		values      (list[Any] | None): The values to add to the tag
		prepend     (bool): If the values should be prepended instead of appended
	"""
	if path.endswith(".json"):
		path = path[:-len(".json")]
	tag: TagFile = tag_type.setdefault(path)
	data: JsonDict = tag.data
	if not data.get("values"):
		data["values"] = values or []

	if prepend:
		data["values"] = (values or []) + data["values"]
	else:
		data["values"].extend(values or [])
	data["values"] = unique_list(data["values"])
	tag.encoder = super_json_dump

def write_function_tag(path: str, functions: list[Any] | None = None, prepend: bool = False) -> None:
	""" Write a function tag at the given path.

	Args:
		path        (str):  The path to the function tag (ex: "namespace:something" for 'data/namespace/tags/function/something.json')
		functions   (list[Any] | None): The functions to add to the tag
		prepend     (bool): If the functions should be prepended instead of appended
	"""
	write_tag(path, Mem.ctx.data.function_tags, functions, prepend)


def read_function(path: str) -> str:
	""" Read the content of a function at the given path.

	Args:
		path (str): The path to the function (ex: "namespace:folder/function_name")

	Returns:
		str: The content of the function
	"""
	if path.endswith(".mcfunction"):
		path = path[:-len(".mcfunction")]
	return Mem.ctx.data.functions[path].text


def write_function(path: str, content: str, overwrite: bool = False, prepend: bool = False, tags: list[str] | None = None) -> None:
	""" Write the content to the function at the given path.

	Args:
		path            (str):  The path to the function (ex: "namespace:folder/function_name")
		content         (str):  The content to write
		overwrite       (bool): If the file should be overwritten (default: Append the content)
		prepend         (bool): If the content should be prepended instead of appended (not used if overwrite is True)
		tags            (list[str] | None): The function tags to add to the function (ex: ["namespace:something"] for 'data/namespace/tags/function/something.json')
	"""
	if path.endswith(".mcfunction"):
		path = path[:-len(".mcfunction")]
	if overwrite:
		Mem.ctx.data.functions[path] = Function(content)
	else:
		if prepend:
			Mem.ctx.data.functions.setdefault(path).prepend(content)
		else:
			Mem.ctx.data.functions.setdefault(path).append(content)
	if tags:
		for tag in tags:
			write_function_tag(tag, [path], prepend)


def write_load_file(content: str, overwrite: bool = False, prepend: bool = False, tags: list[str] | None = None) -> None:
	""" Write the content to the load file

	Args:
		content     (str):  The content to write
		overwrite   (bool): If the file should be overwritten (default: Append the content)
		prepend     (bool): If the content should be prepended instead of appended (not used if overwrite is True)
		tags        (list[str] | None): The function tags to add to the function (ex: ["namespace:something"] for 'data/namespace/tags/function/something.json')
	"""
	write_function(f"{Mem.ctx.project_id}:v{Mem.ctx.project_version}/load/confirm_load", content, overwrite, prepend, tags)


def write_tick_file(content: str, overwrite: bool = False, prepend: bool = False, tags: list[str] | None = None) -> None:
	""" Write the content to the tick file

	Args:
		content     (str):  The content to write
		overwrite   (bool): If the file should be overwritten (default: Append the content)
		prepend     (bool): If the content should be prepended instead of appended (not used if overwrite is True)
		tags        (list[str] | None): The function tags to add to the function (ex: ["namespace:something"] for 'data/namespace/tags/function/something.json')
	"""
	write_function(f"{Mem.ctx.project_id}:v{Mem.ctx.project_version}/tick", content, overwrite, prepend, tags)


def write_versioned_function(path: str, content: str, overwrite: bool = False, prepend: bool = False, tags: list[str] | None = None) -> None:
	""" Write the content to a versioned function at the given path.

	Args:
		path            (str):  The path to the function (ex: "folder/function_name")
		content         (str):  The content to write
		overwrite       (bool): If the file should be overwritten (default: Append the content)
		prepend         (bool): If the content should be prepended instead of appended (not used if overwrite is True)
		tags            (list[str] | None): The function tags to add to the function (ex: ["namespace:something"] for 'data/namespace/tags/function/something.json')
	"""
	write_function(f"{Mem.ctx.project_id}:v{Mem.ctx.project_version}/{path}", content, overwrite, prepend, tags)


# Merge two dict recuirsively
def super_merge_dict(dict1: JsonDict, dict2: JsonDict) -> JsonDict:
	""" Merge the two dictionnaries recursively without modifying originals
	Args:
		dict1 (dict): The first dictionnary
		dict2 (dict): The second dictionnary
	Returns:
		dict: The merged dictionnary
	"""
	# Copy first dictionnary
	new_dict: JsonDict = {}
	for key, value in dict1.items():
		new_dict[key] = value

	# For each key of the second dictionnary,
	for key, value in dict2.items():

		# If key exists in dict1, and both values are also dict, merge recursively
		if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
			new_dict[key] = super_merge_dict(dict1[key], cast(JsonDict, value))

		# Else if it's a list, merge it
		elif key in dict1 and isinstance(dict1[key], list) and isinstance(value, list):
			new_dict[key] = dict1[key] + value
			if not any(isinstance(x, dict) for x in new_dict[key]):
				new_dict[key] = unique_list(new_dict[key])

		# Else, just overwrite or add value
		else:
			new_dict[key] = value

	# Return the new dict
	return new_dict


# Set the JSON encoder to super_json_dump for a JsonFile object
def set_json_encoder(obj: JsonFileT, max_level: int | None = None, indent: str | int = '\t') -> JsonFileT:
	""" Set the encoder of the given object to super_json_dump

	Args:
		obj			(JsonFile):		The object to set the encoder for
		max_level	(int | None):	The maximum level of the JSON dump, or None for default behavior
		indent		(str | int):	The indentation character (default: '\t')
	Returns:
		JsonFile: The object with the encoder set
	"""
	if max_level is None:
		obj.encoder = lambda x: super_json_dump(x, indent=indent)
	else:
		obj.encoder = lambda x: super_json_dump(x, max_level=max_level, indent=indent)
	return obj


# Create a texture object with mcmeta if found
def texture_mcmeta(source_path: str) -> Texture:
	""" Create a Texture object with mcmeta if found

	Args:
		source_path (str): The path to the texture (ex: "assets/textures/texture_name.png")
	Returns:
		Texture: The texture object
	"""
	mcmeta_path: str = f"{source_path}.mcmeta"
	if os.path.exists(mcmeta_path):
		return Texture(source_path=source_path, mcmeta=super_json_load(mcmeta_path))
	return Texture(source_path=source_path)

