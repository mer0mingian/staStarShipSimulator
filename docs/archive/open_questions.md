# Open Questions - VTT Scope Transition

## Campaign & Session Management

1.  **Momentum Reset**: You mentioned "automated reduction of Momentum when transitioning between scenes". Should Momentum reset to 0 at the start of every Session (new game day), or does it persist indefinitely across Scenes until a Session break? --> for any transition between scenes the momentum pool will be reduced by 1 (minimum 0)

2.  **Scene Transitions**: When a GM ends a Scene, should the App automatically prompt for the "Connected Scene" (as per your diagram), or is that manual? --> If another scene has been connected by the GM before, prompt the GM, if they directly want to move the players there. Always offer, to create a new scene on the fly or to move back to the campaign overview.

3.  **Player Access**: Can Players see all Scenes in a Campaign, or only "Active" ones? --> players can only see the active scenes. Not all players need to be present in all scenes, they can be split into two scenes.

4.  **Turn Order**: Do you want auto-sorting (by Daring + Focus) or manual GM ordering for initiative? --> check how this is currently done. Turn order is only relevant for combat scenes, not narrative ones. the players can claim a turn (if multiple do, the captain (or, if not exists as player, the highest ranking officer) needs to decide) who gets the turn. Investigate in the rules, how many turns the GM gets for the NPCs.

## Scene Data & Persistence

5.  **Scene Data Persistence**: Should a Scene save its state (HP, Stress, etc.) permanently, or is it ephemeral (reset on re-entry)? --> The scene should save it's state (i.e. traits, extended tasks, present chars & ships)

6.  **Ship Shields**: Confirm simplified shields (single value) vs quadrant-based (Forward, Aft, Port, Starboard). --> Ships have one tracker for shields, representing the energy used to counter attacks. Prepare an optional setup for quadrant-based shields that can be enabled as a house-rule.

## UI/UX & Navigation

7.  **Navigation Priority**: Should the UI overhaul (Milestone 6) focus on:
    -   Campaign selection/dashboard?
    -   Scene management (creation/transition)?
    -   Character/Ship creation flows?
    -   All of the above?
--> create sub-milestones 6.1 - 6.3. Consider, how these can be worked on by sub-agents in parallel.

8.  **View Screen**: Should this be a separate route (`/view`) or a mode toggle in the Scene view? --> A separate route. This is not to be used by players, but by people watching.

## Data & Migration

9.  **Existing Data**: Is there any existing data (Encounters, Characters) that needs to be migrated to the new Campaign/Scene structure? --> no, you can flush everything.

10. **Universe Library Structure**: Should the Universe Library support Tags/Categories for organizing Chars/Ships (e.g., "Enemies", "Allies", "Starships")? --> Make categories: PCs, NPCs, Creatures, Player Ships, Non-Player ships.
