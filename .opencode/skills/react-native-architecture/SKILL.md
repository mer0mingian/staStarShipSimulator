---
name: react-native-architecture
description: "Build production React Native apps with Expo, navigation, native modules, offline sync, and cross-platform patterns. Use when developing mobile apps, implementing native integrations, or architecting React Native projects. Cluster: Frontend/UI (SPLIT)"
---

# Production React Native Architecture

Architecting scalable, performant, and maintainable React Native applications, focusing on Expo, cross-platform consistency, and native integration.

## When to Use This Skill

- Starting a new, large-scale React Native project
- Deciding between Expo managed workflow and Bare workflow
- Implementing cross-platform state management (Zustand/Redux)
- Setting up navigation structures (React Navigation)
- Integrating native device features (camera, sensors)
- Implementing offline synchronization strategies

## Core Stack Components

| Component | Tool/Library | Purpose |
|-----------|--------------|---------|
| **Workflow** | Expo (Managed or Bare) | Simplified setup and tooling |
| **State Mgmt** | Zustand / Jotai / Redux Toolkit | Global state |
| **Navigation** | React Navigation v6+ | Screen routing, stack, tabs |
| **Styling** | StyleSheet / Styled-Components / NativeWind | Cross-platform styling |
| **Data Fetching** | React Query / SWR | Server state management |
| **Offline Sync** | Realm / WatermelonDB / Redux Persist | Local data storage |

## Key Patterns

### Pattern 1: Navigation Structure (React Navigation) (Cluster: Frontend/UI)

Use nested navigators for complex flows:

```typescript
// Root Navigator (Stack)
//   - AuthStack (Stack)
//     - LoginScreen
//     - RegisterScreen
//   - AppTabs (Tab Navigator)
//     - HomeScreen
//     - SettingsScreen
//   - HomeStack (Stack nested within a Tab)
```

### Pattern 2: State Management with Zustand (Cluster: Frontend/UI)

Use Zustand for simple, fast global state management across components.

```typescript
import { create } from 'zustand';

interface UserState {
  userId: string | null;
  isLoading: boolean;
  setUserId: (id: string | null) => void;
  fetchUser: (id: string) => Promise<void>;
}

const useUserStore = create<UserState>((set, get) => ({
  userId: null,
  isLoading: false,
  setUserId: (id) => set({ userId: id }),
  fetchUser: async (id) => {
    set({ isLoading: true });
    try {
      const response = await api.getUser(id);
      set({ userId: response.id });
    } catch (error) {
      console.error("Failed to fetch user", error);
    } finally {
      set({ isLoading: false });
    }
  }
}));
```

### Pattern 3: Native Module Integration (Bare Workflow)
If Expo managed is too restrictive, use Expo Dev Client or eject to Bare workflow to integrate custom native modules (Swift/Kotlin).

## Best Practices

-   **Expo First:** Stay in the managed workflow as long as possible for simplicity.
-   **Performance:** Use `useMemo`, `useCallback`, and `FlatList` (`VirtualizedList`) appropriately.
-   **Platform Checks:** Use `Platform.OS === 'ios'` or `.ios.tsx`/`.android.tsx` extensions judiciously.
-   **Debugging:** Use Flipper for network/database inspection.

## References

-   [React Native Official Docs](references/rn-docs.html)
-   [Expo Documentation](references/expo-docs.html)
-   [React Navigation Docs](references/react-navigation.html)
-   [Zustand Documentation](references/zustand-docs.html)

---

**Remember:** React Native requires managing platform-specific constraints while maximizing code sharing. (Cluster: Frontend/UI)
