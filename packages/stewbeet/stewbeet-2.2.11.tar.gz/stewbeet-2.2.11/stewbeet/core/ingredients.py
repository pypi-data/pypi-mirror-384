
# Imports
from typing import Any, cast

from beet import LootTable
from beet.core.utils import JsonDict
from stouputils.decorators import simple_cache
from stouputils.io import super_json_dump
from stouputils.print import error

from .__memory__ import Mem
from .constants import NOT_COMPONENTS, PULVERIZING

# Recipes constants
FURNACES_RECIPES_TYPES: tuple[str, ...] = ("smelting", "blasting", "smoking", "campfire_cooking")
CRAFTING_RECIPES_TYPES: tuple[str, ...] = ("crafting_shaped", "crafting_shapeless")
OTHER_RECIPES_TYPES: tuple[str, ...] = ("smithing_transform", "smithing_trim", "stonecutting")
UNUSED_RECIPES_TYPES: tuple[str, ...] = (
	"crafting_decorated_pot", "crafting_special_armordye", "crafting_special_bannerduplicate",
	"crafting_special_bookcloning", "crafting_special_firework_rocket", "crafting_special_firework_star",
	"crafting_special_firework_star_fade", "crafting_special_mapcloning", "crafting_special_mapextending",
	"crafting_special_repairitem", "crafting_special_shielddecoration", "crafting_special_tippedarrow",
	"crafting_transmute",
)
SPECIAL_RECIPES_TYPES: tuple[str, ...] = (PULVERIZING, )
ALL_RECIPES_TYPES: tuple[str, ...] = (*FURNACES_RECIPES_TYPES, *CRAFTING_RECIPES_TYPES, *OTHER_RECIPES_TYPES, *UNUSED_RECIPES_TYPES, *SPECIAL_RECIPES_TYPES)

# Function mainly used for definitions generation
@simple_cache
def ingr_repr(id: str, ns: str|None = None, count: int|None = None) -> JsonDict:
	""" Get the identity of the ingredient from its id for custom crafts
	Args:
		id		(str):		The id of the ingredient, ex: adamantium_fragment
		ns		(str|None):	The namespace of the ingredient (optional if 'id' argument is a vanilla item), ex: iyc
		count	(int|None):	The count of the ingredient (optional, used only when this ingredient format is a result item)
	Returns:
		str: The identity of the ingredient for custom crafts,
			ex: {"components":{"minecraft:custom_data":{"iyc":{"adamantium_fragment":True}}}}
			ex: {"item": "minecraft:stick"}
	"""
	if ":" in id:
		to_return: JsonDict = {"item": id}
	else:
		if ns is None:
			error(f"Namespace must be specified for custom ingredient '{id}', or you may be missing 'minecraft:'")
		to_return: JsonDict = {"components":{"minecraft:custom_data":{ns:{id:True}}}}
	if count is not None:
		to_return["count"] = count
	return to_return

@simple_cache
def item_to_id_ingr_repr(ingr: JsonDict) -> JsonDict:
	""" Replace the "item" key by "id" in an item ingredient representation
	Args:
		ingr (dict): The item ingredient, ex: {"item": "minecraft:stick"}
	Returns:
		dict: The item ingredient representation, ex: {"id": "minecraft:stick"}
	"""
	if ingr.get("item") is None:
		return ingr
	if "Slot" in ingr:
		r: JsonDict = {"Slot": ingr["Slot"], "id": ingr["item"]}
	else:
		r: JsonDict = {"id": ingr["item"]}
	copy: JsonDict = ingr.copy()
	copy.pop("item")
	r.update(copy)
	return r

# Mainly used for manual
@simple_cache
def ingr_to_id(ingredient: JsonDict, add_namespace: bool = True) -> str:
	""" Get the id from an ingredient dict
	Args:
		ingredient (dict): The ingredient dict
			ex: {"components":{"minecraft:custom_data":{iyc:{adamantium_ingot:True}}}}
			ex: {"item": "minecraft:stick"}
	Returns:
		str: The id of the ingredient, ex: "minecraft:stick" or "iyc:adamantium_ingot"
	"""
	if isinstance(ingredient, str):
		ingredient = {"item": ingredient}
	for k in ("item", "id"):
		if ingredient.get(k):
			if not add_namespace and ":" in ingredient[k]:
				return ingredient[k].split(":")[1]
			elif add_namespace and ":" not in ingredient[k]:
				return "minecraft:" + ingredient[k]
			return ingredient[k]

	custom_data: JsonDict = ingredient["components"]["minecraft:custom_data"]
	namespace: str = ""
	id: str = ""
	for cd_ns, cd_data in custom_data.items():
		if isinstance(cd_data, dict):
			cd_data = cast(JsonDict, cd_data)
			values: list[Any] = list(cd_data.values())
			if isinstance(values[0], bool):
				namespace = cd_ns
				id = next(iter(cd_data.keys()))
				break
	if not namespace:
		error(f"No namespace found in custom data: {custom_data}, ingredient: {ingredient}")
	if add_namespace:
		return namespace + ":" + id
	return id

# Mainly used for recipes
@simple_cache
def get_vanilla_item_id_from_ingredient(ingredient: JsonDict, add_namespace: bool = True) -> str:
	""" Get the id of the vanilla item from an ingredient dict
	Args:
		config (dict): The config dict
		ingredient (dict): The ingredient dict
			ex: {"item": "minecraft:stick"}
		add_namespace (bool): Whether to add the namespace to the id
	Returns:
		str: The id of the vanilla item, ex: "minecraft:stick"
	"""
	if isinstance(ingredient, str):
		ingredient = {"item": ingredient}
	ns, ingr_id = ingr_to_id(ingredient).split(":")
	if ns == Mem.ctx.project_id:
		if add_namespace:
			return Mem.definitions[ingr_id]["id"]
		return Mem.definitions[ingr_id]["id"].split(":")[1]
	elif ns == "minecraft":
		if add_namespace:
			return f"{ns}:{ingr_id}"
		return ingr_id
	else:
		if Mem.external_definitions.get(f"{ns}:{ingr_id}"):
			if add_namespace:
				return Mem.external_definitions[f"{ns}:{ingr_id}"]["id"]
			return Mem.external_definitions[f"{ns}:{ingr_id}"]["id"].split(":")[1]
		else:
			error(f"External item '{ns}:{ingr_id}' not found in the external definitions")
	return ""

# Used for recipes
@simple_cache
def get_item_from_ingredient(ingredient: JsonDict) -> JsonDict:
	""" Get the item dict from an ingredient dict
	Args:
		config (dict): The config dict
		ingredient (dict): The ingredient dict
			ex: {"item": "minecraft:stick"}
	Returns:
		dict: The item data dict, ex: {"id": "minecraft:stick", "count": 1}
	"""
	if isinstance(ingredient, str):
		ingredient = {"item": ingredient}
	ingr_id = ingr_to_id(ingredient)
	ns, id = ingr_id.split(":")

	# Get from internal definitions
	if ns == Mem.ctx.project_id:
		item_data: JsonDict = Mem.definitions[id].copy()
		result: JsonDict = {"id": item_data.pop("id"), "count": 1}

		# Add components
		for k, v in item_data.items():
			if k not in NOT_COMPONENTS:
				if result.get("components") is None:
					result["components"] = {}
				result["components"][f"minecraft:{k}"] = v
		return result

	# External definitions
	if Mem.external_definitions.get(ingr_id):
		item_data = Mem.external_definitions[ingr_id].copy()
		result = {"id": item_data.pop("id"), "count": 1}

		# Add components
		for k, v in item_data.items():
			if k not in NOT_COMPONENTS:
				if result.get("components") is None:
					result["components"] = {}
				result["components"][f"minecraft:{k}"] = v
		return result

	# Minecraft item
	if ns == "minecraft":
		return {"id": id, "count": 1}
	error(f"External item '{ingr_id}' not found in the external definitions")
	return {}


# Make a loot table
@simple_cache
def loot_table_from_ingredient(result_ingredient: JsonDict, result_count: int | dict) -> str:
	""" Get the loot table for an ingredient dict
	Args:
		result_ingredient (dict): The ingredient dict
			ex: {"item": "minecraft:stick"}
		result_count (int|dict): The count of the result item, can be an int or a dict for random counts
			ex: 1
			ex: {"type": "minecraft:uniform","min": 4,"max": 6}
	Returns:
		str: The loot table path, ex: "my_datapack:i/stick"
	"""

	# If item from this datapack
	item: str = ingr_to_id(result_ingredient)
	if item.startswith(Mem.ctx.project_id):
		item = item.split(":")[1]
		loot_table = f"{Mem.ctx.project_id}:i/{item}"
		if isinstance(result_count, int) and result_count > 1:
			loot_table += f"_x{result_count}"
		elif isinstance(result_count, dict):
			minimum = result_count.get("min", 1)
			maximum = result_count.get("max", 1)
			if maximum > 1:
				loot_table += f"_x{minimum}to{maximum}"
		return loot_table

	namespace, item = item.split(":")
	loot_table = f"{Mem.ctx.project_id}:recipes/{namespace}/{item}"
	if isinstance(result_count, int) and result_count > 1:
		loot_table += f"_x{result_count}"
	elif isinstance(result_count, dict):
		minimum = result_count.get("min", 1)
		maximum = result_count.get("max", 1)
		if maximum > 1:
			loot_table += f"_x{minimum}to{maximum}"

	# If item from another datapack, generate the loot table
	if namespace != "minecraft":
		file: JsonDict = {"pools":[{"rolls":1,"entries":[{"type":"minecraft:loot_table","value": f"{Mem.ctx.project_id}:external/{namespace}/{item}"}] }] }
	else:
		file: JsonDict = {"pools":[{"rolls":1,"entries":[{"type":"minecraft:item","name":f"{namespace}:{item}"}] }] }
	if (isinstance(result_count, int) and result_count > 1) or isinstance(result_count, dict):
		file["pools"][0]["entries"][0]["functions"] = [{"function": "minecraft:set_count","count": result_count}]

	Mem.ctx.data[loot_table] = LootTable(super_json_dump(file, max_level=9))
	return loot_table

@simple_cache
def get_ingredients_from_recipe(recipe: JsonDict) -> list[str]:
	""" Get the ingredients from a recipe dict
	Args:
		recipe (dict): The final recipe JSON dict, ex:

		{
			"type": "minecraft:crafting_shaped",
			"pattern": [...],
			"key": {...},
			"result": {...}
		}
	Returns:
		list[str]: The ingredients ids
	"""
	ingredients: list[str] = []
	if recipe.get("key"):
		for value in recipe["key"].values():
			ingredients.append(value)
	elif recipe.get("ingredients"):
		for ingr in recipe["ingredients"]:
			ingredients.append(ingr)
	elif recipe.get("ingredient"):
		ingredients.append(recipe["ingredient"])
	elif recipe.get("template"):
		ingredients.append(recipe["template"])
	return ingredients

