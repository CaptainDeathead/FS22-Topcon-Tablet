TopconX35 = {}

function Vehicle:getSpecTable(name)
    local spec = self["spec_" .. 'topconx35' .. "." .. name]
    if spec ~= nil then
        return spec
    end

    return self["spec_" .. name]
end

function getActiveSprayType(object)
    local activeSprayType

    if object.getIsSprayTypeActive ~= nil then
        local sprayerSpec = object:getSpecTable("sprayer")
        for id, sprayType in pairs(sprayerSpec.sprayTypes) do
            if object:getIsSprayTypeActive(sprayType) then
                activeSprayType = id
                break
            end
        end
    end

    return activeSprayType
end

function getMaxWorkAreaWidth(object)
    local workAreaSpec = object:getSpecTable("workArea")

    local calculateWorkAreas = true
    if workAreaSpec == nil or #workAreaSpec.workAreas == 0 then
        calculateWorkAreas = false
    end

    local maxWidth, minWidth = 0, 0

    local function createGuideNode(name, linkNode)
        local node = createTransformGroup(name)
        link(linkNode, node)
        setTranslation(node, 0, 0, 0)
        return node
    end

    local node = createGuideNode("width_node", object.rootNode)

    if calculateWorkAreas then
        local activeSprayType = getActiveSprayType(object)
        -- Exclude ridged markers from workArea calculation
        local skipWorkAreas = {
            ["processRidgeMarkerArea"] = true,
            ["processCombineSwathArea"] = true,
            ["processCombineChopperArea"] = true,
        }

        local function isWorkAreaValid(workArea)
            if skipWorkAreas[workArea.functionName] ~= nil then
                return false
            end

            if (activeSprayType ~= nil and workArea.sprayType ~= activeSprayType) then
                return false
            end

            return workArea.type ~= WorkAreaType.AUXILIARY
        end

        local function toLocalArea(workArea)
            if not isWorkAreaValid(workArea) then
                return nil -- will GC table value cause ipairs
            end

            local x0 = localToLocal(workArea.start, node, 0, 0, 0)
            local x1 = localToLocal(workArea.width, node, 0, 0, 0)
            local x2 = localToLocal(workArea.height, node, 0, 0, 0)

            return { x0, x1, x2 }
        end

        local areaWidths = {}
        for _, workArea in ipairs(workAreaSpec.workAreas) do
            table.insert(areaWidths, toLocalArea(workArea))
        end

        if #areaWidths > 0 then
            maxWidth = 0
            minWidth = math.huge

            for _, e in ipairs(areaWidths) do
                maxWidth = math.max(maxWidth, unpack(e))
                minWidth = math.min(minWidth, unpack(e))
            end
        end
    end

    local width = maxWidth + math.abs(minWidth)
    local leftMarker, rightMarker = object:getAIMarkers()
    if leftMarker ~= nil and rightMarker ~= nil then
        local lx = localToLocal(leftMarker, node, 0, 0, 0)
        local rx = localToLocal(rightMarker, node, 0, 0, 0)
        width = math.max(math.abs(lx - rx), width)
    end

    local offset = (minWidth + maxWidth) * 0.5
    if math.abs(offset) < 0.1 then
        offset = 0
    end

    delete(node)

    return MathUtil.round(width, 3), MathUtil.round(offset, 3)
end

function getActualWorkWidth(object)
    local width, offset = getMaxWorkAreaWidth(object)

    for _, implement in pairs(object:getAttachedImplements()) do
        if implement.object ~= nil then
            local implementWidth, implementOffset = getActualWorkWidth(implement.object)

            width = math.max(width, implementWidth)
            if implementOffset < 0 then
                offset = math.min(offset, implementOffset)
            else
                offset = math.max(offset, implementOffset)
            end
        end
    end

    return width, offset
end


local function getRotation(item)
    local dirX, _, dirZ = localDirectionToWorld(item.rootNode, 0, 0, 1)
    local heading = math.deg(math.atan2(dirX, dirZ))
    heading = (360 - heading + 180) % 360

    return heading
end

local function printTransform(vehicle, tool)
    local vx, vy, vz = getWorldTranslation(vehicle.rootNode)
    local tx, ty, tz = getWorldTranslation(tool.rootNode)

    local on = false
    if tool.getIsTurnedOn ~= nil then
        on = tool:getIsTurnedOn()
    end

    local lowered = true
    if tool.getIsLowered ~= nil then
        lowered = tool:getIsLowered()
    end


    local vry = getRotation(vehicle)
    local try = getRotation(tool)

    local width, offset = getActualWorkWidth(vehicle)

    print(string.format(
        "TopconX35 {'vx': %.2f, 'vy': %.2f, 'vz': %.2f, 'vry': %.2f, 'tx': %.2f, 'ty': %.2f, 'tz': %.2f, 'try': %.2f, 'on': %s, 'lowered': %s, 'work_width': %s}",
        vx, vy, vz, vry, tx, ty, tz, try, on, lowered, width))
end

function TopconX35:loadMap(name)
    print("TopconX35 mod loaded.")
end

function TopconX35:update(dt)
    local vehicle = g_currentMission.controlledVehicle
    if vehicle ~= nil then
        -- Check for attached implement/tool
        if vehicle.getAttachedImplements ~= nil then
            for _, implement in pairs(vehicle:getAttachedImplements()) do
                if implement.object ~= nil then
                    printTransform(vehicle, implement.object)
                    
                end
            end
        else
            if vehicle.getIsLowered ~= nil and vehicle.getIsTurnedOn ~= nil then
                printTransform(vehilce, vehicle)
            end
        end
    end
end

function TopconX35:deleteMap()
end

addModEventListener(TopconX35)
