/**
 * AppShell — Top-level layout wrapper matching Dynamics 365 form chrome.
 *
 * Provides the header bar, navigation tabs, and content area.
 * Uses Fluent UI v9 components exclusively.
 */

import type { ReactNode } from "react";
import { makeStyles, tokens, shorthands } from "@fluentui/react-components";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    width: "100vw",
    backgroundColor: tokens.colorNeutralBackground2,
    overflow: "hidden",
  },
  content: {
    flex: 1,
    overflow: "auto",
    ...shorthands.padding("0"),
  },
});

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const styles = useStyles();

  return (
    <div className={styles.root}>
      <div className={styles.content}>{children}</div>
    </div>
  );
}
