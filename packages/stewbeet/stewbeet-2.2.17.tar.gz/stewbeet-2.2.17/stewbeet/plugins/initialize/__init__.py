
# Imports
import os
from pathlib import Path
from typing import Any

from beet import Context, Pack
from beet.core.utils import JsonDict, TextComponent
from box import Box
from stouputils import relative_path
from stouputils.decorators import measure_time
from stouputils.io import super_json_dump
from stouputils.print import warning

from ...core import Mem
from ...core.constants import MORE_ASSETS_PACK_FORMATS, MORE_DATA_PACK_FORMATS, MORE_DATA_VERSIONS
from .source_lore_font import find_pack_png, prepare_source_lore_font


# Main entry point
@measure_time(message="Total execution time", is_generator=True)
def beet_default(ctx: Context):

	# Assertions
	assert ctx.project_id, "Project ID must be set in the project configuration."

	# Store the Box object in ctx for access throughout the codebase
	meta_box: Box = Box(ctx.meta, default_box=True, default_box_attr={}) # type: ignore
	object.__setattr__(ctx, "meta", meta_box) # Bypass FrozenInstanceError
	Mem.ctx = ctx

	# Preprocess project description
	project_description: TextComponent = Mem.ctx.meta.get("stewbeet", {}).get("project_description", "")
	if not project_description or project_description == "auto":
		# Use project name, version, and author to create a default description
		if not Mem.ctx.meta.get("stewbeet"):
			Mem.ctx.meta["stewbeet"] = {}
		if not Mem.ctx.meta.get("stewbeet", {}).get("project_description"):
			Mem.ctx.meta["stewbeet"]["project_description"] = f"{ctx.project_name} [{ctx.project_version}] by {ctx.project_author}"

	# Preprocess source lore
	source_lore: TextComponent = Mem.ctx.meta.get("stewbeet", {}).get("source_lore", "")
	if not source_lore or source_lore == "auto":
		if not find_pack_png():
			Mem.ctx.meta["stewbeet"]["source_lore"] = [{"text": ctx.project_name,"italic":True,"color":"blue"}]
		else:
			Mem.ctx.meta["stewbeet"]["source_lore"] = [{"text":"ICON"},{"text":f" {ctx.project_name}","italic":True,"color":"blue"}]
	Mem.ctx.meta["stewbeet"]["pack_icon_path"] = prepare_source_lore_font(Mem.ctx.meta.get("stewbeet", {}).get("source_lore", []))

	# Preprocess manual name
	manual_name: TextComponent = Mem.ctx.meta.get("stewbeet", {}).get("manual", {}).get("name", "")
	if not manual_name:
		Mem.ctx.meta["stewbeet"]["manual"]["name"] = f"{ctx.project_name} Manual"

	# Convert paths to relative ones
	object.__setattr__(ctx, "output_directory", relative_path(str(Mem.ctx.output_directory)))

	# Add missing pack format registries if not present, and data version
	ctx.data.pack_format_registry.update(MORE_DATA_PACK_FORMATS)
	ctx.assets.pack_format_registry.update(MORE_ASSETS_PACK_FORMATS)
	ctx.meta["data_version"] = MORE_DATA_VERSIONS
	if ctx.minecraft_version:
		tuple_version: tuple[int, ...] = tuple(int(x) for x in ctx.minecraft_version.split(".") if x.isdigit())
		ctx.data.pack_format = ctx.data.pack_format_registry.get(tuple_version, ctx.data.pack_format)
		ctx.assets.pack_format = ctx.assets.pack_format_registry.get(tuple_version, ctx.assets.pack_format)

	# Helper function to setup pack.mcmeta
	def setup_pack_mcmeta(pack: Pack[Any], pack_format: int):
		existing_mcmeta = pack.mcmeta.data or {}
		pack_mcmeta: JsonDict = {"pack": {}}
		pack_mcmeta.update(existing_mcmeta)
		pack_mcmeta["pack"].update(existing_mcmeta.get("pack", {}))
		pack_mcmeta["pack"]["pack_format"] = pack_format
		if (pack is ctx.data and pack_format >= 82) or (pack is ctx.assets and pack_format >= 65):
			pack_mcmeta["pack"]["min_format"] = pack_format
			pack_mcmeta["pack"]["max_format"] = 1000
		pack_mcmeta["pack"]["description"] = Mem.ctx.meta.get("stewbeet", {}).get("project_description", "")
		pack_mcmeta["id"] = Mem.ctx.project_id
		pack.mcmeta.data = pack_mcmeta
		pack.mcmeta.encoder = super_json_dump

	# Setup pack.mcmeta for both packs
	setup_pack_mcmeta(ctx.data, ctx.data.pack_format)
	setup_pack_mcmeta(ctx.assets, ctx.assets.pack_format)

	# Convert texture names if needed (from old legacy system)
	textures_folder: str = Mem.ctx.meta.get("stewbeet", {}).get("textures_folder", "")
	if textures_folder and Path(textures_folder).exists():
		REPLACEMENTS = {
			"_off": "",
			"_down": "_bottom",
			"_up": "_top",
			"_north": "_front",
			"_south": "_back",
			"_west": "_left",
			"_east": "_right",
		}

		# Get all texture files
		texture_files = [f for f in os.listdir(textures_folder) if f.endswith(('.png', '.jpg', '.jpeg', ".mcmeta"))]

		for file in texture_files:
			new_name = file.lower()
			for k, v in REPLACEMENTS.items():
				if k in file:
					new_name = new_name.replace(k, v)

			if new_name != file:
				old_path = Path(textures_folder) / file
				new_path = Path(textures_folder) / new_name
				if old_path.exists() and not new_path.exists():
					os.rename(old_path, new_path)
					warning(f"Renamed texture '{file}' to '{new_name}'")

	# Extend the datapack namespace with sorter files
	ctx.require("stewbeet.plugins.datapack.sorters.extend_datapack")

	# Yield message to indicate successful build
	yield

