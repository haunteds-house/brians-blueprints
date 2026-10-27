-- Headless acceptance fixture. Only declared raw-material/fluid interfaces
-- receive inputs. Production machines use the blueprint's actual power grid.
local config = storage.test_config
local force = game.forces.player
force.research_all_technologies()
for _, technology in pairs(force.technologies) do
  for _, effect in pairs(technology.prototype.effects) do
    if effect.type == "change-recipe-productivity" then
      technology.level = 1
      technology.researched = false
    end
  end
  local level = tonumber(technology.name:match("^inserter%-capacity%-bonus%-(%d+)$"))
  if level and level > 3 then technology.researched = false end
end

local surface = game.create_surface("bootstrap-acceptance", {
  width = 1024, height = 1024, water = 0,
  autoplace_settings = {entity = {treat_missing_as_default = false}}
})
surface.request_to_generate_chunks({0, 0}, 6)
surface.force_generate_chunk_requests()
local tiles = {}
for x = -32, 512 do
  for y = -32, 192 do
    tiles[#tiles + 1] = {name = "grass-1", position = {x, y}}
  end
end
surface.set_tiles(tiles)

local inventory = game.create_inventory(1)
assert(inventory[1].import_stack(storage.blueprint_string) == 0, "Blueprint import failed")
local expected = #inventory[1].get_blueprint_entities()
local ghosts = inventory[1].build_blueprint {
  surface = surface, force = force, position = {0, 0},
  force_build = true, build_mode = defines.build_mode.forced
}
for _, ghost in pairs(ghosts) do
  local revived = ghost.revive {raise_revive = false}
  assert(revived, "Failed to revive blueprint entity")
end
assert(#surface.find_entities_filtered {force = force} == expected,
       "Some blueprint entities were omitted during placement")

local feeders, fluids = {}, {}
for _, port in ipairs(config.item_ports) do
  local belt = surface.find_entity("fast-transport-belt", {port.x, port.y})
  assert(belt, "Missing declared belt input")
  feeders[#feeders + 1] = {entity = belt, item = port.item}
end
for _, port in ipairs(config.fluid_ports) do
  local pipe = surface.find_entity("pipe", {port.x, port.y})
  assert(pipe, "Missing declared fluid input")
  fluids[#fluids + 1] = {entity = pipe, name = port.fluid}
end

-- The fixture's generator is outside the factory and supplies ample electricity.
local power = surface.create_entity {
  name = "electric-energy-interface", position = {75, -12}, force = force
}
power.power_production = 1000000000
power.electric_buffer_size = 100000000000
power.energy = 100000000000
local inlet = surface.create_entity {
  name = "big-electric-pole", position = {73, -12}, force = force
}
local grid = assert(surface.find_entity("big-electric-pole", {73, 17}))
inlet.get_wire_connector(defines.wire_connector_id.pole_copper, true).connect_to(
  grid.get_wire_connector(defines.wire_connector_id.pole_copper, true))
assert(inlet.electric_network_id and inlet.electric_network_id == grid.electric_network_id,
       "Power inlet is not connected to the blueprint grid")

local machines = surface.find_entities_filtered {type = "assembling-machine"}
local labs = surface.find_entities_filtered {name = "lab"}
local statistics = force.get_item_production_statistics(surface)
local warmup = config.warmup_minutes * 3600
local sample = config.sample_minutes * 3600
local started = game.tick
local baseline
local status_names = {}
for name, value in pairs(defines.entity_status) do status_names[value] = name end
local recipe_counts = {}
for _, machine in pairs(machines) do
  local recipe = machine.get_recipe()
  if recipe then recipe_counts[recipe.name] = (recipe_counts[recipe.name] or 0) + 1 end
end
for name, count in pairs(config.science_counts) do
  assert(recipe_counts[name] == count, "Science machine count changed: " .. name)
end

local function totals()
  local result = {}
  for name, _ in pairs(config.science_counts) do
    result[name] = statistics.get_input_count(name)
  end
  return result
end

local function diagnostics()
  local result = {}
  for _, machine in pairs(machines) do
    local recipe = machine.get_recipe()
    if recipe then
      result[#result + 1] = {
        recipe = recipe.name, position = machine.position, status = machine.status,
        status_name = status_names[machine.status],
        recipe_enabled = force.recipes[recipe.name].enabled,
        energy = machine.energy,
        input = machine.get_inventory(defines.inventory.crafter_input).get_contents(),
        fluids = machine.get_fluid_contents(), crafts = machine.products_finished
      }
    end
  end
  return result
end

script.on_event(defines.events.on_tick, function()
  local ok, message = pcall(function()
    local elapsed = game.tick - started
    for _, feeder in pairs(feeders) do
      for lane = 1, 2 do
        feeder.entity.get_transport_line(lane).insert_at_back {name = feeder.item, count = 1}
      end
    end
    if elapsed % 30 == 0 then
      for _, fluid in pairs(fluids) do
        fluid.entity.set_fluid_segment_fluid(1, {name = fluid.name, amount = 100000})
      end
      for _, lab in pairs(labs) do lab.clear_items_inside() end
    end
    if elapsed == warmup then baseline = totals() end
    if elapsed % 3600 == 0 then
      helpers.write_file("bootstrap-progress.json", helpers.table_to_json {
        elapsed_ticks = elapsed, totals = totals(), machines = diagnostics()
      })
    end
    if elapsed >= warmup + sample then
      local finish = totals()
      local rates, produced = {}, {}
      local passed = true
      for name, count in pairs(finish) do
        produced[name] = count - baseline[name]
        rates[name] = produced[name] / config.sample_minutes
        if rates[name] < 44.5 then passed = false end
      end
      local unpowered = 0
      for _, machine in pairs(machines) do
        if machine.status == defines.entity_status.no_power then unpowered = unpowered + 1 end
      end
      if unpowered > 0 then passed = false end
      helpers.write_file("bootstrap-result.json", helpers.table_to_json {
        engine_version = script.active_mods.base,
        official_expansion = script.active_mods["space-age"],
        passed = passed, warmup_minutes = config.warmup_minutes,
        sample_minutes = config.sample_minutes, packs_per_minute = rates,
        produced_packs = produced, recipe_counts = recipe_counts,
        declared_item_inputs = config.item_ports,
        declared_fluid_inputs = config.fluid_ports,
        unpowered_machines = unpowered, blueprint_entity_count = expected,
        recipe_productivity_research = false, inserter_capacity_max = 3,
        machines = diagnostics()
      })
      script.on_event(defines.events.on_tick, nil)
      game.tick_paused = true
    end
  end)
  if not ok then
    helpers.write_file("bootstrap-result.json", helpers.table_to_json {passed = false, error = message})
    script.on_event(defines.events.on_tick, nil)
    game.tick_paused = true
  end
end)
game.speed = 100
game.tick_paused = false
