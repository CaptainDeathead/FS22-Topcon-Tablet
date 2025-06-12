TopconX35 = {}

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

    print(string.format(
        "TopconX35 {'vx': %.2f, 'vy': %.2f, 'vz': %.2f, 'vry': %.2f, 'tx': %.2f, 'ty': %.2f, 'tz': %.2f, 'try': %.2f, 'on': %s, 'lowered': %s}",
        vx, vy, vz, vry, tx, ty, tz, try, on, lowered))
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
