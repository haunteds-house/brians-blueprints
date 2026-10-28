-- Inspect the original layout using actual 2.1 pipe topology.
local force=game.forces.player;force.research_all_technologies()
local surface=game.create_surface('original-bootstrap-inspection',{width=512,height=512,water=0,autoplace_settings={entity={treat_missing_as_default=false}}})
surface.request_to_generate_chunks({32,32},4);surface.force_generate_chunk_requests()
local tiles={};for x=-16,160 do for y=-16,160 do tiles[#tiles+1]={name='grass-1',position={x,y}} end end;surface.set_tiles(tiles)
local inv=game.create_inventory(1);assert(inv[1].import_stack(storage.blueprint_string)==0)
local expected=#inv[1].get_blueprint_entities()
local ghosts=inv[1].build_blueprint{surface=surface,force=force,position={0,0},force_build=true,build_mode=defines.build_mode.forced}
for _,g in pairs(ghosts) do assert(g.revive{raise_revive=false}) end
local green=storage.test_config.original_phase==3
if green then
 local power=surface.create_entity{name='electric-energy-interface',position={-6.5,44.5},force=force}
 power.power_production=1000000000;power.electric_buffer_size=100000000000;power.energy=100000000000
 local inlet=surface.create_entity{name='medium-electric-pole',position={-3.5,44.5},force=force}
 local grid=assert(surface.find_entity('small-electric-pole',{2.5,44.5}))
 inlet.get_wire_connector(defines.wire_connector_id.pole_copper,true).connect_to(grid.get_wire_connector(defines.wire_connector_id.pole_copper,true))
 assert(surface.find_entity('wooden-chest',{37.5,20.5}).insert{name='inserter',count=50}==50)
else
 local power=assert(surface.create_entity{name='electric-energy-interface',position={82.5,76.5},force=force})
 power.power_production=1000000000;power.electric_buffer_size=100000000000;power.energy=100000000000
 local inlet=assert(surface.create_entity{name='medium-electric-pole',position={79.5,76.5},force=force})
 local grid=assert(surface.find_entity('medium-electric-pole',{72.5,76.5}))
 inlet.get_wire_connector(defines.wire_connector_id.pole_copper,true).connect_to(grid.get_wire_connector(defines.wire_connector_id.pole_copper,true))
end
local import_cases={}
for _,p in ipairs(storage.test_config.imports or {}) do
 import_cases[#import_cases+1]={plan=p,input=assert(surface.find_entity('fast-transport-belt',p.input)),science=assert(surface.find_entity('fast-transport-belt',p.science_target)),overflow=assert(surface.find_entity('fast-transport-belt',p.mall_overflow)),science_count=0,overflow_count=0,backpressure_count=0}
end
local function drain(belt,item)
 local n=0
 for lane=1,2 do n=n+belt.get_transport_line(lane).remove_item{name=item,count=100} end
 return n
end
local heavy=surface.find_entity('chemical-plant',{32.5,80.5})
local light=surface.find_entity('chemical-plant',{48.5,80.5})
local stock_chest
if storage.test_config.original_phase==5 then
 local maker=assert(surface.find_entity('assembling-machine-2',{34.5,45.5}))
 assert(maker.get_inventory(defines.inventory.crafter_output).insert{name='locomotive',count=5}==5)
 stock_chest=assert(surface.find_entity('wooden-chest',{34.5,48.5}))
end
local low_baseline
local function pipe(x,y) return assert(surface.find_entity('pipe',{x,y})) end
local started=game.tick
script.on_event(defines.events.on_tick,function()
 if game.tick-started<(green and 7200 or 120) then return end
 if green then
  local delivered=0
  for _,e in pairs(surface.find_entities_filtered{type='assembling-machine'}) do
   if e.get_recipe() and e.get_recipe().name=='logistic-science-pack' then delivered=delivered+e.get_inventory(defines.inventory.crafter_input).get_item_count('inserter') end
  end
  local diagnostic={}
  for _,p in ipairs({{37.5,21.5},{14.5,44.5},{13.5,43.5}}) do
   local e=surface.find_entity('inserter',p);diagnostic[#diagnostic+1]={position=p,status=e and e.status,energy=e and e.energy}
  end
  helpers.write_file('bootstrap-result.json',helpers.table_to_json{diagnostic=diagnostic,source_count=surface.find_entity('wooden-chest',{37.5,20.5}).get_item_count('inserter'),destination_count=surface.find_entity('wooden-chest',{13.5,44.5}).get_item_count('inserter'),passed=delivered>0,engine_version=script.active_mods.base,inserters_delivered_to_science=delivered,scope='Transport test: inserters supplied only in original mall output chest. No manual delivery to science.',entity_count=expected})
  script.on_event(defines.events.on_tick,nil);game.tick_paused=true;return
 end
 if #import_cases>0 then
  local elapsed=game.tick-started
  for _,c in ipairs(import_cases) do
   for lane=1,2 do c.input.get_transport_line(lane).insert_at_back{name=c.plan.item,count=1} end
   local overflow=drain(c.overflow,c.plan.item)
   if elapsed<10800 then
    local science=drain(c.science,c.plan.item)
    if elapsed>=7200 then c.science_count=c.science_count+science;c.overflow_count=c.overflow_count+overflow end
   elseif elapsed>=14400 then c.backpressure_count=c.backpressure_count+overflow end
  end
  if elapsed<18000 then return end
  local results={};local passed=true
  for _,c in ipairs(import_cases) do
   local ok=c.science_count>=1200 and c.overflow_count<60 and c.backpressure_count>=1200
   passed=passed and ok
   results[#results+1]={item=c.plan.item,science_items_per_minute=c.science_count,overflow_during_science_demand=c.overflow_count,overflow_with_science_backed_up=c.backpressure_count,passed=ok}
  end
  helpers.write_file('bootstrap-result.json',helpers.table_to_json{passed=passed,engine_version=script.active_mods.base,cases=results,scope='Main plate-import priority and backpressure test; terminal belts drained, not a full science-throughput benchmark.'})
  script.on_event(defines.events.on_tick,nil);game.tick_paused=true;return
 end
 if heavy and light and not storage.test_config.inspect_only then
  local elapsed=game.tick-started
  if elapsed==120 then
   local function same(a,b) assert(pipe(a[1],a[2]).get_fluid_segment_id(1)==pipe(b[1],b[2]).get_fluid_segment_id(1),'Disconnected cracking fluid') end
   same({59.5,7.5},{67.5,7.5});same({28.5,58.5},{61.5,6.5});same({28.5,58.5},{61.5,4.5});same({25.5,67.5},{31.5,78.5});same({25.5,67.5},{47.5,78.5})
   same({34.5,57.5},{33.5,78.5});same({31.5,57.5},{31.5,82.5})
   same({31.5,57.5},{49.5,78.5});same({28.5,58.5},{47.5,82.5})
   local plastic=assert(surface.find_entity('chemical-plant',{52.5,5.5}))
   surface.find_entity('oil-refinery',{31.5,54.5}).disabled_by_script=true
   pipe(59.5,7.5).set_fluid_segment_fluid(1,{name='crude-oil',amount=1000})
   pipe(25.5,67.5).set_fluid_segment_fluid(1,{name='water',amount=20000})

  end
  if elapsed==1800 then
   assert(surface.find_entity('chemical-plant',{22.5,51.5}).products_finished>0,'Basic refining did not supply sulfur before cracking/advanced oil')
   surface.find_entity('chemical-plant',{52.5,5.5}).get_inventory(defines.inventory.crafter_input).insert{name='coal',count=50}
   pipe(34.5,57.5).set_fluid_segment_fluid(1,{name='heavy-oil',amount=5000})
   pipe(31.5,57.5).set_fluid_segment_fluid(1,{name='light-oil',amount=5000})
  end
  if elapsed<5400 then return end
  if elapsed==5400 then
   assert(heavy.products_finished>0 and light.products_finished>0,'Cracking did not start above reserve')
   pipe(34.5,57.5).set_fluid_segment_fluid(1,{name='heavy-oil',amount=300})
   pipe(31.5,57.5).set_fluid_segment_fluid(1,{name='light-oil',amount=300})
  end
  if elapsed==6000 then low_baseline={heavy.products_finished,light.products_finished} end
  if elapsed<7800 then return end
  helpers.write_file('bootstrap-result.json',helpers.table_to_json{passed=surface.find_entity('chemical-plant',{52.5,5.5}).products_finished>0 and surface.find_entity('chemical-plant',{52.5,5.5}).get_inventory(defines.inventory.crafter_output).get_item_count('plastic-bar')==0 and low_baseline[1]==heavy.products_finished and low_baseline[2]==light.products_finished and (not stock_chest or stock_chest.get_item_count('locomotive')==2),plastic_crafts=surface.find_entity('chemical-plant',{52.5,5.5}).products_finished,plastic_output_buffer=surface.find_entity('chemical-plant',{52.5,5.5}).get_inventory(defines.inventory.crafter_output).get_item_count('plastic-bar'),locomotive_stock=stock_chest and stock_chest.get_item_count('locomotive'),engine_version=script.active_mods.base,basic_refining_supplied_sulfur=true,heavy_cracking_crafts=heavy.products_finished,low_baseline=low_baseline,heavy_enable=heavy.get_control_behavior().circuit_enable_disable,heavy_disabled=heavy.get_control_behavior().disabled,heavy_condition=heavy.get_control_behavior().circuit_condition,heavy_contents=heavy.get_control_behavior().circuit_read_contents,heavy_tank=surface.find_entity('storage-tank',{36.5,53.5}).get_fluid_count('heavy-oil'),light_tank=surface.find_entity('storage-tank',{38.5,56.5}).get_fluid_count('light-oil'),light_cracking_crafts=light.products_finished,low_reserve_stops_verified=low_baseline[1]==heavy.products_finished and low_baseline[2]==light.products_finished,scope='Original refinery networks: connected cracking, high-reserve production and low-reserve circuit stop.'})
  script.on_event(defines.events.on_tick,nil);game.tick_paused=true;return
 end
 local nodes={}
 for _,e in pairs(surface.find_entities_filtered{force=force}) do
  if e.fluids_count>0 then
   local storages={}
   for i=1,e.fluids_count do
    local connections={}
    for _,c in pairs(e.get_fluid_box_pipe_connections(i) or {}) do
     connections[#connections+1]={position=c.position,target_position=c.target_position,target=c.target and {name=c.target.name,position=c.target.position},target_index=c.target_fluidbox_index}
    end
    local filter=e.has_fluid_segment(i) and e.get_fluid_segment_filter(i)
    storages[#storages+1]={index=i,segment=e.has_fluid_segment(i) and e.get_fluid_segment_id(i),filter=filter and filter.name,connections=connections}
   end
   nodes[#nodes+1]={name=e.name,recipe=(e.type=='assembling-machine' or e.type=='furnace') and e.get_recipe() and e.get_recipe().name,position=e.position,storages=storages}
  end
 end
 helpers.write_file('bootstrap-result.json',helpers.table_to_json{passed=#ghosts==expected,engine_version=script.active_mods.base,nodes=nodes,entity_count=expected})
 script.on_event(defines.events.on_tick,nil);game.tick_paused=true
end)
game.speed=100
