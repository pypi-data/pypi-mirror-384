
# ruff: noqa: RUF012
# Imports
from __future__ import annotations

from typing import cast

from beet.core.utils import JsonDict, TextComponent
from box import Box

from ..__memory__ import Mem


# Add item model component
def add_item_model_component(black_list: list[str] | None = None) -> None:
	""" Add an item model component to all items in the definitions.

	Args:
		black_list			(list[str]):	The list of items to ignore.
		ignore_paintings	(bool):			Whether to ignore items that are paintings (have PAINTING_DATA).
	"""
	if black_list is None:
		black_list = []
	for item, data in Mem.definitions.items():
		if item in black_list or data.get("item_model", None) is not None:
			continue
		data["item_model"] = f"{Mem.ctx.project_id}:{item}"
	return

# Add item name and lore
def add_item_name_and_lore_if_missing(is_external: bool = False, black_list: list[str] | None = None) -> None:
	""" Add item name and lore to all items in the definitions if they are missing.

	Args:
		is_external	(bool):				Whether the definitions is the external one or not (meaning the namespace is in the item name).
		black_list	(list[str]):		The list of items to ignore.
	"""
	# Load the source lore
	if black_list is None:
		black_list = []
	source_lore: TextComponent = Mem.ctx.meta.get("stewbeet", {}).get("source_lore", {})

	# For each item, add item name and lore if missing (if not in black_list)
	for item, data in Mem.definitions.items():
		if item in black_list:
			continue

		# Add item name if none
		if not data.get("item_name"):
			if not is_external:
				item_str: str = item.replace("_"," ").title()
			else:
				item_str: str = item.split(":")[-1].replace("_"," ").title()
			data["item_name"] = {"text": item_str}	# Use a TextComponent to allow auto.lang_file to work properly

		# Apply namespaced lore if none
		if not data.get("lore"):
			data["lore"] = cast(list[TextComponent], [])

		# If item is not external,
		if not is_external:

			# Add the source lore ONLY if not already present
			if source_lore not in data["lore"]:
				data["lore"].append(source_lore)

		# If item is external, add the source lore to the item lore (without ICON)
		else:
			# Extract the namespace
			titled_namespace: str = item.split(":")[0].replace("_"," ").title()

			# Create the new namespace lore with the titled namespace
			new_source_lore: JsonDict = {"text": titled_namespace, "italic": True, "color": "blue"}

			# Add the namespace lore ONLY if not already present
			if new_source_lore not in data["lore"]:
				data["lore"].append(new_source_lore)
	return

# Add private custom data for namespace
def add_private_custom_data_for_namespace(is_external: bool = False) -> None:
	""" Add private custom data for namespace to all items in the definitions if they are missing.

	Args:
		is_external	(bool):				Whether the definitions is the external one or not (meaning the namespace is in the item name).
	"""
	for item, data in Mem.definitions.items():
		if not data.get("custom_data"):
			data["custom_data"] = cast(JsonDict, {})
		if is_external and ":" in item:
			ns, id = item.split(":")
		else:
			ns, id = Mem.ctx.project_id, item
		if not data["custom_data"].get(ns):
			data["custom_data"][ns] = {}
		data["custom_data"][ns][id] = True
	return

# Smithed ignore convention
def add_smithed_ignore_vanilla_behaviours_convention() -> None:
	""" Add smithed convention to all items in the definitions if they are missing.

	Refer to https://wiki.smithed.dev/conventions/tag-specification/#custom-items for more information.
	"""
	for data in Mem.definitions.values():
		data["custom_data"] = Box(data.get("custom_data", {}), default_box=True, default_box_attr={}, default_box_create_on_get=True)
		data["custom_data"].smithed.ignore.functionality = True # pyright: ignore[reportUnknownMemberType]
		data["custom_data"].smithed.ignore.crafting = True # pyright: ignore[reportUnknownMemberType]

# Set manual components
def set_manual_components(white_list: list[str]) -> None:
	""" Override the components to include in the manual when hovering items.

	Args:
		white_list	(list[str]):	The list of components to include.
	"""
	if not white_list:
		return
	from ...plugins.ingame_manual.shared_import import SharedMemory
	SharedMemory.components_to_include = white_list

