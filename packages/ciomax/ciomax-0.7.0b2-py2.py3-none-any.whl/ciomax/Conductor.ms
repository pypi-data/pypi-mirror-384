-- Conductor render menu extension script
macroScript RenderWithConductor
category: "Menu Rendering"
tooltip: "Render with Conductor"
(
  on execute do
  (
    local maxScriptPath = getThisScriptFilename()
    local pythonScriptPath = substituteString maxScriptPath ".ms" ".py"
    python.ExecuteFile pythonScriptPath
  )
) 
-- The block above says, run Conductor.py on menu item press.

function addConductorLegacy = (
  if menuMan.registerMenuContext 0x196eb40b then
  (
    local renderMenuItem
    local mainMenuBar = menuMan.getMainMenuBar()
    for i = 1 to mainMenuBar.numItems() do
    (
      local menuItem = mainMenuBar.getItem(i)
      if menuItem.getTitle() == "&Rendering" then
      (
        renderMenuItem = mainMenuBar.getItem(i)
        exit
      )
    )
    local renderMenu = renderMenuItem.getSubMenu()
    local newAction = menuMan.createActionItem "RenderWithConductor" "Menu Rendering"
    for i = 1 to renderMenu.numItems() do
    (
      local menuItem = renderMenu.getItem(i)
      if menuItem.getTitle() == "Render" then
      (
        renderMenu.addItem newAction (i + 1)
        exit
      )
    )
    menuMan.updateMenuBar()
  )
)

function addConductor = (
  function menuCallback = (

    -- Add existing actions from autobackup action table
    local menuMgr = callbacks.notificationParam()
    local mainMenuBar = menuMgr.mainMenuBar
    local subMenuId = "341703ab-b8d2-4af9-bb43-6a3d0b2cb51b"
    local renderSubMenu = menuMgr.GetMenuById subMenuId

    -- local beforeItemId = "0be2836e-ed5a-453e-a94d-12ea19357125"
    local beforeItemId =  "b57d8aab-0035-469f-b598-14e1bc953722"
    local macroScriptActionTableID = 647394
    local macroScriptActionId = "RenderWithConductor`Menu Rendering"
    renderSubMenu.CreateAction "0DF774CB-DBCF-4803-A899-3E2BB97C5A6D" macroScriptActionTableID macroScriptActionId beforeId:beforeItemId title:"Rendering With Conductor"

  )

  callbacks.removeScripts id:#RenderwithConductor
  callbacks.addScript #cuiRegisterMenus menuCallback id:#RenderwithConductor
)

-- Adds Conductor to the Main Menu>Render section.
local max_ver_major = (maxVersion() as array)[8]

if max_ver_major >= 2025 then(
  addConductor()
) else (
  addConductorLegacy()
)