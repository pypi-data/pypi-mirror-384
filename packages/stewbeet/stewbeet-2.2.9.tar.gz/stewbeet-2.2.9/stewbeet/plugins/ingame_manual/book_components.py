"""
Handles generation of book components and content
"""
import os

from beet.core.utils import JsonDict, TextComponent
from PIL import Image
from stouputils.print import error, warning

from ...core.__memory__ import Mem
from ...core.ingredients import ingr_to_id
from .image_utils import generate_high_res_font
from .shared_import import NONE_FONT, SharedMemory, get_page_number


# Call the previous function
def high_res_font_from_ingredient(ingredient: str | JsonDict, count: int = 1) -> str:
	""" Generate the high res font to display in the manual for the ingredient

	Args:
		ingredient	(str|dict):	The ingredient, ex: "adamantium_fragment" or {"item": "minecraft:stick"} or {"components": {"custom_data": {"iyc": {"adamantium_fragment": true}}}}
		count		(int):		The count of the item
	Returns:
		str: The font to the generated texture
	"""
	# Decode the ingredient
	if isinstance(ingredient, dict):
		ingr_str: str = ingr_to_id(ingredient, add_namespace = True)
	else:
		ingr_str = ingredient

	# Get the item image
	if ':' in ingr_str:
		image_path = f"{SharedMemory.cache_path}/items/{ingr_str.replace(':', '/')}.png"
		if not os.path.exists(image_path):
			warning(f"Missing texture at '{image_path}', using placeholder texture")
			item_image = Image.new("RGBA", (16, 16), (255, 255, 255, 0))  # Placeholder image
		else:
			item_image = Image.open(image_path)
		ingr_str = ingr_str.split(":")[1]
	else:
		path: str = f"{SharedMemory.cache_path}/items/{Mem.ctx.project_id}/{ingr_str}.png"
		if not os.path.exists(path):
			warning(f"Missing texture at '{path}', using placeholder texture")
			item_image = Image.new("RGBA", (16, 16), (255, 255, 255, 0))  # Placeholder image
		else:
			item_image = Image.open(path)

	# Generate the high res font
	return generate_high_res_font(ingr_str, item_image, count)


# Convert ingredient to formatted JSON for book
def get_item_component(ingredient: str | JsonDict, only_those_components: list[str] | None = None, count: int = 1, add_change_page: bool = True) -> JsonDict:
	""" Generate item hover text for a craft ingredient
	Args:
		ingredient (dict|str): The ingredient
			ex: {'components': {'custom_data': {'iyc': {'adamantium_fragment': True}}}}
			ex: {'item': 'minecraft:stick'}
			ex: "adamantium_fragment"	# Only available for the datapack items
	Returns:
		TextComponent:
			ex: {"text":NONE_FONT,"color":"white","hover_event":{"action":"show_item","id":"minecraft:command_block", "components": {...}},"click_event":{"action":"change_page","value":"8"}}
			ex: {"text":NONE_FONT,"color":"white","hover_event":{"action":"show_item","id":"minecraft:stick"}}
	"""
	if only_those_components is None:
		only_those_components = []

	# Get the item id
	formatted: TextComponent = {
		"text": NONE_FONT,
		"hover_event": {
			"action": "show_item",
			"id": "",  # Inline contents field
			"components": {}  # Will be added if needed
		}
	}

	if isinstance(ingredient, dict) and ingredient.get("item"):
		formatted["hover_event"]["id"] = ingredient["item"]
	else:
		# Get the item in the definitions
		if isinstance(ingredient, str):
			id = ingredient
			item: JsonDict = Mem.definitions[ingredient]
		else:
			item: JsonDict = {}
			custom_data: JsonDict = ingredient["components"]["minecraft:custom_data"]
			id = ingr_to_id(ingredient, add_namespace = False)
			if custom_data.get(Mem.ctx.project_id):
				item = Mem.definitions.get(id, {})
			else:
				ns = next(iter(custom_data.keys())) + ":"
				for data in custom_data.values():
					item = Mem.external_definitions.get(ns + next(iter(data.keys())), {})
					if item:
						break
		if not item:
			error("Item not found in definitions or external definitions: " + str(ingredient))

		# Copy id and components
		formatted["hover_event"]["id"] = item["id"].replace("minecraft:", "")
		components = {}
		if only_those_components:
			for key in only_those_components:
				if key in item:
					components[key] = item[key]
		else:
			for key, value in item.items():
				if key in SharedMemory.components_to_include:
					components[key] = value
		formatted["hover_event"]["components"] = components

		# If item is from my datapack, get its page number
		if add_change_page:
			page_number = get_page_number(id)
			if page_number != -1:
				formatted["click_event"] = {
					"action": "change_page",
					"page": page_number
				}

	# High resolution
	if SharedMemory.high_resolution:
		formatted["text"] = high_res_font_from_ingredient(ingredient, count)

	# Return
	return formatted

