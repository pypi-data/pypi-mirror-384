# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s cs_dynamicpages -t test_dynamic_page_row.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src cs_dynamicpages.testing.CS_DYNAMICPAGES_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot /src/cs_dynamicpages/tests/robot/test_dynamic_page_row.robot
#
# See the http://docs.plone.org for further details (search for robot
# framework).
#
# ============================================================================

*** Settings *****************************************************************

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***************************************************************

Scenario: As a site administrator I can add a DynamicPageRow
  Given a logged-in site administrator
    and an add DynamicPageFolder form
   When I type 'My DynamicPageRow' into the title field
    and I submit the form
   Then a DynamicPageRow with the title 'My DynamicPageRow' has been created

Scenario: As a site administrator I can view a DynamicPageRow
  Given a logged-in site administrator
    and a DynamicPageRow 'My DynamicPageRow'
   When I go to the DynamicPageRow view
   Then I can see the DynamicPageRow title 'My DynamicPageRow'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add DynamicPageFolder form
  Go To  ${PLONE_URL}/++add++DynamicPageFolder

a DynamicPageRow 'My DynamicPageRow'
  Create content  type=DynamicPageFolder  id=my-dynamic_page_row  title=My DynamicPageRow

# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.IBasic.title  ${title}

I submit the form
  Click Button  Save

I go to the DynamicPageRow view
  Go To  ${PLONE_URL}/my-dynamic_page_row
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a DynamicPageRow with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the DynamicPageRow title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
