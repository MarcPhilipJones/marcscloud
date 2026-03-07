import { Link } from "react-router-dom";
import AuthButton from "./AuthButton";

export default function Header() {
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link to="/" className="site-title">
          {{SITE_NAME}}
        </Link>
        <nav className="site-nav">
          <Link to="/">Home</Link>
          <Link to="/cases">My Cases</Link>
        </nav>
        <AuthButton />
      </div>
    </header>
  );
}
