-- Finite-batch integration test. A courier models the documented manual chest
-- transfers; only external checklist materials are supplied. No intermediate,
-- rocket, platform or crafted silo is injected into production.
local config, force = storage.test_config, game.forces.player
local researched = {}
local function unlock(name)
  local technology = assert(force.technologies[name], name)
  if researched[name] then return end
  for _, prerequisite in pairs(technology.prerequisites) do unlock(prerequisite.name) end
  for _, ingredient in pairs(technology.research_unit_ingredients) do
    assert(ingredient.name == 'automation-science-pack' or ingredient.name == 'logistic-science-pack'
      or ingredient.name == 'chemical-science-pack', 'Non-launch science prerequisite: '..name)
  end
  technology.researched = true
  researched[name] = true
end
unlock('rocket-silo')
unlock('automation-2')
unlock('fast-inserter')
unlock('electric-energy-distribution-1')
local surface = game.surfaces.nauvis
surface.request_to_generate_chunks({32,32},4)
surface.force_generate_chunk_requests()
for _, e in pairs(surface.find_entities_filtered{area={{-16,-16},{144,96}}}) do
  if e.type ~= 'character' then e.destroy() end
end
local tiles={}
for x=-16,144 do for y=-16,96 do tiles[#tiles+1]={name='grass-1',position={x,y}} end end
surface.set_tiles(tiles)
local function place(encoded, position, defer)
  local inventory=game.create_inventory(1)
  assert(inventory[1].import_stack(encoded)==0,'Import failed')
  local expected=#inventory[1].get_blueprint_entities()
  local ghosts=inventory[1].build_blueprint{surface=surface,force=force,position=position,
    force_build=true,build_mode=defines.build_mode.forced}
  assert(#ghosts==expected,'Blueprint placement omitted entities')
  local deferred={}
  for _,g in pairs(ghosts) do
    if defer and (g.ghost_name=='rocket-silo' or g.ghost_name=='cargo-landing-pad') then
      deferred[g.ghost_name]=g
    else assert(g.revive{raise_revive=false},'Failed revival') end
  end
  inventory.destroy()
  return deferred,expected
end
local _, workshop_count=place(storage.blueprint_string,{0,0},false)
local pad_ghosts,pad_count=place(config.pad,{96,0},true)
local grid=assert(surface.find_entity('medium-electric-pole',{2.5,4.5}))
local power=surface.create_entity{name='electric-energy-interface',position={-1.5,4.5},force=force}
power.power_production=1000000000;power.electric_buffer_size=100000000000;power.energy=100000000000
local pad_grid=assert(surface.find_entity('medium-electric-pole',{100.5,8.5}))
-- External power lines are site-specific. Supply each blueprint at its inlet.
local pad_power=surface.create_entity{name='electric-energy-interface',position={97.5,8.5},force=force}
pad_power.power_production=1000000000;pad_power.electric_buffer_size=100000000000;pad_power.energy=100000000000
assert(grid.electric_network_id and pad_grid.electric_network_id,'Missing grids')
local stock=game.create_inventory(200)
for name,count in pairs(config.external_items) do
  assert(stock.insert{name=name,count=count}==count,'Stock capacity')
end
local cells={}
for _, c in ipairs(config.cells) do
  assert(force.recipes[c.recipe].enabled,'Recipe not unlocked: '..c.recipe)
  local cell={plan=c, input=assert(surface.find_entity('steel-chest',c.input)),
    output=assert(surface.find_entity('steel-chest',c.output)),
    machine=assert(surface.find_entity(c.recipe=='solid-fuel-from-light-oil' and 'chemical-plant' or 'assembling-machine-2',c.machine)),
    remaining={},collected=0}
  for _, a in ipairs(c.ingredients) do
    if a.type=='item' then cell.remaining[a.name]=a.amount end
  end
  if c.fluid_port then
    cell.pipe=assert(surface.find_entity('pipe',{c.fluid_port.x,c.fluid_port.y}))

  end
  cells[#cells+1]=cell
end
local started=game.tick
local silo,platform,launch_ordered,launch_finished
local milestones={}
script.on_event(defines.events.on_rocket_launched,function() launch_finished=game.tick-started end)
local function finish(passed,err)
  local produced={}
  for _,c in ipairs(cells) do produced[c.plan.product]=(produced[c.plan.product] or 0)+c.collected end
  helpers.write_file('bootstrap-result.json',helpers.table_to_json{
    passed=passed,error=err,engine_version=script.active_mods.base,official_expansion=script.active_mods['space-age'],
    workshop_entity_count=workshop_count,pad_entity_count=pad_count,produced=produced,
    elapsed_minutes=(game.tick-started)/3600,launch_ordered=launch_ordered,launch_finished_ticks=launch_finished,
    platform_created=platform and platform.valid and platform.hub~=nil,
    external_items=config.external_items,fluid_consumption=config.fluid_consumption,
    milestones=milestones,researched=researched,
    scope='Pre-researched finite workshop, manual transfers modeled by courier; excludes start-to-rocket survival time.'})
  script.on_event(defines.events.on_tick,nil);game.tick_paused=true
end
script.on_event(defines.events.on_tick,function()
  local ok,err=pcall(function()
    local elapsed=game.tick-started
    for _,c in ipairs(cells) do
      local target_crafts=c.plan.target / prototypes.recipe[c.plan.recipe].products[1].amount
      if c.machine.products_finished>=target_crafts then c.machine.disabled_by_script=true end
    end
    if elapsed%30==0 then
      for _,c in ipairs(cells) do
        local inv=c.output.get_inventory(defines.inventory.chest)
        local n=inv.get_item_count(c.plan.product)
        if n>0 then
          assert(stock.insert{name=c.plan.product,count=n}==n)
          inv.remove{name=c.plan.product,count=n};c.collected=c.collected+n
        end
        for name,remaining in pairs(c.remaining) do
          local n=math.min(remaining,stock.get_item_count(name))
          if n>0 then
            local inserted=c.input.insert{name=name,count=n}
            stock.remove{name=name,count=inserted};c.remaining[name]=remaining-inserted
          end
        end
        if c.pipe and not c.fluid_checked then
          local id=c.pipe.get_fluid_segment_id(1)
          local connected=false
          for i=1,c.machine.fluids_count do
            for _,connection in pairs(c.machine.get_fluid_box_pipe_connections(i) or {}) do
              if connection.target and connection.target.get_fluid_segment_id(connection.target_fluidbox_index)==id then connected=true end
            end
          end
          assert(connected,'Disconnected workshop fluid: '..c.plan.recipe)
          c.fluid_checked=true
        end
        if c.pipe and c.collected<c.plan.target then
          c.pipe.set_fluid_segment_fluid(1,{name=c.plan.fluid_port.fluid,amount=10000})
        end
        if c.collected>=c.plan.target and not milestones[tostring(c.plan.id)] then
          milestones[tostring(c.plan.id)]=elapsed/3600
        end
      end
      if not silo and stock.get_item_count('rocket-silo')>0 and stock.get_item_count('cargo-landing-pad')>0 then
        for name,g in pairs(pad_ghosts) do
          assert(stock.remove{name=name,count=1}==1)
          assert(g.revive{raise_revive=false})
        end
        silo=assert(surface.find_entity('rocket-silo',{106.5,10.5}))
        milestones.pad_built=elapsed/3600
      end
      if silo then
        local chest=assert(surface.find_entity('steel-chest',{100.5,10.5}))
        for name,count in pairs(config.rocket_load) do
          local n=math.min(count,stock.get_item_count(name))
          if n>0 then assert(chest.insert{name=name,count=n}==n);stock.remove{name=name,count=n} end
        end
        if silo.rocket and silo.rocket.valid and stock.get_item_count('space-platform-starter-pack')>0 and not platform and silo.get_inventory(defines.inventory.rocket_silo_attached_cargo_unit) then
          local cargo=silo.get_inventory(defines.inventory.rocket_silo_attached_cargo_unit)
          assert(cargo.insert{name='space-platform-starter-pack',count=1}==1)
          stock.remove{name='space-platform-starter-pack',count=1}
          platform=assert(force.create_space_platform{name='Bootstrap acceptance',planet='nauvis',starter_pack='space-platform-starter-pack'})
        end
        if platform and not launch_ordered then
          -- In 2.1 initiate the launch, then bind the attached pod to the
          -- waiting platform. Passing that destination to launch_rocket
          -- before ordering the launch returns false for a new platform.
          local pod=silo.rocket and silo.rocket.attached_cargo_pod
          if pod then
            launch_ordered=silo.launch_rocket()
            if launch_ordered then
              pod.cargo_pod_destination={type=defines.cargo_destination.space_platform,space_platform=platform}
            end
          end
        end
      end
    end
    if elapsed%3600==0 then
      local diagnostic={}
      for _,c in ipairs(cells) do diagnostic[#diagnostic+1]={recipe=c.plan.recipe,collected=c.collected,status=c.machine.status,energy=c.machine.energy} end
      helpers.write_file('bootstrap-progress.json',helpers.table_to_json{elapsed_ticks=elapsed,cells=diagnostic})
    end
    if launch_finished and platform and platform.hub then finish(true)
    elseif elapsed>90*3600 then
      local missing={}
      for _,c in ipairs(cells) do missing[#missing+1]=c.plan.recipe..'='..c.collected..'/'..c.plan.target..' status '..c.machine.status end
      error('Launch timeout; '..table.concat(missing,', ')..'; silo '..tostring(silo and silo.rocket_parts))
    end
  end)
  if not ok then finish(false,err) end
end)
game.speed=100;game.tick_paused=false
