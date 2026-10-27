-- Test reusable production and unloading modules in disposable, separate surfaces.
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

local function attach_power(surface, pole_position, generator_position, grid_position)
  local inlet = surface.create_entity {
    name = "medium-electric-pole", position = pole_position, force = force
  }
  local generator = surface.create_entity {
    name = "electric-energy-interface", position = generator_position, force = force
  }
  assert(inlet and generator, "Could not place test power supply")
  generator.power_production = 1000000000
  generator.electric_buffer_size = 100000000000
  generator.energy = 100000000000
  local grid = assert(surface.find_entity("medium-electric-pole", grid_position) or
    surface.find_entity("small-electric-pole", grid_position))
  inlet.get_wire_connector(defines.wire_connector_id.pole_copper, true).connect_to(
    grid.get_wire_connector(defines.wire_connector_id.pole_copper, true))
  assert(inlet.electric_network_id == grid.electric_network_id, "Disconnected test supply")
end

local function make_train(surface, fluid)
  local front = surface.create_entity {
    name = "locomotive", position = {40, 29}, direction = 4, force = force
  }
  assert(front, "Locomotive does not fit the reference station")
  local back = assert(surface.create_entity {
    name = "locomotive", position = {33, 29}, direction = 4, force = force
  })
  for _, locomotive in pairs({front, back}) do
    locomotive.get_inventory(defines.inventory.fuel).insert {name = "coal", count = 50}
  end
  local wagons = {}
  for _, x in ipairs({26, 19}) do
    local wagon = assert(surface.create_entity {
      name = fluid and "fluid-wagon" or "cargo-wagon", position = {x, 29},
      direction = 4, force = force
    }, "Wagon does not fit the station")
    wagons[#wagons + 1] = wagon
  end
  assert(#front.train.carriages == 4, "Reference 2-2 train did not couple")
  if fluid then
    local stop = surface.find_entities_filtered {name = "train-stop"}[1]
    front.train.schedule = {current = 1, records = {{station = stop.backer_name,
      wait_conditions = {{type = "time", compare_type = "and", ticks = 100000}}}}}
    front.train.manual_mode = false
  else
    front.train.manual_mode = true
  end
  return wagons, front.train
end

local cases = {}
for index, entry in ipairs(config.cases) do
  local surface = game.create_surface("bootstrap-module-" .. index, {
    width = 2048, height = 1024, water = 0,
    autoplace_settings = {entity = {treat_missing_as_default = false}}
  })
  local inventory = game.create_inventory(1)
  assert(inventory[1].import_stack(entry.blueprint) == 0, "Module import failed: " .. entry.name)
  local entities = inventory[1].get_blueprint_entities()
  local min_x, min_y, max_x, max_y = 0, 0, 32, 32
  for _, entity in pairs(entities) do
    min_x = math.min(min_x, entity.position.x - 10)
    min_y = math.min(min_y, entity.position.y - 10)
    max_x = math.max(max_x, entity.position.x + 10)
    max_y = math.max(max_y, entity.position.y + 10)
  end
  surface.request_to_generate_chunks({(min_x + max_x) / 2, (min_y + max_y) / 2},
    math.ceil(math.max(max_x - min_x, max_y - min_y) / 64) + 2)
  surface.force_generate_chunk_requests()
  local tiles = {}
  for x = math.floor(min_x), math.ceil(max_x) do
    for y = math.floor(min_y), math.ceil(max_y) do
      tiles[#tiles + 1] = {name = "grass-1", position = {x, y}}
    end
  end
  surface.set_tiles(tiles)
  local ghosts = inventory[1].build_blueprint {
    surface = surface, force = force, position = {0, 0},
    force_build = true, build_mode = defines.build_mode.forced
  }
  local failed = {}
  for _, ghost in pairs(ghosts) do
    if ghost.valid then
      local name, position = ghost.ghost_name, ghost.position
      if not ghost.revive {raise_revive = false} then
        failed[#failed + 1] = {name = name, position = position}
      end
    end
  end
  -- Rolling stock can precede its rails in the source entity order.
  for _, ghost in pairs(ghosts) do
    if ghost.valid and ghost.type == "entity-ghost" then ghost.revive {raise_revive = false} end
  end
  failed = {}
  for _, ghost in pairs(ghosts) do
    if ghost.valid and ghost.type == "entity-ghost" then
      failed[#failed + 1] = {name = ghost.ghost_name, position = ghost.position}
    end
  end
  local expected_names, actual_names = {}, {}
  for _, entity in pairs(entities) do
    expected_names[entity.name] = (expected_names[entity.name] or 0) + 1
  end
  for _, entity in pairs(surface.find_entities_filtered {force = force}) do
    actual_names[entity.name] = (actual_names[entity.name] or 0) + 1
  end
  local differences = {}
  for name, count in pairs(expected_names) do
    if count ~= (actual_names[name] or 0) then
      differences[name] = {expected = count, actual = actual_names[name] or 0}
    end
  end
  local built = #surface.find_entities_filtered {force = force}
  local case = {entry = entry, surface = surface, expected = #entities,
    built = built, failed = failed, differences = differences, removed = 0, refill = {0, 0}, sinks = {}, baseline = 0}
  if entry.kind ~= "placement" then
    assert(#failed == 0 and built == #entities, "Module placement mismatch: " .. entry.name)
  end
  if entry.kind == "placement" and next(differences) then
    local missing = {}
    for _, entity in pairs(entities) do
      if not surface.find_entity(entity.name, entity.position) then
        local near = {}
        for _, other in pairs(surface.find_entities_filtered {position = entity.position, radius = 1}) do
          near[#near + 1] = {name = other.name, position = other.position}
        end
        missing[#missing + 1] = {name = entity.name, position = entity.position, near = near}
      end
    end
    helpers.write_file("bootstrap-missing.json", helpers.table_to_json(missing))
  end
  inventory.destroy()
  if entry.kind == "smelting" then
    attach_power(surface, {-2.5, 5.5}, {-5.5, 5.5}, {2.5, 5.5})
    case.feeder = assert(surface.find_entity("fast-transport-belt", {39.5, .5}))
    for row = 0, entry.rows - 1 do
      case.sinks[#case.sinks + 1] = assert(surface.find_entity(
        "fast-transport-belt", {.5, 6.5 + row * 8}))
    end
  elseif entry.kind == "solid-import" then
    attach_power(surface, {32.5, 34.5}, {34.5, 36.5}, {29.5, 32.5})
    case.wagons, case.train = make_train(surface, false)
    for _, x in ipairs({18.5, 22.5, 27.5}) do
      case.sinks[#case.sinks + 1] = assert(surface.find_entity("fast-transport-belt", {x, 63.5}))
    end
  elseif entry.kind == "fluid-import" then
    attach_power(surface, {28.5, 34.5}, {30.5, 36.5}, {22.5, 30.5})
    case.wagons, case.train = make_train(surface, true)
    case.outlet = assert(surface.find_entity("pipe", {22.5, 63.5}))
  elseif entry.kind == "uranium" then
    attach_power(surface, {3.5, 1.5}, {1.5, 1.5}, {7.5, 4.5})
    case.feeder = assert(surface.find_entity("transport-belt", {10.5, .5}))
  elseif entry.kind == "solar" then
    attach_power(surface, {3.5, 3.5}, {1.5, 1.5}, {6.5, 6.5})
    case.input = assert(surface.find_entity("iron-chest", {8.5, 5.5})).get_inventory(defines.inventory.chest)
  end
  cases[#cases + 1] = case
end

local warmup = config.warmup_minutes * 3600
local sample = config.sample_minutes * 3600
local started = game.tick

local function produced(case)
  local stats = force.get_item_production_statistics(case.surface)
  if case.entry.kind == "smelting" then return stats.get_input_count(case.entry.product) end
  if case.entry.kind == "uranium" then
    return stats.get_input_count("uranium-235") + stats.get_input_count("uranium-238")
  end
  if case.entry.kind == "solar" then return stats.get_input_count("solar-panel") end
  return case.removed
end

script.on_event(defines.events.on_tick, function()
  local ok, message = pcall(function()
    local elapsed = game.tick - started
    for _, case in ipairs(cases) do
      local kind = case.entry.kind
      if case.feeder then
        for lane = 1, 2 do
          case.feeder.get_transport_line(lane).insert_at_back {
            name = kind == "uranium" and "uranium-ore" or case.entry.ingredient, count = 1
          }
        end
      end
      for _, sink in pairs(case.sinks) do
        for lane = 1, 2 do
          local line = sink.get_transport_line(lane)
          local count = line.get_item_count()
          assert(count <= 4, "Sink measured more than a single belt tile")
          case.removed = case.removed + count
          line.clear()
        end
      end
      if kind == "solid-import" then
        for i, wagon in ipairs(case.wagons) do
          local added = wagon.get_inventory(defines.inventory.cargo_wagon).insert {
            name = "iron-ore", count = 4000
          }
          case.refill[i] = case.refill[i] + added
        end
      elseif kind == "fluid-import" then
        for i, wagon in ipairs(case.wagons) do
          local current = wagon.get_fluid(1)
          case.refill[i] = case.refill[i] + 50000 - (current and current.amount or 0)
          wagon.set_fluid(1, {name = "crude-oil", amount = 50000})
        end
        local fluid = case.outlet.get_fluid_segment_fluid(1)
        if fluid then case.removed = case.removed + fluid.amount end
        case.outlet.clear_fluid_segment_fluid(1)
      elseif kind == "solar" then
        if elapsed % 60 == 0 then
          for _, item in ipairs({"copper-plate", "steel-plate", "electronic-circuit"}) do
            case.input.insert {name = item, count = 10}
          end
        end
      end
      if elapsed == warmup then case.baseline = produced(case) end
    end
    if elapsed % 3600 == 0 then
      helpers.write_file("bootstrap-progress.json", helpers.table_to_json {elapsed_ticks = elapsed})
    end
    if elapsed >= warmup + sample then
      local results, passed = {}, true
      for _, case in ipairs(cases) do
        local rate = (produced(case) - case.baseline) / config.sample_minutes
        local kind = case.entry.kind
        local expected = case.entry.expected_rate or
          (kind == "solid-import" and 4200 or kind == "fluid-import" and 10800 or
           kind == "uranium" and 20 or kind == "solar" and 3 or 0)
        local good = rate >= expected * .98
        if kind == "solid-import" or kind == "fluid-import" then
          local initial = kind == "solid-import" and 2000 or 50000
          if case.refill[1] <= initial or case.refill[2] <= initial then good = false end
        end
        if kind == "placement" then good = case.built == case.expected end
        local diagnostics = {}
        if not good then
          passed = false
          for _, entity in pairs(case.surface.find_entities_filtered {
              type = {"assembling-machine", "inserter", "electric-pole"}, force = force}) do
            if #diagnostics < 12 then
              local status = "unknown"
              for key, value in pairs(defines.entity_status) do
                if entity.status == value then status = key end
              end
              diagnostics[#diagnostics + 1] = {name = entity.name, position = entity.position,
                status = status, energy = entity.energy,
                input = entity.type == "assembling-machine" and
                  entity.get_inventory(defines.inventory.crafter_input).get_contents() or nil}
            end
          end
        end
        results[#results + 1] = {name = case.entry.name, passed = good,
          rate_per_minute = rate, required_rate = expected,
          blueprint_entities = case.expected, placed_entities = case.built,
          supplied_per_wagon = case.wagons and case.refill or nil,
          diagnostics = not good and diagnostics or nil,
          placement_differences = next(case.differences) and case.differences or nil}
      end
      helpers.write_file("bootstrap-result.json", helpers.table_to_json {
        passed = passed, engine_version = script.active_mods.base,
        warmup_minutes = config.warmup_minutes, sample_minutes = config.sample_minutes,
        inserter_capacity_max = 3, cases = results,
        note = "Import throughput uses a continuously supplied stationary 2-2 train; travel time is excluded."
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
