interface PortalUser {
  userName: string;
  firstName: string;
  lastName: string;
  contactId: string;
}

function getPortalUser(): PortalUser | null {
  const portal = (window as unknown as Record<string, unknown>)["Microsoft"] as
    | { Dynamic365?: { Portal?: { User?: Record<string, string> } } }
    | undefined;
  const user = portal?.Dynamic365?.Portal?.User;
  if (!user?.userName) return null;
  return {
    userName: user.userName,
    firstName: user.firstName ?? "",
    lastName: user.lastName ?? "",
    contactId: user.contactId ?? "",
  };
}

export default function AuthButton() {
  const user = getPortalUser();
  const isAuthenticated = !!user;

  if (isAuthenticated) {
    return (
      <div className="auth-area">
        <span className="user-name">
          {user.firstName} {user.lastName}
        </span>
        <a
          href="/Account/Login/LogOff?returnUrl=%2F"
          className="btn btn-secondary btn-sm"
        >
          Sign Out
        </a>
      </div>
    );
  }

  return (
    <div className="auth-area">
      <a href="/SignIn?returnUrl=%2F" className="btn btn-primary btn-sm">
        Sign In
      </a>
    </div>
  );
}
