-- Real silo research using the separate annex, with finite pack inputs.
local force=game.forces.player
local function unlock(t)
  for _,p in pairs(t.prerequisites) do unlock(p) end
  t.researched=true
end
local technology=force.technologies['rocket-silo']
for _,p in pairs(technology.prerequisites) do unlock(p) end
unlock(force.technologies['electric-energy-distribution-1'])
unlock(force.technologies['fast-inserter'])
assert(not technology.researched)
local surface=game.create_surface('silo-research-test',{width=256,height=256,water=0,
  autoplace_settings={entity={treat_missing_as_default=false}}})
surface.request_to_generate_chunks({0,0},3);surface.force_generate_chunk_requests()
local tiles={}
for x=-16,48 do for y=-16,48 do tiles[#tiles+1]={name='grass-1',position={x,y}} end end
surface.set_tiles(tiles)
local inventory=game.create_inventory(1)
assert(inventory[1].import_stack(storage.blueprint_string)==0)
local expected=#inventory[1].get_blueprint_entities()
local ghosts=inventory[1].build_blueprint{surface=surface,force=force,position={0,0},force_build=true,build_mode=defines.build_mode.forced}
assert(#ghosts==expected)
for _,g in pairs(ghosts) do assert(g.revive{raise_revive=false}) end
local packs={'automation-science-pack','logistic-science-pack','chemical-science-pack'}
local chests=surface.find_entities_filtered{name='wooden-chest'}
assert(#chests==36)
for _,chest in pairs(chests) do
  for _,name in ipairs(packs) do assert(chest.insert{name=name,count=28}==28) end
end
local power=surface.create_entity{name='electric-energy-interface',position={-3.5,4.5},force=force}
power.power_production=1000000000;power.electric_buffer_size=100000000000;power.energy=100000000000
local inlet=surface.create_entity{name='medium-electric-pole',position={-.5,4.5},force=force}
local grid=assert(surface.find_entity('medium-electric-pole',{6.5,4.5}))
inlet.get_wire_connector(defines.wire_connector_id.pole_copper,true).connect_to(grid.get_wire_connector(defines.wire_connector_id.pole_copper,true))
assert(force.add_research('rocket-silo'))
local started=game.tick
script.on_event(defines.events.on_tick,function()
  local elapsed=game.tick-started
  if technology.researched or elapsed>40*3600 then
    helpers.write_file('bootstrap-result.json',helpers.table_to_json{
      passed=technology.researched,engine_version=script.active_mods.base,official_expansion=script.active_mods['space-age'],
      labs=36,blueprint_entity_count=expected,research='rocket-silo',research_units=technology.research_unit_count,
      elapsed_minutes=elapsed/3600,research_speed_modifier=force.laboratory_speed_modifier,
      packs_supplied_each=1008,scope='Pre-researched prerequisites; finite packs supplied in chest-fed annex. Excludes pack production, manual loading and survival time.'})
    script.on_event(defines.events.on_tick,nil);game.tick_paused=true
  elseif elapsed%3600==0 then
    helpers.write_file('bootstrap-progress.json',helpers.table_to_json{elapsed_ticks=elapsed,research_progress=force.research_progress})
  end
end)
game.speed=100;game.tick_paused=false
